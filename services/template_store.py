"""
模板库服务 (Template Store)
Phase 1: 使用JSON文件存储行业模板 + 关键词匹配
Phase 2: 可升级为ChromaDB向量库

设计说明：
这是一个轻量级的模板存储系统，兼容未来的RAG升级。
接口设计预留了向量检索的扩展能力。
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from app_config import config


class TemplateStore:
    """
    简历模板存储库

    Phase 1实现：基于JSON的模板存储
    Phase 2扩展：预留ChromaDB接口，upgrade_to_vector_db()
    """

    # 内置模板（当模板文件不存在时使用）
    DEFAULT_TEMPLATES = {
        "大模型应用": {
            "industry": "大模型应用",
            "keywords": ["LLM", "GPT", "Agent", "RAG", "Prompt", "LangChain"],
            "phrases": [
                "主导了基于LLM的产品架构设计",
                "构建了RAG系统提升问答准确率",
                "设计了Prompt模板体系实现标准化输出",
            ],
            "quantifications": {
                "准确率": "85%+",
                "响应时间": "<2s",
                "召回率": "90%+",
            },
        },
        "量化交易": {
            "industry": "量化交易",
            "keywords": ["因子", "策略", "回测", "风控", "高频"],
            "phrases": [
                "开发了多因子选股模型",
                "搭建了量化回测系统",
                "设计了风控预警机制",
            ],
            "quantifications": {
                "年化收益": "15%+",
                "回撤控制": "<10%",
                "因子数量": "50+",
            },
        },
        "新能源": {
            "industry": "新能源",
            "keywords": ["储能", "锂电", "碳中和", "BMS", "热管理"],
            "phrases": [
                "参与了储能系统的产品设计",
                "优化了BMS算法提升电池寿命",
                "推动了碳中和产品的商业化落地",
            ],
            "quantifications": {
                "电池寿命": "提升20%+",
                "能量效率": "95%+",
            },
        },
        "电商": {
            "industry": "电商",
            "keywords": ["增长", "变现", "供应链", "推荐系统", "搜索"],
            "phrases": [
                "设计了增长策略带来X%用户提升",
                "优化了推荐系统提升CTR",
                "搭建了供应链管理系统",
            ],
            "quantifications": {
                "GMV提升": "30%+",
                "转化率": "提升X%",
            },
        },
        "SaaS": {
            "industry": "SaaS",
            "keywords": ["B端", "ARR", "MRR", "续费率", "NPS"],
            "phrases": [
                "设计了B端产品架构",
                "搭建了客户成功体系",
                "优化了产品NPS评分",
            ],
            "quantifications": {
                "ARR增长": "40%+",
                "续费率": "90%+",
            },
        },
        "通用互联网": {
            "industry": "通用互联网",
            "keywords": ["产品经理", "需求分析", "项目管理", "数据分析"],
            "phrases": [
                "主导了产品需求分析和设计",
                "协调跨团队推动项目交付",
                "通过数据驱动优化产品体验",
            ],
            "quantifications": {
                "项目交付": "准时率95%+",
            },
        },
    }

    def __init__(self):
        """初始化模板库"""
        self.templates: Dict = {}
        self._load_templates()

    def _load_templates(self):
        """从文件加载模板（如果存在）"""
        templates_file = config.TEMPLATES_DIR / "resume_templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, "r", encoding="utf-8") as f:
                    self.templates = json.load(f)
            except Exception as e:
                print(f"⚠️ 加载模板文件失败: {e}, 使用内置模板")
                self.templates = self.DEFAULT_TEMPLATES.copy()
        else:
            self.templates = self.DEFAULT_TEMPLATES.copy()

    def get_template(self, industry: str) -> Optional[Dict]:
        """
        获取指定行业的模板

        Args:
            industry: 行业名称

        Returns:
            模板字典，如果不存在返回None
        """
        return self.templates.get(industry)

    def match_industry(self, jd_text: str) -> str:
        """
        根据JD文本匹配最可能的行业

        Args:
            jd_text: JD描述文本

        Returns:
            最匹配的行业名称
        """
        jd_lower = jd_text.lower()
        best_match = "通用互联网"
        best_score = 0

        for industry, template in self.templates.items():
            score = 0
            for keyword in template.get("keywords", []):
                if keyword.lower() in jd_lower:
                    score += 1
            if score > best_score:
                best_score = score
                best_match = industry

        return best_match

    def get_relevant_phrases(
        self,
        industry: str,
        keyword: str,
        limit: int = 3,
    ) -> List[str]:
        """
        获取与特定关键词相关的推荐短语

        Args:
            industry: 行业名称
            keyword: 关键词
            limit: 返回数量限制

        Returns:
            推荐短语列表
        """
        template = self.get_template(industry)
        if not template:
            return []

        phrases = template.get("phrases", [])
        # 简单过滤：返回所有短语（实际生产中可以做更复杂的语义匹配）
        return phrases[:limit]

    def get_quantification基准(self, industry: str, metric: str) -> Optional[str]:
        """
        获取特定行业指标的量化基准

        Args:
            industry: 行业名称
            metric: 指标名称

        Returns:
            量化基准值字符串
        """
        template = self.get_template(industry)
        if not template:
            return None
        return template.get("quantifications", {}).get(metric)

    def save_templates(self):
        """保存模板到文件"""
        config.ensure_dirs()
        templates_file = config.TEMPLATES_DIR / "resume_templates.json"
        with open(templates_file, "w", encoding="utf-8") as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)

    # === Phase 2预留接口 ===
    def upgrade_to_vector_db(self, vector_db_path: str = None):
        """
        升级到向量数据库（Phase 2实现）

        预留接口，当前为空实现。
        升级时需要：
        1. 安装chromadb: pip install chromadb
        2. 初始化ChromaDB客户端
        3. 将templates转换为embeddings存入向量库
        4. 修改match_industry()为向量检索

        Args:
            vector_db_path: 向量数据库路径
        """
        raise NotImplementedError(
            "Phase 2功能预留：请等待后续升级\n"
            "升级后将支持语义化的模板检索"
        )

    def is_vector_db_available(self) -> bool:
        """
        检查是否已升级到向量数据库

        Returns:
            是否使用向量数据库
        """
        return False  # 当前版本不支持向量检索


# 全局单例
template_store = TemplateStore()