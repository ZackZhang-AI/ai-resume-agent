"""
FastAPI 后端服务
提供简历优化的 REST API 接口
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
import base64

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app_config import config
from models.schema import (
    JDAnalysis,
    OptimizedResume,
    ScoreReport,
    InterviewQuestion,
    ResumeContext,
)
from agents.analyst import AnalystAgent
from agents.optimizer import OptimizerAgent
from agents.verifier import VerifierAgent
from agents.recruiter import RecruiterAgent
from services.evaluator import Evaluator
from utils.markdown_exporter import MarkdownExporter
from utils.word_exporter import WordExporter
from services.llm_client import get_quality_mode
import PyPDF2
import io


# === Pydantic 请求/响应模型 ===

class OptimizeRequest(BaseModel):
    job_description: str
    original_resume: str
    company_name: Optional[str] = None


class OptimizeResponse(BaseModel):
    success: bool
    message: str
    quality_mode: str = "rule_based"
    # JD分析结果
    jd_analysis: Optional[dict] = None
    # 优化后的简历
    optimized_resume: Optional[dict] = None
    # 量化指标警告（待确认）
    quantification_warnings: list = []
    confirmation_required: bool = False
    missing_info_questions: list = []
    risk_flags: list = []
    quality_notes: list = []
    # 评分报告
    score_report: Optional[dict] = None
    # 面试问题
    interview_questions: list = []
    # 修改记录
    modifications: list = []


# === FastAPI 应用 ===

app = FastAPI(
    title="简历优化助手 API",
    description="多Agent协作的智能简历优化系统",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
analyst = AnalystAgent()
optimizer = OptimizerAgent()
verifier = VerifierAgent()
recruiter = RecruiterAgent()
evaluator = Evaluator()
exporter = MarkdownExporter()
word_exporter = WordExporter()


# === 文档解析工具 ===

def parse_pdf(file_content: bytes) -> str:
    """从PDF中提取文本"""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF解析失败: {str(e)}")


def parse_docx(file_content: bytes) -> str:
    """从Word文档中提取文本"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_content))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Word文档解析失败: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return frontend_path.read_text(encoding="utf-8")
    return {"message": "Frontend not found"}


@app.get("/api")
async def api_info():
    """API 信息"""
    return {
        "service": "简历优化助手 API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/optimize": "简历优化主接口",
            "POST /api/upload": "上传JD或简历文件",
            "GET /api/download/word": "下载简历为Word文档"
        }
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    解析上传的文件（PDF或Word）
    返回提取的文本内容
    """
    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith('.pdf'):
        text = parse_pdf(content)
    elif filename.endswith('.docx') or filename.endswith('.doc'):
        text = parse_docx(content)
    elif filename.endswith('.txt'):
        text = content.decode('utf-8').strip()
    else:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式，请上传 PDF、Word(.docx) 或 TXT 文件"
        )

    return {
        "success": True,
        "filename": file.filename,
        "content": text,
        "char_count": len(text)
    }


@app.get("/api/download/word")
async def download_word(
    resume_text: str,
    report_overall: float = 75.0,
    report_readiness: str = "准备充分",
    dimensions: str = "",  # JSON encoded
    feedback: str = "",
    questions: str = "",   # JSON encoded
    modifications: str = "" # JSON encoded
):
    """
    生成并下载Word文档

    参数通过query传递（需URL编码）
    """
    from models.schema import OptimizedResume, ScoreReport, InterviewQuestion, OptimizationLogic
    import json

    # 解析resume_text为sections字典
    sections = {"完整简历": resume_text}

    # 解析dimensions JSON
    dimensions_dict = {}
    if dimensions:
        try:
            dimensions_dict = json.loads(dimensions)
        except:
            pass

    # 解析questions JSON
    questions_list = []
    if questions:
        try:
            questions_data = json.loads(questions)
            for q in questions_data:
                questions_list.append(InterviewQuestion(
                    question=q.get("text", ""),
                    type=q.get("type", "行为面"),
                    evaluation_criteria="",
                    sample_answer="",
                    jd_keyword_targeted=q.get("keyword", "")
                ))
        except:
            pass

    # 解析modifications JSON
    logics = []
    if modifications:
        try:
            mods = json.loads(modifications)
            for m in mods:
                logics.append(OptimizationLogic(
                    original_text=m.get("original", ""),
                    optimized_text=m.get("optimized", ""),
                    reason=m.get("reason", ""),
                    jd_keyword_matched=""
                ))
        except:
            pass

    # 构建对象
    resume = OptimizedResume(
        sections=sections,
        optimization_logics=logics,
        quantifications_added=[],
        match_score=report_overall
    )

    report = ScoreReport(
        overall_score=report_overall,
        dimensions=dimensions_dict,
        radar_chart_ascii="",
        feedback=feedback,
        interview_readiness=report_readiness
    )

    # 生成Word文档
    doc_bytes = word_exporter.export_full_report_to_bytes(resume, report, questions_list)

    return Response(
        content=doc_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": "attachment; filename=optimized_resume.docx"
        }
    )


@app.post("/api/optimize", response_model=OptimizeResponse)
async def optimize_resume(request: OptimizeRequest):
    """
    简历优化主接口

    接收 JD 和简历，返回完整的优化结果
    """
    try:
        # 输入验证
        if not request.job_description.strip():
            raise HTTPException(status_code=400, detail="岗位描述不能为空")
        if not request.original_resume.strip():
            raise HTTPException(status_code=400, detail="简历内容不能为空")

        # 初始化上下文
        context = ResumeContext(
            original_resume=request.original_resume,
            job_description=request.job_description,
            quality_mode=get_quality_mode(optimizer.llm_client),
        )

        # === 步骤1: JD深度解码 ===
        context.jd_analysis = await analyst.analyze(request.job_description)

        # === 步骤2: 简历优化 ===
        iteration = 0
        feedback = None

        while iteration < config.MAX_RETRIES:
            iteration += 1
            context.iteration_count = iteration

            context.optimized_resume = await optimizer.optimize(
                original_resume=request.original_resume,
                jd_analysis=context.jd_analysis,
                feedback=feedback,
            )

            if not evaluator.should_iterate(
                context.optimized_resume.match_score,
                config.MAX_RETRIES,
                iteration,
            ):
                break

            suggestions = evaluator.generate_improvement_suggestions(
                context.optimized_resume,
                context.jd_analysis,
            )
            feedback = "；".join(suggestions)

        # === 步骤3: 防幻觉校验 ===
        warnings, _ = verifier.verify(
            original_resume=request.original_resume,
            optimized_resume=context.optimized_resume,
        )

        quantification_warnings = []
        if warnings:
            quantification_warnings = [
                {
                    "risk_type": w.risk_type,
                    "original_claim": w.original_claim,
                    "suggested_claim": w.suggested_claim,
                    "basis": w.basis,
                    "user_confirmed": w.user_confirmed,
                }
                for w in warnings
            ]
            context.quantifications_pending = warnings

        # === 步骤4: 生成面试问题 ===
        context.interview_questions = await recruiter.generate_questions(
            optimized_resume=context.optimized_resume,
            jd_analysis=context.jd_analysis,
        )

        # === 步骤5: 评分报告 ===
        context.score_report = await recruiter.evaluate(
            optimized_resume=context.optimized_resume,
            jd_analysis=context.jd_analysis,
            risk_count=len(warnings),
            quality_mode=context.quality_mode,
        )

        # === 导出结果 ===
        exporter.export_full_report(
            resume=context.optimized_resume,
            report=context.score_report,
            questions=context.interview_questions,
            company_name=request.company_name,
        )

        # 构造修改记录
        modifications = []
        if context.optimized_resume.optimization_logics:
            for logic in context.optimized_resume.optimization_logics:
                modifications.append({
                    "original": logic.original_text,
                    "optimized": logic.optimized_text,
                    "reason": logic.reason,
                })

        # 构造响应
        return OptimizeResponse(
            success=True,
            message="优化完成",
            quality_mode=context.quality_mode,
            jd_analysis={
                "core_skills": context.jd_analysis.core_skills,
                "soft_skills": context.jd_analysis.soft_skills,
                "hidden_requirements": context.jd_analysis.hidden_requirements,
                "industry_context": context.jd_analysis.industry_context,
            },
            optimized_resume={
                "full_text": "\n".join(context.optimized_resume.sections.values()),
                "match_score": context.optimized_resume.match_score,
            },
            quantification_warnings=quantification_warnings,
            confirmation_required=bool(warnings),
            missing_info_questions=context.optimized_resume.missing_info_questions,
            risk_flags=context.optimized_resume.risk_flags,
            quality_notes=context.optimized_resume.quality_notes,
            score_report={
                "overall_score": context.score_report.overall_score,
                "dimensions": context.score_report.dimensions,
                "feedback": context.score_report.feedback,
                "interview_readiness": context.score_report.interview_readiness,
                "risk_count": context.score_report.risk_count,
                "quality_mode": context.score_report.quality_mode,
            },
            interview_questions=[
                {
                    "type": q.type,
                    "text": q.question,
                    "keyword": q.jd_keyword_targeted,
                }
                for q in context.interview_questions
            ],
            modifications=modifications,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    config.ensure_dirs()
    print("🚀 启动简历优化助手 API 服务...")
    print(f"📍 地址: http://localhost:8000")
    print(f"📚 API文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
