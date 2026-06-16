"""
Markdown导出工具
将优化后的简历、面试问题、评分报告导出为格式化的Markdown文件
"""
from pathlib import Path
from datetime import datetime
from typing import List
import re
from models.schema import (
    OptimizedResume,
    ScoreReport,
    InterviewQuestion,
    OptimizationLogic,
)
from app_config import config


class MarkdownExporter:
    """
    Markdown格式导出器

    支持导出：
    1. 优化后的简历
    2. 评分报告
    3. 面试问题列表
    4. 修改日志（Optimization_Logic）
    """

    def __init__(self, output_dir: Path = None):
        """
        初始化导出器

        Args:
            output_dir: 输出目录，默认使用config.OUTPUTS_DIR
        """
        self.output_dir = output_dir or config.OUTPUTS_DIR
        config.ensure_dirs()

    def export_resume(
        self,
        resume: OptimizedResume,
        filename: str = None,
    ) -> Path:
        """
        导出优化后的简历为Markdown

        Args:
            resume: 优化后的简历
            filename: 文件名，默认使用时间戳

        Returns:
            导出文件的路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimized_resume_{timestamp}.md"

        filepath = self.output_dir / filename

        content = self._build_resume_markdown(resume)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def export_score_report(
        self,
        report: ScoreReport,
        filename: str = None,
    ) -> Path:
        """
        导出评分报告为Markdown

        Args:
            report: 评分报告
            filename: 文件名

        Returns:
            导出文件的路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"score_report_{timestamp}.md"

        filepath = self.output_dir / filename

        content = self._build_score_report_markdown(report)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def export_interview_questions(
        self,
        questions: List[InterviewQuestion],
        filename: str = None,
    ) -> Path:
        """
        导出面试问题列表为Markdown

        Args:
            questions: 面试问题列表
            filename: 文件名

        Returns:
            导出文件的路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_questions_{timestamp}.md"

        filepath = self.output_dir / filename

        content = self._build_questions_markdown(questions)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def export_full_report(
        self,
        resume: OptimizedResume,
        report: ScoreReport,
        questions: List[InterviewQuestion],
        company_name: str = None,
    ) -> Path:
        """
        导出完整报告（包含所有内容）

        Args:
            resume: 优化后的简历
            report: 评分报告
            questions: 面试问题列表
            company_name: 公司名称（用于文件名）

        Returns:
            导出文件的路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_str = f"_{self._safe_filename_part(company_name)}" if company_name else ""
        filename = f"full_report{company_str}_{timestamp}.md"

        filepath = self.output_dir / filename

        content = []
        content.append("# 简历优化完整报告\n")
        content.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        content.append("---\n")

        # 1. 优化后简历
        content.append("## 优化后的简历\n")
        content.append(self._build_resume_markdown(resume))

        # 2. 修改说明
        content.append("---\n")
        content.append("## 修改说明\n")
        content.append(self._build_optimization_log_markdown(resume.optimization_logics))

        # 3. 评分报告
        content.append("---\n")
        content.append("## 评分报告\n")
        content.append(self._build_score_report_markdown(report))

        # 4. 面试问题
        content.append("---\n")
        content.append("## 面试问题\n")
        content.append(self._build_questions_markdown(questions))

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return filepath

    def _build_resume_markdown(self, resume: OptimizedResume) -> str:
        """构建简历Markdown内容"""
        lines = []

        for section_name, content in resume.sections.items():
            lines.append(f"### {section_name}\n")
            lines.append(f"{content}\n")

        lines.append(f"\n**匹配度评分: {resume.match_score}**\n")

        return "\n".join(lines)

    def _safe_filename_part(self, value: str) -> str:
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value.strip())
        return safe[:40] or "company"

    def _build_score_report_markdown(self, report: ScoreReport) -> str:
        """构建评分报告Markdown内容"""
        lines = []

        lines.append(f"## 综合评分: {report.overall_score}\n")
        lines.append(f"**面试准备度: {report.interview_readiness}**\n")
        lines.append("\n### 各维度评分\n")

        for dimension, score in report.dimensions.items():
            bar = "█" * int(score / 5)
            lines.append(f"- {dimension}: {bar} {score}")

        lines.append("\n### 雷达图\n")
        lines.append("```\n")
        lines.append(report.radar_chart_ascii)
        lines.append("```\n")

        lines.append("\n### 改进建议\n")
        lines.append(f"{report.feedback}\n")

        return "\n".join(lines)

    def _build_questions_markdown(self, questions: List[InterviewQuestion]) -> str:
        """构建面试问题Markdown内容"""
        lines = []

        lines.append(f"共 {len(questions)} 道面试问题\n")

        for i, q in enumerate(questions, 1):
            lines.append(f"### {i}. [{q.type}] {q.question}\n")
            lines.append(f"**针对关键词:** {q.jd_keyword_targeted}\n")
            lines.append(f"\n**评估标准:** {q.evaluation_criteria}\n")
            lines.append(f"\n**参考答案:**\n")
            lines.append(f"> {q.sample_answer}\n")

        return "\n".join(lines)

    def _build_optimization_log_markdown(self, logics: List[OptimizationLogic]) -> str:
        """构建修改日志Markdown内容"""
        lines = []

        if not logics:
            lines.append("*暂无详细修改记录*\n")
            return "\n".join(lines)

        lines.append("| 原文 | 修改后 | 修改原因 | 匹配关键词 |\n")
        lines.append("|------|--------|----------|------------|\n")

        for logic in logics:
            lines.append(
                f"| {logic.original_text} | {logic.optimized_text} | "
                f"{logic.reason} | {logic.jd_keyword_matched} |"
            )

        lines.append("\n")
        return "\n".join(lines)
