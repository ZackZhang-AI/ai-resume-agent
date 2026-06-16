"""
AI简历助手 - 全链路求职战略家
主入口文件

核心流程：
User Input → Analyst → Optimizer → Verifier → Recruiter → Output
                                ↑                          ↓
                                ←←←←←← 循环迭代 ←←←←←←←←

功能：
1. JD深度解码
2. 简历STAR法则优化
3. 防幻觉校验
4. 模拟面试生成
5. 评分雷达图可视化
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app_config import config
from models.schema import ResumeContext
from agents.analyst import AnalystAgent
from agents.optimizer import OptimizerAgent
from agents.verifier import VerifierAgent
from agents.recruiter import RecruiterAgent
from services.template_store import template_store
from services.evaluator import Evaluator
from services.llm_client import get_quality_mode
from utils.markdown_exporter import MarkdownExporter


class ResumeAgentSystem:
    """
    简历Agent系统主控制器

    协调所有Agent完成从JD分析到面试准备的完整流程
    """

    def __init__(self):
        """初始化系统"""
        self.analyst = AnalystAgent()
        self.optimizer = OptimizerAgent()
        self.verifier = VerifierAgent()
        self.recruiter = RecruiterAgent()
        self.evaluator = Evaluator()
        self.exporter = MarkdownExporter()

    async def run(self, job_description: str, original_resume: str, company_name: str = None):
        """
        运行完整的简历优化流程

        Args:
            job_description: 岗位描述
            original_resume: 原始简历
            company_name: 公司名称（可选，用于文件命名）

        Returns:
            包含所有输出的上下文对象
        """
        print("\n" + "=" * 60)
        print("🚀 AI简历助手 - 全链路求职战略家")
        print("=" * 60)

        # 初始化上下文
        context = ResumeContext(
            original_resume=original_resume,
            job_description=job_description,
            quality_mode=get_quality_mode(self.optimizer.llm_client),
        )

        # === 步骤1: JD深度解码 ===
        print("\n[步骤1/5] 📊 JD深度解码中...")
        context.jd_analysis = await self.analyst.analyze(job_description)
        print(f"  ✓ 识别核心技能: {', '.join(context.jd_analysis.core_skills[:3])}...")
        print(f"  ✓ 识别软技能: {', '.join(context.jd_analysis.soft_skills[:2])}...")
        print(f"  ✓ 行业背景: {context.jd_analysis.industry_context}")

        # === 步骤2: 简历优化（可能循环）===
        print("\n[步骤2/5] ✍️ 简历优化中...")
        iteration = 0
        feedback = None

        while iteration < config.MAX_RETRIES:
            iteration += 1
            context.iteration_count = iteration
            print(f"  第 {iteration} 次优化迭代...")

            # 调用优化器
            context.optimized_resume = await self.optimizer.optimize(
                original_resume=original_resume,
                jd_analysis=context.jd_analysis,
                feedback=feedback,
            )

            # 检查是否需要继续迭代
            if not self.evaluator.should_iterate(
                context.optimized_resume.match_score,
                config.MAX_RETRIES,
                iteration,
            ):
                print(f"  ✓ 匹配度已达到 {context.optimized_resume.match_score}，无需继续迭代")
                break

            # 生成反馈用于下一次迭代
            suggestions = self.evaluator.generate_improvement_suggestions(
                context.optimized_resume,
                context.jd_analysis,
            )
            feedback = "；".join(suggestions)
            print(f"  建议改进: {feedback[:50]}...")

        print(f"  ✓ 最终匹配度: {context.optimized_resume.match_score}")

        # === 步骤3: 防幻觉校验 ===
        print("\n[步骤3/5] 🔍 防幻觉校验中...")
        warnings, all_confirmed = self.verifier.verify(
            original_resume=original_resume,
            optimized_resume=context.optimized_resume,
        )

        if warnings:
            print(f"  ⚠️ 检测到 {len(warnings)} 项新增量化指标")
            all_confirmed = self.verifier.interactive_confirm(warnings)

            if not all_confirmed:
                # 过滤未确认的内容
                context.optimized_resume = self.verifier.filter_unconfirmed(
                    context.optimized_resume, warnings
                )
                context.quantifications_pending = warnings
        else:
            print("  ✓ 未检测到新增量化指标")

        # === 步骤4: 模拟面试生成 ===
        print("\n[步骤4/5] 🎯 生成模拟面试问题...")
        context.interview_questions = await self.recruiter.generate_questions(
            optimized_resume=context.optimized_resume,
            jd_analysis=context.jd_analysis,
        )
        print(f"  ✓ 生成 {len(context.interview_questions)} 道面试问题")

        # === 步骤5: 评分报告 ===
        print("\n[步骤5/5] 📈 生成评分报告...")
        context.score_report = await self.recruiter.evaluate(
            optimized_resume=context.optimized_resume,
            jd_analysis=context.jd_analysis,
            risk_count=len(warnings),
            quality_mode=context.quality_mode,
        )
        print(f"  ✓ 综合评分: {context.score_report.overall_score}")
        print(f"  ✓ 面试准备度: {context.score_report.interview_readiness}")

        # === 导出结果 ===
        print("\n[导出] 💾 保存结果...")
        output_path = self.exporter.export_full_report(
            resume=context.optimized_resume,
            report=context.score_report,
            questions=context.interview_questions,
            company_name=company_name,
        )
        print(f"  ✓ 完整报告已保存至: {output_path}")

        # 打印最终结果概览
        self._print_summary(context)

        return context

    def _print_summary(self, context: ResumeContext):
        """打印结果概览"""
        print("\n" + "=" * 60)
        print("📋 简历优化完成 - 结果概览")
        print("=" * 60)

        print("\n【评分雷达图】")
        print(context.score_report.radar_chart_ascii)

        print("\n【改进建议】")
        print(context.score_report.feedback)

        print("\n【面试问题预览（前3道）】")
        for i, q in enumerate(context.interview_questions[:3], 1):
            print(f"  {i}. {q.question[:40]}...")

        print("\n" + "=" * 60)
        print("✅ 完整报告已导出至 outputs/ 目录")
        print("=" * 60)


def get_user_input() -> tuple:
    """获取用户输入"""
    print("\n" + "=" * 60)
    print("请输入以下信息（直接回车使用示例）")
    print("=" * 60)

    # JD输入
    print("\n📌 请粘贴目标岗位JD（Job Description）：")
    print("（输入完成后按Ctrl+D结束输入）")
    jd_input = sys.stdin.read().strip()

    if not jd_input.strip():
        # 使用示例JD
        jd_input = """
        我们正在寻找一位AI产品经理加入我们的团队。

        岗位要求：
        1. 本科及以上学历，计算机或相关专业优先
        2. 3年以上AI/LLM产品经验，有从0到1搭建AI产品经验优先
        3. 熟悉LLM技术栈（RAG、LangChain、Prompt Engineering等）
        4. 具备跨团队协作能力，能协调工程、算法、设计团队
        5. 数据驱动，具备良好的数据分析能力
        6. 有规模化系统设计经验优先

        我们提供：
        - 有竞争力的薪酬
        - 弹性工作制
        - 技术氛围浓厚
        """

    # 简历输入
    print("\n📄 请粘贴您的原始简历：")
    print("（输入完成后按Ctrl+D结束输入）")
    resume_input = sys.stdin.read().strip()

    if not resume_input.strip():
        # 使用示例简历
        resume_input = """
        张三
        电话: 138xxxx8888 | 邮箱: zhangsan@email.com

        教育背景
        北京大学 计算机科学与技术 硕士 2020-2023

        工作经历
        字节跳动 - AI产品经理 2023-至今
        - 负责AI产品设计工作
        - 参与了一些项目

        项目经历
        智能问答系统
        - 负责产品需求分析
        - 和团队一起完成了系统开发

        技能清单
        Python, SQL, 数据分析, 产品经理
        """

    # 公司名称（可选）
    print("\n🏢 公司名称（可选，直接回车跳过）：")
    company_name = sys.stdin.readline().strip()

    return jd_input, resume_input, company_name or None


async def main():
    """主函数"""
    # 检查配置
    config.ensure_dirs()

    # 获取用户输入
    job_description, original_resume, company_name = get_user_input()

    # 创建并运行系统
    system = ResumeAgentSystem()

    try:
        await system.run(
            job_description=job_description,
            original_resume=original_resume,
            company_name=company_name,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
