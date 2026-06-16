"""
Agent C: 模拟面试官 (The Recruiter)
职责：基于优化后的简历和JD，生成5-10个最具挑战性的面试问题，
     并对用户的回答进行打分。

核心功能：
1. 生成针对JD的面试问题
2. 评估简历匹配度
3. 提供改进反馈
"""
from typing import List
from models.schema import (
    JDAnalysis,
    OptimizedResume,
    ScoreReport,
    InterviewQuestion,
)
from services.llm_client import create_llm_client


class RecruiterAgent:
    """
    模拟面试官 - 基于简历和JD生成面试问题并评分
    """

    # 问题类型与JD关键词的映射
    QUESTION_TEMPLATES = {
        "从0到1": [
            "请描述一个你从0到1搭建产品的经历，遇到的最大挑战是什么？",
            "如何在资源有限的情况下推动一个创新项目落地？",
        ],
        "跨团队": [
            "请举例说明你如何协调不同部门推动项目完成",
            "遇到团队利益冲突时你是怎么处理的？",
        ],
        "技术深度": [
            "你如何保证与技术团队的沟通不走样？",
            "请解释一个技术决策背后的产品考量",
        ],
        "数据驱动": [
            "请举例说明你如何用数据驱动产品决策",
            "A/B测试中如何判断实验结果的统计显著性？",
        ],
        "规模化": [
            "如何设计系统架构以支撑业务规模化增长？",
            "请描述一个处理高并发的案例",
        ],
        "商业化": [
            "如何平衡用户体验和商业化目标？",
            "你的产品如何为公司创造收入？",
        ],
    }

    # 评分维度定义
    SCORE_DIMENSIONS = {
        "JD匹配": "是否覆盖目标岗位的关键能力",
        "真实性风险": "是否存在未确认的量化、职责升级或工具栈新增",
        "STAR完整度": "是否说明背景、行动和结果",
        "可读性": "是否结构清晰、语言自然",
        "可投递度": "是否接近可直接投递版本",
    }

    def __init__(self, llm_client=None):
        """
        初始化模拟面试官

        Args:
            llm_client: LLM客户端实例，若为None则自动从配置创建MiniMax客户端
        """
        if llm_client is None:
            llm_client = create_llm_client()
        self.llm_client = llm_client

    async def generate_questions(
        self,
        optimized_resume: OptimizedResume,
        jd_analysis: JDAnalysis,
    ) -> List[InterviewQuestion]:
        """
        生成面试问题

        Args:
            optimized_resume: 优化后的简历
            jd_analysis: JD分析结果

        Returns:
            面试问题列表
        """
        if self.llm_client:
            return await self._ai_generate_questions(optimized_resume, jd_analysis)
        return self._rule_based_generate_questions(optimized_resume, jd_analysis)

    def _rule_based_generate_questions(
        self,
        optimized_resume: OptimizedResume,
        jd_analysis: JDAnalysis,
    ) -> List[InterviewQuestion]:
        """基于规则生成面试问题（无需API调用）"""
        questions: List[InterviewQuestion] = []

        # 1. 基于隐性需求生成问题
        for hidden_req in jd_analysis.hidden_requirements:
            for key, templates in self.QUESTION_TEMPLATES.items():
                if key in hidden_req:
                    for template in templates[:1]:  # 每个类型取一个问题
                        questions.append(
                            InterviewQuestion(
                                question=template,
                                type=self._classify_question_type(key),
                                evaluation_criteria=self.SCORE_DIMENSIONS.get(
                                    "逻辑性", ""
                                ),
                                sample_answer="[参考答案示例]",
                                jd_keyword_targeted=hidden_req,
                            )
                        )

        # 2. 基于核心技能生成技术面问题
        for skill in jd_analysis.core_skills[:2]:  # 最多2个
            questions.append(
                InterviewQuestion(
                    question=f"你对{skill}在产品工作中的实际应用有什么理解？",
                    type="技术面",
                    evaluation_criteria="是否展现技术深度和实际应用能力",
                    sample_answer=f"[关于{skill}的参考答案]",
                    jd_keyword_targeted=skill,
                )
            )

        # 3. 生成经典行为面问题
        classic_questions = [
            ("最大挑战", "行为面"),
            ("失败经历", "压力面"),
            ("团队冲突", "行为面"),
        ]
        for q_type, p_type in classic_questions[:2]:
            questions.append(
                InterviewQuestion(
                    question=f"请描述你在工作中遇到的一次{q_type}，你是如何应对的？",
                    type=p_type,
                    evaluation_criteria="STAR法则 + 体现成长性",
                    sample_answer="[STAR格式参考答案]",
                    jd_keyword_targeted="软技能",
                )
            )

        return questions[:10]  # 最多10个问题

    def _classify_question_type(self, keyword: str) -> str:
        """根据关键词分类问题类型"""
        type_mapping = {
            "从0到1": "行为面",
            "跨团队": "行为面",
            "技术深度": "技术面",
            "数据驱动": "技术面",
            "规模化": "技术面",
            "商业化": "业务面",
        }
        return type_mapping.get(keyword, "行为面")

    async def _ai_generate_questions(
        self,
        optimized_resume: OptimizedResume,
        jd_analysis: JDAnalysis,
    ) -> List[InterviewQuestion]:
        """
        使用AI生成更具挑战性的面试问题（需要API调用）
        """
        resume_text = optimized_resume.sections.get("完整简历", "")

        prompt = f"""
你是一个专业的面试官。请根据以下简历和JD分析结果，生成10个针对性的面试问题。

## JD分析结果
核心技能: {', '.join(jd_analysis.core_skills)}
软技能: {', '.join(jd_analysis.soft_skills)}
隐性需求: {', '.join(jd_analysis.hidden_requirements)}

## 优化后的简历
{resume_text}

## 输出要求
严格输出JSON格式，不要有其他内容：
{{
    "questions": [
        {{
            "question": "问题文本",
            "type": "问题类型（行为面/技术面/压力面等）",
            "evaluation_criteria": "评估标准",
            "sample_answer": "参考答案示例",
            "jd_keyword_targeted": "对应的JD关键词"
        }}
    ]
}}
"""
        import json
        import re

        result = await self.llm_client.generate_async(prompt)

        # 尝试提取JSON
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(result)

        return [
            InterviewQuestion(
                question=q.get("question", ""),
                type=q.get("type", "行为面"),
                evaluation_criteria=q.get("evaluation_criteria", ""),
                sample_answer=q.get("sample_answer", ""),
                jd_keyword_targeted=q.get("jd_keyword_targeted", ""),
            )
            for q in data.get("questions", [])
        ][:10]  # 最多10个问题

    async def evaluate(
        self,
        optimized_resume: OptimizedResume,
        jd_analysis: JDAnalysis,
        risk_count: int = 0,
        quality_mode: str = "rule_based",
    ) -> ScoreReport:
        """
        评估简历质量

        Args:
            optimized_resume: 优化后的简历
            jd_analysis: JD分析结果

        Returns:
            评分报告
        """
        # 计算各维度得分
        dimensions = self._calculate_dimensions(optimized_resume, jd_analysis, risk_count)

        # 生成雷达图
        from utils.ascii_chart import ASCIIRadarChart

        radar_chart = ASCIIRadarChart()
        radar_ascii = radar_chart.draw(list(dimensions.keys()), list(dimensions.values()))

        # 计算综合得分
        overall_score = sum(dimensions.values()) / len(dimensions)
        if risk_count > 0:
            overall_score = min(overall_score, 72.0)
        resume_text = optimized_resume.sections.get("完整简历", "")
        if "[需补充:" in resume_text:
            overall_score = min(overall_score, 78.0)
        if quality_mode == "rule_based":
            overall_score = min(overall_score, 80.0)

        # 生成反馈
        feedback = self._generate_feedback(dimensions, jd_analysis)

        # 评估面试准备度
        readiness = self._evaluate_readiness(overall_score)

        return ScoreReport(
            overall_score=round(overall_score, 1),
            dimensions=dimensions,
            radar_chart_ascii=radar_ascii,
            feedback=feedback,
            interview_readiness=readiness,
            risk_count=risk_count,
            quality_mode=quality_mode,
        )

    def _calculate_star_score_strict(self, resume_text: str) -> float:
        """计算STAR法则使用得分 - 更严格的版本"""
        import re
        score = 0

        # 1. 检查STAR关键词（最高30分）
        star_keywords = {
            "情境/背景": ["面对", "为了解决", "在", "背景下", "面对", "情境"],
            "任务/目标": ["负责", "主导", "承担", "面临", "职责"],
            "行动": ["推动", "协调", "设计", "构建", "搭建", "开发", "完成", "实现", "优化", "提升", "主导", "负责"],
            "结果": ["提升了", "增长了", "优化了", "实现了", "完成了", "获得", "达到", "增长", "提升"],
        }

        for category, keywords in star_keywords.items():
            count = sum(1 for kw in keywords if kw in resume_text)
            if count >= 2:
                score += 7.5
            elif count >= 1:
                score += 3.5

        # 2. 量化结果检查（最高40分）
        percentages = re.findall(r'\d+%', resume_text)
        numbers = re.findall(r'\d+', resume_text)

        if percentages:
            score += 25
        if len(numbers) >= 5:
            score += 15
        elif len(numbers) >= 3:
            score += 10

        # 3. 动词多样性（最高30分）
        strong_verbs = ["主导", "负责", "推动", "协调", "设计", "构建", "搭建", "实现", "优化"]
        verb_count = sum(1 for v in strong_verbs if v in resume_text)
        score += min(verb_count * 4, 30)

        return min(score, 100)

    def _calculate_dimensions(
        self,
        optimized_resume: OptimizedResume,
        jd_analysis: JDAnalysis,
        risk_count: int = 0,
    ) -> dict:
        """计算各维度得分"""
        resume_text = optimized_resume.sections.get("完整简历", "")

        # 1. JD匹配：检查技能关键词匹配
        jd_score = 50
        matched_skills = sum(
            1 for skill in jd_analysis.core_skills
            if skill.lower() in resume_text.lower()
        )
        if jd_analysis.core_skills:
            jd_score = 35 + (matched_skills / len(jd_analysis.core_skills)) * 50

        # 2. 真实性风险：风险越多分越低，未确认占位也扣分
        authenticity_score = max(35, 90 - risk_count * 15)
        if "[需补充:" in resume_text:
            authenticity_score = min(authenticity_score, 65)

        # 3. STAR完整度：要求行动和结果，但不因数字密度直接高分
        star_score = self._calculate_star_score_strict(resume_text)
        if "[需补充:" in resume_text:
            star_score = min(star_score, 70)

        # 4. 可读性：简单检查换行和结构
        readability_score = 50
        line_count = resume_text.count("\n")
        if line_count > 15:
            readability_score = 80
        elif line_count > 8:
            readability_score = 65

        # 5. 可投递度：综合完成度和待补充情况
        deliverability_score = min(jd_score, star_score, readability_score)
        if optimized_resume.missing_info_questions:
            deliverability_score = min(deliverability_score, 68)
        if risk_count > 0:
            deliverability_score = min(deliverability_score, 62)

        return {
            "JD匹配": round(jd_score, 1),
            "真实性风险": round(authenticity_score, 1),
            "STAR完整度": round(star_score, 1),
            "可读性": round(readability_score, 1),
            "可投递度": round(deliverability_score, 1),
        }

    def _generate_feedback(self, dimensions: dict, jd_analysis: JDAnalysis) -> str:
        """生成改进反馈"""
        feedbacks = []

        # 找出最低分项
        min_dim = min(dimensions, key=dimensions.get)
        if dimensions[min_dim] < 70:
            feedbacks.append(f"建议强化'{min_dim}'部分")

        # 检查匹配度
        if jd_analysis.hidden_requirements:
            feedbacks.append(f"JD强调'{jd_analysis.hidden_requirements[0]}'，建议在简历中更突出体现")

        if not feedbacks:
            feedbacks.append("整体质量良好，可继续完善细节")

        return "；".join(feedbacks)

    def _evaluate_readiness(self, overall_score: float) -> str:
        """评估面试准备度"""
        if overall_score >= 80:
            return "🌟 准备充分，可以出击"
        elif overall_score >= 70:
            return "👍 基本就绪，建议再完善技术深度"
        elif overall_score >= 60:
            return "💪 需要强化，建议针对薄弱环节准备"
        else:
            return "📚 建议继续完善简历后再投递"
