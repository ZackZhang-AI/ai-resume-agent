"""
评分引擎服务 (Evaluator)
负责计算简历与JD的匹配度，以及各维度的评分
"""
from typing import Dict, List
from models.schema import JDAnalysis, OptimizedResume, ScoreReport
from app_config import config


class Evaluator:
    """
    简历评分引擎
    """

    # ATS友好度检查规则
    ATS_RULES = {
        "has_contact": {"field": "联系方式", "weight": 10},
        "has_education": {"field": "教育背景", "weight": 15},
        "has_experience": {"field": "工作/实习经历", "weight": 25},
        "has_projects": {"field": "项目经历", "weight": 20},
        "has_skills": {"field": "技能列表", "weight": 15},
        "has_quantification": {"field": "量化数据", "weight": 15},
    }

    def __init__(self):
        """初始化评分引擎"""
        pass

    def calculate_match_score(
        self,
        optimized_resume: OptimizedResume,
        jd_analysis: JDAnalysis,
    ) -> float:
        """
        计算简历与JD的综合匹配度

        Args:
            optimized_resume: 优化后的简历
            jd_analysis: JD分析结果

        Returns:
            匹配度分数 (0-100)
        """
        resume_text = optimized_resume.sections.get("完整简历", "").lower()

        # 1. 关键词匹配得分 (权重: 60%)
        keyword_score = self._calculate_keyword_score(resume_text, jd_analysis)

        # 2. STAR法则得分 (权重: 20%)
        star_score = self._calculate_star_score(resume_text)

        # 3. 量化指标得分 (权重: 20%)
        quant_score = self._calculate_quantification_score(resume_text)

        # 综合得分
        total_score = (
            keyword_score * 0.6 +
            star_score * 0.2 +
            quant_score * 0.2
        )

        return round(total_score, 1)

    def _calculate_keyword_score(self, resume_text: str, jd_analysis: JDAnalysis) -> float:
        """计算关键词匹配得分"""
        if not jd_analysis.core_skills and not jd_analysis.soft_skills:
            return 50.0

        all_keywords = jd_analysis.core_skills + jd_analysis.soft_skills
        matched = sum(
            1 for kw in all_keywords
            if kw.lower() in resume_text
        )

        return (matched / len(all_keywords)) * 100

    def _calculate_star_score(self, resume_text: str) -> float:
        """计算STAR法则使用得分"""
        score = 50  # 基础分

        # 检查STAR元素
        star_indicators = {
            "action_verbs": ["主导", "负责", "推动", "协调", "设计", "构建"],
            "results": ["提升了", "增长了", "优化了", "实现了", "完成了"],
        }

        action_count = sum(
            1 for verb in star_indicators["action_verbs"]
            if verb in resume_text
        )
        result_count = sum(
            1 for result in star_indicators["results"]
            if result in resume_text
        )

        if action_count >= 3:
            score += 25
        if result_count >= 2:
            score += 25

        return min(score, 100)

    def _calculate_quantification_score(self, resume_text: str) -> float:
        """计算量化指标得分"""
        score = 0

        # 检测数字/百分比
        has_percentage = "%" in resume_text or "增长" in resume_text
        has_absolute = any(char.isdigit() for char in resume_text)

        if has_percentage:
            score += 50
        if has_absolute:
            score += 30
        if has_percentage and has_absolute:
            score += 20  # 额外加分

        return min(score, 100)

    def evaluate_ats_friendliness(self, resume_text: str) -> Dict:
        """
        评估ATS友好度

        Args:
            resume_text: 简历文本

        Returns:
            ATS评估结果
        """
        result = {
            "passed_rules": [],
            "failed_rules": [],
            "total_score": 0,
        }

        # 检查各项规则
        if "电话" in resume_text or "手机" in resume_text or "@" in resume_text:
            result["passed_rules"].append("has_contact")
        else:
            result["failed_rules"].append("has_contact")

        if "本科" in resume_text or "硕士" in resume_text or "博士" in resume_text:
            result["passed_rules"].append("has_education")
        else:
            result["failed_rules"].append("has_education")

        if "工作" in resume_text or "实习" in resume_text or "经历" in resume_text:
            result["passed_rules"].append("has_experience")
        else:
            result["failed_rules"].append("has_experience")

        if "项目" in resume_text:
            result["passed_rules"].append("has_projects")
        else:
            result["failed_rules"].append("has_projects")

        # 计算总分
        passed_weight = sum(
            self.ATS_RULES[rule]["weight"]
            for rule in result["passed_rules"]
        )
        result["total_score"] = passed_weight

        return result

    def generate_improvement_suggestions(
        self,
        optimized_resume: OptimizedResume,
        jd_analysis: JDAnalysis,
    ) -> List[str]:
        """
        生成改进建议

        Args:
            optimized_resume: 优化后的简历
            jd_analysis: JD分析结果

        Returns:
            改进建议列表
        """
        suggestions = []

        resume_text = optimized_resume.sections.get("完整简历", "")

        # 关键词建议
        missing_keywords = [
            kw for kw in jd_analysis.core_skills
            if kw.lower() not in resume_text.lower()
        ]
        if missing_keywords:
            suggestions.append(
                f"建议补充以下技能关键词: {', '.join(missing_keywords[:3])}"
            )

        # 量化建议
        quant_count = sum(1 for char in resume_text if char.isdigit())
        if quant_count < 3:
            suggestions.append("建议增加更多量化指标，如百分比、绝对值等")

        # STAR法则建议
        if "主导" not in resume_text and "负责" not in resume_text:
            suggestions.append("建议使用STAR法则，重点突出'行动'和'结果'")

        # 隐性需求建议
        if jd_analysis.hidden_requirements:
            suggestions.append(
                f"JD强调'{jd_analysis.hidden_requirements[0]}'，"
                "建议在经历中更突出体现"
            )

        if not suggestions:
            suggestions.append("整体质量良好，继续保持！")

        return suggestions

    def should_iterate(
        self,
        score: float,
        max_retries: int,
        current_iteration: int,
    ) -> bool:
        """
        判断是否需要继续迭代优化

        Args:
            score: 当前匹配度分数
            max_retries: 最大迭代次数
            current_iteration: 当前迭代次数

        Returns:
            是否需要继续迭代
        """
        if current_iteration >= max_retries:
            return False
        if score >= config.MATCH_SCORE_THRESHOLD:
            return False
        return True