"""
Agent V: 防幻觉校验员 (The Verifier)
核心差异化设计：防止AI在优化简历时编造或夸大用户的经历

职责：
1. 对比"原始简历文本"和"优化后文本"
2. 高亮出所有新增的数字、量化指标和技能点
3. 弹窗提示用户确认这些量化指标是否真实可达
4. 阻塞式确认后才允许流程继续

设计理念：
"人机协同"而非"纯AI替代"——AI可以提供建议，但真实性由用户负责。
这体现了AI PM对AIGC合规性风险的深刻理解。
"""
import re
from typing import List, Tuple
from models.schema import (
    OptimizedResume,
    QuantificationWarning,
)


class VerifierAgent:
    """
    防幻觉校验员 - 确保AI优化不超出用户真实能力范围
    """

    # 量化指标的正则表达式模式
    QUANTITY_PATTERNS = [
        r"\d+%",           # 百分比：30%, 60%
        r"\d+x",           # 倍数：3x, 10x
        r"\d+万",          # 绝对值：10万用户
        r"\d+万+",         # 更多绝对值
        r"提升\d+",        # 提升30
        r"增长\d+",        # 增长50
        r"减少\d+",        # 减少40
        r"从\d+到\d+",     # 从200ms到80ms
        r"\d+人",          # 5人团队
        r"\d+个",          # 3个项目
        r"管理\d+",        # 管理10人
        r"\d+[\.\d]*[kKmM]", # 10k, 1.5M
    ]

    # 技能增强的标记词
    SKILL_UPGRADE_PATTERNS = [
        "主导",
        "构建",
        "设计",
        "搭建",
        "创建",
        "从0到1",
        "owner",
        "负责人",
        "统筹",
        "牵头",
    ]

    TOOL_PATTERNS = [
        "LangChain",
        "RAG",
        "Prompt Engineering",
        "ChromaDB",
        "向量数据库",
        "微调",
        "A/B测试",
        "SQL",
        "Python",
        "Agent",
    ]

    COMPANY_IMPACT_PATTERNS = [
        "公司级",
        "平台级",
        "核心",
        "全链路",
        "千万级",
        "百万级",
        "行业领先",
    ]

    def __init__(self):
        """初始化校验员"""
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self.quantity_regex = re.compile("|".join(self.QUANTITY_PATTERNS), re.IGNORECASE)
        self.skill_upgrade_regex = re.compile(
            "|".join(self.SKILL_UPGRADE_PATTERNS), re.IGNORECASE
        )
        self.tool_regex = re.compile("|".join(re.escape(item) for item in self.TOOL_PATTERNS), re.IGNORECASE)
        self.company_impact_regex = re.compile("|".join(self.COMPANY_IMPACT_PATTERNS), re.IGNORECASE)

    def verify(
        self,
        original_resume: str,
        optimized_resume: OptimizedResume,
    ) -> Tuple[List[QuantificationWarning], bool]:
        """
        校验优化后的简历

        Args:
            original_resume: 原始简历文本
            optimized_resume: AI优化后的简历

        Returns:
            (warnings, all_confirmed): 警告列表 和 是否全部确认
        """
        warnings: List[QuantificationWarning] = []

        # 1. 提取原始简历中的量化指标
        original_quantities = set(self.quantity_regex.findall(original_resume))

        # 2. 提取优化简历中的量化指标
        optimized_text = "\n".join(optimized_resume.sections.values())
        optimized_quantities = self.quantity_regex.findall(optimized_text)

        # 3. 找出新增的量化指标（可能是AI编造的）
        for quant in optimized_quantities:
            if quant not in original_quantities:
                # 这是新增的量化指标，需要用户确认
                warnings.append(
                    QuantificationWarning(
                        risk_type="quantification",
                        original_claim=self._get_context_for_quant(
                            original_resume, quant
                        ),
                        suggested_claim=quant,
                        basis="AI基于行业基准推荐，请确认实际是否达到",
                        user_confirmed=False,
                    )
                )

        # 4. 检测技能升级是否过度
        warnings.extend(self._detect_role_upgrade_risks(original_resume, optimized_text))
        warnings.extend(self._detect_new_tool_risks(original_resume, optimized_text))
        warnings.extend(self._detect_company_impact_risks(original_resume, optimized_text))

        original_upgrades = self.skill_upgrade_regex.findall(original_resume)
        optimized_upgrades = self.skill_upgrade_regex.findall(optimized_text)
        if len(optimized_upgrades) > len(original_upgrades) + 3:
            warnings.append(
                QuantificationWarning(
                    risk_type="role_upgrade",
                    original_claim="原始经历描述",
                    suggested_claim=f"AI建议使用{len(optimized_upgrades)}个强化动词",
                    basis="强化动词使用过多可能不符合实际情况",
                    user_confirmed=False,
                )
            )

        # 5. 如果有待确认的警告，需要用户确认
        if warnings:
            return warnings, False

        return warnings, True

    def _detect_role_upgrade_risks(self, original_resume: str, optimized_text: str) -> List[QuantificationWarning]:
        warnings: List[QuantificationWarning] = []
        original_has_participation = any(word in original_resume for word in ["参与", "协助", "配合"])
        upgraded_terms = ["主导", "牵头", "统筹", "负责人", "owner", "从0到1"]
        for term in upgraded_terms:
            if term.lower() in optimized_text.lower() and term.lower() not in original_resume.lower():
                if original_has_participation or term in ["负责人", "owner", "从0到1"]:
                    warnings.append(
                        QuantificationWarning(
                            risk_type="role_upgrade",
                            original_claim="原始简历未明确该职责层级",
                            suggested_claim=term,
                            basis="职责层级升级需要用户确认，避免把参与/协助包装成主导。",
                        )
                    )
        return warnings

    def _detect_new_tool_risks(self, original_resume: str, optimized_text: str) -> List[QuantificationWarning]:
        warnings: List[QuantificationWarning] = []
        original_tools = {tool.lower() for tool in self.tool_regex.findall(original_resume)}
        for tool in set(self.tool_regex.findall(optimized_text)):
            if tool.lower() not in original_tools:
                warnings.append(
                    QuantificationWarning(
                        risk_type="tool_added",
                        original_claim="原始简历未明确该工具或技术栈",
                        suggested_claim=tool,
                        basis="新增工具栈必须有真实使用证据，否则应改为了解/学习/待补充。",
                    )
                )
        return warnings

    def _detect_company_impact_risks(self, original_resume: str, optimized_text: str) -> List[QuantificationWarning]:
        warnings: List[QuantificationWarning] = []
        original_terms = {term.lower() for term in self.company_impact_regex.findall(original_resume)}
        for term in set(self.company_impact_regex.findall(optimized_text)):
            if term.lower() not in original_terms:
                warnings.append(
                    QuantificationWarning(
                        risk_type="impact_scope",
                        original_claim="原始简历未明确该影响范围",
                        suggested_claim=term,
                        basis="公司级/平台级/大规模影响表述需要事实支撑。",
                    )
                )
        return warnings

    def _get_context_for_quant(self, text: str, quant: str) -> str:
        """
        获取量化指标所在的上下文（原始描述）
        """
        lines = text.split("\n")
        for line in lines:
            if quant in line:
                # 返回该行附近的原始描述
                return line.strip()
        return "原始简历中未找到相关描述"

    def confirm_quantification(
        self,
        warnings: List[QuantificationWarning],
        confirmed_indices: List[int],
    ) -> List[QuantificationWarning]:
        """
        更新用户确认状态

        Args:
            warnings: 警告列表
            confirmed_indices: 用户确认的索引列表

        Returns:
            更新后的警告列表
        """
        for i, warning in enumerate(warnings):
            if i in confirmed_indices:
                warning.user_confirmed = True
        return warnings

    def interactive_confirm(self, warnings: List[QuantificationWarning]) -> bool:
        """
        交互式确认——打印警告信息并等待用户输入

        Args:
            warnings: 需要确认的警告列表

        Returns:
            是否全部确认通过
        """
        if not warnings:
            print("\n✅ Verifier检查通过：未发现新增量化指标")
            return True

        print("\n" + "=" * 60)
        print("⚠️  Verifier检测到以下新增量化指标，需要您确认：")
        print("=" * 60)

        confirmed_indices = []

        for i, warning in enumerate(warnings):
            print(f"\n[{i + 1}] 量化建议：{warning.suggested_claim}")
            print(f"    原始描述：{warning.original_claim}")
            print(f"    AI依据：{warning.basis}")

            # 简化确认流程
            while True:
                response = input("    确认此指标真实可达？(y/n/q退出): ").lower().strip()
                if response == "y":
                    confirmed_indices.append(i)
                    break
                elif response == "n":
                    break
                elif response == "q":
                    print("\n用户取消，流程终止")
                    return False
                else:
                    print("    请输入 y(是) / n(否) / q(退出)")

        # 更新警告状态
        self.confirm_quantification(warnings, confirmed_indices)

        all_confirmed = len(confirmed_indices) == len(warnings)
        if all_confirmed:
            print("\n✅ 全部量化指标已确认，流程继续")
        else:
            unconfirmed = len(warnings) - len(confirmed_indices)
            print(f"\n⚠️  有{unconfirmed}项未确认，这些内容将被移除")

        return all_confirmed

    def filter_unconfirmed(self, optimized_resume: OptimizedResume, warnings: List[QuantificationWarning]) -> OptimizedResume:
        """
        过滤掉用户未确认的量化指标

        Args:
            optimized_resume: 优化后的简历
            warnings: 警告列表

        Returns:
            过滤后的简历
        """
        # 获取用户未确认的量化指标
        unconfirmed_quants = set()
        for w in warnings:
            if not w.user_confirmed:
                unconfirmed_quants.add(w.suggested_claim)

        if not unconfirmed_quants:
            return optimized_resume

        # 替换未确认的量化指标为更保守的描述
        filtered_sections = {}
        for section_name, content in optimized_resume.sections.items():
            filtered_content = content
            for quant in unconfirmed_quants:
                # 将具体数字替换为更保守的描述
                filtered_content = filtered_content.replace(
                    quant, "[已移除待确认数据]"
                )
            filtered_sections[section_name] = filtered_content

        return OptimizedResume(
            sections=filtered_sections,
            optimization_logics=optimized_resume.optimization_logics,
            quantifications_added=optimized_resume.quantifications_added,
            match_score=optimized_resume.match_score,
            missing_info_questions=optimized_resume.missing_info_questions,
            risk_flags=optimized_resume.risk_flags,
            quality_notes=optimized_resume.quality_notes,
        )
