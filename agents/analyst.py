 
"""
Agent A: JD深度解码员 (The Analyst)
职责：抓取或解析目标岗位的JD，识别出隐藏的"核心关键词"、技术栈偏好和软技能需求。
亮点：它不只是看字面意思，而是分析出"这家公司更看重从0到1的构建能力，还是大规模系统的稳定性"。
"""
from typing import Dict, List
from models.schema import JDAnalysis
from services.llm_client import create_llm_client


class AnalystAgent:
    """
    JD深度解码员 - 分析Job Description中的显性和隐性需求
    """

    # JD中常见的隐性需求模式
    HIDDEN_PATTERNS = {
        "从0到1": "候选人有独立搭建产品/系统的经验，而非仅参与已有项目",
        "大规模系统": "候选人有处理高并发、海量数据的架构设计经验",
        "跨团队": "候选人具备跨部门协调、推动落地的能力",
        "商业化": "候选人有将技术/产品落地并产生商业价值的经验",
        "技术深度": "候选人不只是传话筒，而有技术理解能力",
        "创新": "候选人有提出并落地新方案的案例",
    }

    # 软技能关键词映射
    SOFT_SKILL_PATTERNS = {
        "协作": ["跨团队", "协作", "配合", "协调", "沟通"],
        "owner": ["owner", "负责人", "主导", "推动"],
        "数据驱动": ["数据驱动", "A/B测试", "量化", "指标"],
        "结果导向": ["结果导向", "KPI", "交付", "落地"],
    }

    def __init__(self, llm_client=None):
        """
        初始化解码员

        Args:
            llm_client: LLM客户端实例，若为None则自动从配置创建MiniMax客户端
        """
        if llm_client is None:
            llm_client = create_llm_client()
        self.llm_client = llm_client

    async def analyze(self, job_description: str) -> JDAnalysis:
        """
        深度解码JD

        Args:
            job_description: 岗位描述文本

        Returns:
            JDAnalysis: 结构化的JD分析结果
        """
        # 如果有LLM客户端，使用AI增强分析
        if self.llm_client:
            return await self._ai_analyze(job_description)
        # 否则使用规则基础分析
        return self._rule_based_analyze(job_description)

    def _rule_based_analyze(self, jd_text: str) -> JDAnalysis:
        """基于规则的分析（无需API调用）"""
        jd_lower = jd_text.lower()

        # 提取核心技能（简单关键词匹配）
        core_skills = []
        skill_keywords = [
            "python", "llm", "gpt", "langchain", "数据分析",
            "机器学习", "深度学习", "产品经理", "ai",
            "sql", "prompt", "rag", "nlp"
        ]
        for skill in skill_keywords:
            if skill in jd_lower:
                core_skills.append(skill)

        # 提取软技能
        soft_skills = []
        for skill_name, patterns in self.SOFT_SKILL_PATTERNS.items():
            for pattern in patterns:
                if pattern in jd_lower:
                    if skill_name not in soft_skills:
                        soft_skills.append(skill_name)
                    break

        # 识别隐性需求
        hidden_reqs = []
        for pattern, description in self.HIDDEN_PATTERNS.items():
            if pattern in jd_lower:
                hidden_reqs.append(description)

        # 计算关键词权重
        keyword_weights = {}
        for skill in core_skills:
            keyword_weights[skill] = 0.8  # 默认权重

        # 行业背景判断
        industry_context = self._detect_industry(jd_text)

        return JDAnalysis(
            core_skills=core_skills,
            soft_skills=soft_skills,
            hidden_requirements=hidden_reqs,
            keyword_weights=keyword_weights,
            industry_context=industry_context,
            pain_points=[],
            tool_chains=[],
            industry_verbs=["主导", "负责", "推进", "协调"],
            function_type="PM",
        )

    def _detect_industry(self, jd_text: str) -> str:
        """检测行业背景"""
        industry_markers = {
            "大模型应用": ["llm", "gpt", "大模型", "生成式", "agent", "垂类模型"],
            "量化交易": ["量化", "因子", "策略", "交易", "市值"],
            "新能源": ["新能源", "碳中和", "储能", "电动车", "锂电"],
            "电商": ["电商", "直播", "供应链", "增长", "变现"],
            "SaaS": ["SaaS", "B端", "企业服务", "订阅", "ARR"],
        }

        jd_lower = jd_text.lower()
        for industry, markers in industry_markers.items():
            if any(marker in jd_lower for marker in markers):
                return industry
        return "通用互联网"

    async def _ai_analyze(self, jd_text: str) -> JDAnalysis:
        """
        使用AI进行深度分析（需要API调用）
        """
        prompt = f"""
你是一个专业的HR JD分析师。请分析以下岗位描述，输出结构化的分析结果。

## 岗位描述
{jd_text}

## 输出要求
请严格输出以下格式的JSON（不要有其他内容）：
{{
    "core_skills": ["硬技能列表，如Python、LLM、SQL"],
    "soft_skills": ["软技能列表，如跨团队协作、数据驱动"],
    "hidden_requirements": ["隐性需求列表，如'从0到1构建能力'"],
    "keyword_weights": {{"关键词": 权重}},
    "industry_context": "行业背景，如'大模型应用层'",
    "pain_points": ["该岗位常见的业务/技术挑战，如'用户留存率低'、'QPS瓶颈'"],
    "tool_chains": ["JD中提到的工具/技术栈，如'LangChain'、'CRM系统'"],
    "industry_verbs": ["该岗位常用的行动动词，如'主导'、'推进'、'统筹'"],
    "function_type": "职能类型，如PM/运营/市场/算法/研发"
}}

## 分析要求
1. core_skills: 识别硬技能/技术栈要求
2. soft_skills: 识别软技能要求（如协作、数据驱动等）
3. hidden_requirements: 分析隐含的深层需求（如"从0到1构建能力"等）
4. keyword_weights: 关键词重要性权重（0-1）
5. industry_context: 判断行业背景
6. pain_points: 该岗位面试官常问的"你遇到过什么挑战"类型的问题
7. tool_chains: JD明确提到或暗示要使用的工具/平台/框架
8. industry_verbs: 该岗位招聘信息中常用的动词，反映工作性质
9. function_type: 判断是PM/运营/市场/算法/研发中的哪一类
"""
        result = await self.llm_client.generate_async(prompt)
        import json
        import re

        # 尝试提取JSON
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(result)

        return JDAnalysis(
            core_skills=data.get("core_skills", []),
            soft_skills=data.get("soft_skills", []),
            hidden_requirements=data.get("hidden_requirements", []),
            keyword_weights=data.get("keyword_weights", {}),
            industry_context=data.get("industry_context", "通用互联网"),
            pain_points=data.get("pain_points", []),
            tool_chains=data.get("tool_chains", []),
            industry_verbs=data.get("industry_verbs", []),
            function_type=data.get("function_type", "PM"),
        )

    def get_keyword_weight(self, analysis: JDAnalysis, keyword: str) -> float:
        """获取特定关键词的权重"""
        return analysis.keyword_weights.get(keyword.lower(), 0.5)
