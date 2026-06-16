import pytest

from agents.optimizer import OptimizerAgent
from agents.verifier import VerifierAgent
from agents.recruiter import RecruiterAgent
from models.schema import JDAnalysis, OptimizedResume
from services import llm_client


def sample_jd() -> JDAnalysis:
    return JDAnalysis(
        core_skills=["LLM", "RAG", "LangChain"],
        soft_skills=["跨团队协作", "数据驱动"],
        hidden_requirements=["从0到1构建能力"],
        keyword_weights={"LLM": 0.9},
        industry_context="大模型应用",
        pain_points=[],
        tool_chains=["RAG", "LangChain"],
        industry_verbs=["推进", "协调", "分析"],
        function_type="PM",
    )


def test_rule_optimizer_does_not_duplicate_replacement_text():
    optimizer = OptimizerAgent(llm_client=None)
    resume = "编写产品需求文档，参与机器人逻辑设计。"

    optimized = optimizer._rule_based_optimize(resume, sample_jd())
    text = optimized.sections["完整简历"]

    assert "编编写" not in text
    assert "编写/构建" not in text


def test_rule_optimizer_does_not_upgrade_participation_to_lead():
    optimizer = OptimizerAgent(llm_client=None)
    resume = "参与智能问答系统需求分析，协助研发完成模型接入。"

    optimized = optimizer._rule_based_optimize(resume, sample_jd())
    text = optimized.sections["完整简历"]

    assert "主导" not in text
    assert "牵头" not in text
    assert "参与" in text


def test_verifier_flags_new_numbers_tools_and_role_upgrade():
    verifier = VerifierAgent()
    original = "参与智能客服产品迭代，协助研发完成模型接入。"
    optimized = OptimizedResume(
        sections={"完整简历": "主导智能客服产品从0到1建设，使用LangChain和RAG，提升30%。"},
        optimization_logics=[],
        quantifications_added=[],
        match_score=70,
    )

    warnings, all_confirmed = verifier.verify(original, optimized)
    risk_types = {warning.risk_type for warning in warnings}

    assert not all_confirmed
    assert "quantification" in risk_types
    assert "tool_added" in risk_types
    assert "role_upgrade" in risk_types


def test_missing_api_key_uses_rule_based_quality_mode(monkeypatch):
    monkeypatch.setattr(llm_client.config, "LLM_PROVIDER", None)
    monkeypatch.setattr(llm_client.config, "OPENAI_API_KEY", None)
    monkeypatch.setattr(llm_client.config, "GEMINI_API_KEY", None)
    monkeypatch.setattr(llm_client.config, "MINIMAX_API_KEY", None)

    client = llm_client.create_llm_client()

    assert client is None
    assert llm_client.get_quality_mode(client) == "rule_based"


def test_selected_providers_can_be_instantiated(monkeypatch):
    monkeypatch.setattr(llm_client.config, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(llm_client.config, "GEMINI_API_KEY", "gemini-test")
    monkeypatch.setattr(llm_client.config, "MINIMAX_API_KEY", "minimax-test")

    assert llm_client.create_llm_client("openai").provider == "openai"
    assert llm_client.create_llm_client("gemini").provider == "gemini"
    assert llm_client.create_llm_client("minimax").provider == "minimax"


@pytest.mark.asyncio
async def test_score_is_not_overconfident_with_missing_info():
    recruiter = RecruiterAgent(llm_client=None)
    optimized = OptimizedResume(
        sections={
            "完整简历": (
                "参与智能问答系统需求分析，协助研发完成模型接入。"
                "[需补充: 结果指标、规模或周期]"
            )
        },
        optimization_logics=[],
        quantifications_added=["建议补充指标"],
        match_score=60,
        missing_info_questions=["请补充真实效果指标"],
    )

    report = await recruiter.evaluate(optimized, sample_jd(), risk_count=1, quality_mode="rule_based")

    assert report.overall_score < 85
    assert report.risk_count == 1
    assert report.quality_mode == "rule_based"
