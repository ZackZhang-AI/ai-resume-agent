"""
Agent B: 简历优化师 (The Optimizer)

目标：在真实经历边界内生成可投递简历，而不是机械包装。
"""
import json
import re
from typing import List, Tuple

from models.schema import JDAnalysis, OptimizedResume, OptimizationLogic
from services.llm_client import create_llm_client


class OptimizerAgent:
    """使用STAR法则和真实性约束重构简历内容。"""

    VERB_UPGRADE = {
        "做": "推进",
        "写": "撰写",
        "看": "分析",
        "完成": "交付",
    }

    def __init__(self, llm_client=None):
        self.llm_client = llm_client if llm_client is not None else create_llm_client()

    async def optimize(
        self,
        original_resume: str,
        jd_analysis: JDAnalysis,
        feedback: str = None,
    ) -> OptimizedResume:
        if self.llm_client:
            return await self._ai_optimize(original_resume, jd_analysis, feedback)
        return self._rule_based_optimize(original_resume, jd_analysis, feedback)

    def _rule_based_optimize(
        self,
        original_resume: str,
        jd_analysis: JDAnalysis,
        feedback: str = None,
    ) -> OptimizedResume:
        lines = original_resume.strip().split("\n")
        optimized_lines = []
        optimization_logics: List[OptimizationLogic] = []
        quantifications_added: List[str] = []
        risk_flags: List[str] = []

        for line in lines:
            if not line.strip():
                optimized_lines.append(line)
                continue

            optimized_line, logics, quants = self._process_line(line, jd_analysis)
            optimized_lines.append(optimized_line)
            optimization_logics.extend(logics)
            quantifications_added.extend(quants)
            risk_flags.extend(self._detect_line_risks(line, optimized_line))

        optimized_text = "\n".join(optimized_lines)
        match_score = self._calculate_match_score(optimized_text, jd_analysis)

        return OptimizedResume(
            sections={"完整简历": optimized_text},
            optimization_logics=optimization_logics,
            quantifications_added=quantifications_added,
            match_score=match_score,
            missing_info_questions=self.diagnose_missing_info(original_resume, jd_analysis),
            risk_flags=sorted(set(risk_flags)),
            quality_notes=[
                "当前为规则兜底模式，适合发现缺口，不建议直接作为最终投递版本。",
                "请补充[需补充: ...]中的真实数据后再生成正式版本。",
            ],
        )

    def _process_line(
        self, line: str, jd_analysis: JDAnalysis
    ) -> Tuple[str, List[OptimizationLogic], List[str]]:
        original_line = line
        optimization_logics: List[OptimizationLogic] = []
        quantifications_added: List[str] = []

        for weak_verb, strong_verb in self.VERB_UPGRADE.items():
            if weak_verb in line and strong_verb not in line:
                line = line.replace(weak_verb, strong_verb, 1)
                optimization_logics.append(
                    OptimizationLogic(
                        original_text=original_line,
                        optimized_text=line,
                        reason="使用更清晰但不夸大职责边界的动词",
                        jd_keyword_matched="表达清晰度",
                    )
                )
                break

        if self._looks_like_experience_line(line) and not self._has_quantified_result(line):
            line = f"{line.rstrip()} [需补充: 结果指标、规模或周期]"
            quantifications_added.append(f"建议为'{original_line[:20]}...'补充具体数值")

        return line, optimization_logics, quantifications_added

    def diagnose_missing_info(self, resume_text: str, jd_analysis: JDAnalysis) -> List[str]:
        questions = []
        if not self._has_quantified_result(resume_text):
            questions.append("请补充核心项目的真实结果指标，例如准确率、转化率、效率提升、用户规模或交付周期。")

        missing_skills = [
            skill for skill in jd_analysis.core_skills
            if skill.lower() not in resume_text.lower()
        ]
        if missing_skills:
            questions.append(f"JD强调{', '.join(missing_skills[:4])}，请确认你是否有相关真实经历或工具使用证据。")

        if "参与" in resume_text:
            questions.append("简历中有“参与”表述，请补充你的具体职责边界：负责哪一块、产出物是什么、决策权到哪里。")

        if any("从0到1" in req for req in jd_analysis.hidden_requirements):
            questions.append("请确认是否有从0到1搭建产品/流程/系统的经历；如果没有，应改为协作或迭代优化表述。")

        return questions[:6]

    def _calculate_match_score(self, optimized_text: str, jd_analysis: JDAnalysis) -> float:
        text_lower = optimized_text.lower()
        keywords = jd_analysis.core_skills + jd_analysis.soft_skills
        if not keywords:
            return 45.0
        matched = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        base = (matched / len(keywords)) * 70
        if "[需补充:" in optimized_text:
            base -= 10
        return round(max(30.0, min(base, 82.0)), 1)

    async def _ai_optimize(
        self,
        original_resume: str,
        jd_analysis: JDAnalysis,
        feedback: str = None,
    ) -> OptimizedResume:
        feedback_section = f"\n## 上次优化反馈\n{feedback}" if feedback else ""
        prompt = f"""你是一位严格、保守、面向真实投递的中文简历编辑。你的任务不是包装夸大，而是在用户已有事实边界内生成可以投递的简历成稿。

## 目标岗位信息
职能类型: {jd_analysis.function_type}
行业背景: {jd_analysis.industry_context}
核心技能: {', '.join(jd_analysis.core_skills) if jd_analysis.core_skills else '无'}
软技能: {', '.join(jd_analysis.soft_skills) if jd_analysis.soft_skills else '无'}
隐性需求: {', '.join(jd_analysis.hidden_requirements) if jd_analysis.hidden_requirements else '无'}
岗位常见痛点: {', '.join(jd_analysis.pain_points) if jd_analysis.pain_points else '无具体数据'}
工具链: {', '.join(jd_analysis.tool_chains) if jd_analysis.tool_chains else '无具体要求'}
行业常用动词: {', '.join(jd_analysis.industry_verbs) if jd_analysis.industry_verbs else '推进、协调、分析、交付'}
{feedback_section}

## 原始简历
{original_resume}

## 必须遵守的真实性原则
1. 不得引入原文没有的具体数字、百分比、团队人数、用户规模。
2. 不得将“参与/协助”改成“主导/负责整体/owner/负责人”。
3. 不得假设用户使用过原文没有提到的工具；JD要求但原文没有的工具只能进入 missing_info_questions。
4. 不得把个人贡献扩大为公司级、平台级、核心负责人。
5. 缺数据时使用 [需补充: 请填写真实...]，不要编数字。

## 成稿标准
1. 每条核心经历尽量包含背景、行动、结果，但保持简历语言简洁。
2. 允许使用标注：[原文][/原文]、[合理润色][/合理润色]、[需补充: ...]。
3. 自然融入JD关键词，前提是原文有事实支撑。
4. 输出应该像可投递简历，而不是解释性文章。

## 输出JSON格式
严格输出JSON，不要有其他内容：
{{
    "sections": {{"完整简历": "优化后的完整简历"}},
    "missing_info_questions": ["为了生成最终投递版，需要问用户的问题"],
    "risk_flags": ["可能需要用户确认的真实性风险"],
    "quality_notes": ["成稿质量说明"],
    "optimization_logics": [
        {{
            "original_text": "原文（必须是用户真实写过的）",
            "optimized_text": "优化后的版本",
            "reason": "优化原因",
            "jd_keyword_matched": "匹配的JD关键词"
        }}
    ],
    "quantifications_added": ["需要补充量化的具体项目"],
    "match_score": 0到100的数字
}}
"""
        result = await self.llm_client.generate_async(prompt)
        match = re.search(r"\{[\s\S]*\}", result)
        data = json.loads(match.group() if match else result)

        return OptimizedResume(
            sections=data.get("sections", {"完整简历": original_resume}),
            optimization_logics=[
                OptimizationLogic(
                    original_text=item.get("original_text", ""),
                    optimized_text=item.get("optimized_text", ""),
                    reason=item.get("reason", ""),
                    jd_keyword_matched=item.get("jd_keyword_matched", ""),
                )
                for item in data.get("optimization_logics", [])
            ],
            quantifications_added=data.get("quantifications_added", []),
            match_score=self._coerce_score(data.get("match_score", 50.0)),
            missing_info_questions=data.get("missing_info_questions", []),
            risk_flags=data.get("risk_flags", []),
            quality_notes=data.get("quality_notes", []),
        )

    def suggest_quantification(self, context: str) -> List[str]:
        suggestions = []
        if "性能" in context or "效率" in context:
            suggestions.append("建议补充真实的效率或性能变化，例如响应时间、处理时长、人工成本变化。")
        if "用户" in context or "客户" in context:
            suggestions.append("建议补充真实用户规模或影响范围。")
        if "团队" in context or "管理" in context:
            suggestions.append("建议补充真实团队规模和你的职责边界。")
        if "项目" in context or "产品" in context:
            suggestions.append("建议补充项目周期、交付物或上线状态。")
        return suggestions

    def _looks_like_experience_line(self, line: str) -> bool:
        stripped = line.strip()
        if len(stripped) < 12 or stripped.endswith(("：", ":")):
            return False
        markers = ["负责", "参与", "推进", "优化", "设计", "分析", "协助", "协调", "搭建", "开发", "交付"]
        return any(marker in stripped for marker in markers)

    def _has_quantified_result(self, text: str) -> bool:
        return bool(re.search(r"\d+%|\d+人|\d+万|\d+个|增长|提升|降低|转化率|准确率|召回率|留存|GMV|ARR", text))

    def _detect_line_risks(self, original_line: str, optimized_line: str) -> List[str]:
        risks = []
        if "参与" in original_line and "主导" in optimized_line:
            risks.append("职责升级风险：原文为参与，优化后出现主导。")
        if re.search(r"\d+%|\d+人|\d+万|\d+个", optimized_line) and not re.search(r"\d+%|\d+人|\d+万|\d+个", original_line):
            risks.append("量化指标风险：优化后出现原文没有的具体数字。")
        return risks

    def _coerce_score(self, raw_score) -> float:
        if isinstance(raw_score, str):
            cleaned = raw_score.replace("%", "").strip()
            if "/" in cleaned:
                left, right = cleaned.split("/", 1)
                score = float(left) / float(right) * 100
            else:
                score = float(cleaned)
        else:
            score = float(raw_score)
        if score < 1:
            score *= 100
        return round(max(0.0, min(score, 100.0)), 1)
