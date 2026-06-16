from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class JDAnalysis(BaseModel):
    """JD深度解码的输出结构"""

    core_skills: List[str] = Field(
        description="硬技能/技术栈关键词，如Python、LLM、A/B测试"
    )
    soft_skills: List[str] = Field(
        description="软技能关键词，如跨团队协作、数据驱动、owner意识"
    )
    hidden_requirements: List[str] = Field(
        description="JD中隐含的深层需求，如'从0到1构建能力'、'大规模系统稳定性'"
    )
    keyword_weights: Dict[str, float] = Field(
        description="关键词权重，用于后续匹配度计算，范围0-1"
    )
    industry_context: str = Field(
        description="行业背景分析，如'新能源+AI'或'大模型研发'"
    )
    pain_points: List[str] = Field(
        default_factory=list,
        description="岗位常见痛点/挑战，如'用户留存率低'、'QPS瓶颈'、'跨团队协调难'"
    )
    tool_chains: List[str] = Field(
        default_factory=list,
        description="JD中提到的工具/技术栈，如'LangChain'、'CRM系统'、'SQL'"
    )
    industry_verbs: List[str] = Field(
        default_factory=list,
        description="该岗位常用的行动动词，如'主导'、'推进'、'统筹'"
    )
    function_type: str = Field(
        default="PM",
        description="职能类型：PM/运营/市场/算法/研发等"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "core_skills": ["Python", "LLM", "数据分析"],
                "soft_skills": ["跨团队协作", "owner意识"],
                "hidden_requirements": ["从0到1构建能力", "大规模系统稳定性"],
                "keyword_weights": {"Python": 0.8, "LLM": 0.9},
                "industry_context": "大模型应用层",
                "pain_points": ["模型幻觉严重", "QPS瓶颈", "知识库召回率低"],
                "tool_chains": ["LangChain", "ChromaDB", "Pydantic"],
                "industry_verbs": ["主导", "重构", "构建", "搭建"],
                "function_type": "PM",
            }
        }


class OptimizationLogic(BaseModel):
    """每个修改点的可解释性记录"""

    original_text: str = Field(description="原始简历文本")
    optimized_text: str = Field(description="优化后的文本")
    reason: str = Field(
        description="解释为什么这样改，包含JD中的哪个关键词驱动了这次修改"
    )
    jd_keyword_matched: str = Field(
        description="匹配到JD中的哪个关键词"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "负责写代码",
                "optimized_text": "主导了基于Python的微服务重构",
                "reason": "目标JD对'架构设计能力'有40%权重需求",
                "jd_keyword_matched": "架构设计",
            }
        }


class QuantificationWarning(BaseModel):
    """Verifier高亮的量化指标警告"""

    risk_type: str = Field(default="quantification", description="风险类型")
    original_claim: str = Field(description="原始简历中的描述（无数据）")
    suggested_claim: str = Field(description="AI建议的量化描述")
    basis: str = Field(
        description="AI给出这个量化建议的行业基准或依据"
    )
    user_confirmed: bool = Field(
        default=False, description="用户是否确认此量化指标真实可达"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_claim": "提升了系统性能",
                "suggested_claim": "将API响应时间从200ms降至80ms（提升60%）",
                "basis": "行业同岗位平均优化幅度为40-70%",
                "user_confirmed": False,
            }
        }


class OptimizedResume(BaseModel):
    """优化后的简历结构"""

    sections: Dict[str, str] = Field(
        description="简历各部分内容，key为section名（如教育背景、工作经历、项目经历）"
    )
    optimization_logics: List[OptimizationLogic] = Field(
        description="所有修改点的可解释性记录"
    )
    quantifications_added: List[str] = Field(
        description="新增的量化指标列表，供Verifier高亮提示"
    )
    match_score: float = Field(
        description="与JD的匹配度得分，0-100"
    )
    missing_info_questions: List[str] = Field(
        default_factory=list,
        description="为了生成真实可投递简历，需要用户补充的信息问题"
    )
    risk_flags: List[str] = Field(
        default_factory=list,
        description="优化中可能涉及真实性确认的风险提示"
    )
    quality_notes: List[str] = Field(
        default_factory=list,
        description="成稿质量说明和后续优化建议"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sections": {
                    "工作经历": "主导了某AI产品的需求分析...",
                    "项目经历": "基于LangChain构建了.../",
                },
                "optimization_logics": [],
                "quantifications_added": ["提升60%性能", "管理5人团队"],
                "match_score": 75.0,
            }
        }


class ScoreReport(BaseModel):
    """评分报告"""

    overall_score: float = Field(description="综合评分，0-100")
    dimensions: Dict[str, float] = Field(
        description="各维度评分，包含：逻辑性、技术深度、业务贡献、排版美观"
    )
    radar_chart_ascii: str = Field(description="ASCII绘制的雷达图")
    feedback: str = Field(
        description="综合反馈，包含具体改进建议"
    )
    interview_readiness: str = Field(
        description="面试准备度评估，如'可以出击'、'需要强化技术深度'"
    )
    risk_count: int = Field(default=0, description="未确认风险项数量")
    quality_mode: str = Field(default="rule_based", description="生成质量模式：llm或rule_based")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 78.0,
                "dimensions": {
                    "逻辑性": 85.0,
                    "技术深度": 70.0,
                    "业务贡献": 80.0,
                    "排版美观": 75.0,
                },
                "radar_chart_ascii": "见ascii_chart模块",
                "feedback": "建议补充量化指标",
                "interview_readiness": "可以出击",
            }
        }


class InterviewQuestion(BaseModel):
    """面试问题"""

    question: str = Field(description="面试问题正文")
    type: str = Field(
        description="问题类型，如'行为面'、'技术面'、'压力面'"
    )
    evaluation_criteria: str = Field(
        description="评估标准，说明什么算好答案"
    )
    sample_answer: str = Field(
        description="参考答案，展示优秀答案的样子"
    )
    jd_keyword_targeted: str = Field(
        description="这个问题针对的是JD中的哪个关键词"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "请描述一个你从0到1搭建AI产品的经历",
                "type": "行为面",
                "evaluation_criteria": "STAR法则完整、有数据支撑、体现owner意识",
                "sample_answer": "我在X公司主导了...",
                "jd_keyword_targeted": "从0到1构建能力",
            }
        }


class ResumeContext(BaseModel):
    """贯穿整个Agent流程的上下文对象"""

    original_resume: str = Field(description="用户输入的原始简历文本")
    job_description: str = Field(description="目标岗位的JD文本")
    jd_analysis: Optional[JDAnalysis] = Field(
        default=None, description="Analyst的输出"
    )
    optimized_resume: Optional[OptimizedResume] = Field(
        default=None, description="Optimizer的输出"
    )
    quantifications_pending: List[QuantificationWarning] = Field(
        default_factory=list, description="待用户确认的量化指标"
    )
    score_report: Optional[ScoreReport] = Field(
        default=None, description="Recruiter的评分报告"
    )
    interview_questions: List[InterviewQuestion] = Field(
        default_factory=list, description="生成的面试问题列表"
    )
    iteration_count: int = Field(
        default=0, description="当前迭代次数，用于防止死循环"
    )
    quality_mode: str = Field(
        default="rule_based", description="当前流程使用的质量模式"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_resume": "在某公司实习...",
                "job_description": "某AI公司招聘AI产品经理...",
                "iteration_count": 1,
            }
        }
