"""
应用配置文件
管理全局配置项，包括循环次数、评分阈值、API配置等
"""
import os
from pathlib import Path
from typing import Optional


class AppConfig:
    """应用配置管理"""

    # === Agent行为控制 ===
    MAX_RETRIES: int = 3  # 评分循环最大迭代次数，防止死循环
    MATCH_SCORE_THRESHOLD: float = 75.0  # 简历匹配度合格阈值，低于此值触发优化循环

    # === API配置 ===
    # 支持OpenAI、Gemini和MiniMax，优先从环境变量读取
    LLM_PROVIDER: Optional[str] = os.getenv("LLM_PROVIDER")
    LLM_MODEL: Optional[str] = os.getenv("LLM_MODEL")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    MINIMAX_API_KEY: Optional[str] = os.getenv("MINIMAX_API_KEY")

    # MiniMax配置 (Coding Plan sk-cp- 系列密钥使用 api.minimaxi.com)
    MINIMAX_BASE_URL: str = "https://api.minimaxi.com/v1"
    MINIMAX_MODEL: str = "MiniMax-M2.7"
    MINIMAX_TEMPERATURE: float = 0.7

    # 默认使用GPT-4o，可切换到Gemini或MiniMax
    DEFAULT_MODEL: str = "gpt-4o"  # 或 "gemini-1.5-pro" 或 "minimax-text-01"
    TEMPERATURE: float = 0.7  # 生成稳定性

    # === 路径配置 ===
    PROJECT_ROOT: Path = Path(__file__).parent
    TEMPLATES_DIR: Path = PROJECT_ROOT / "templates"
    OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"

    # === 评分维度 ===
    SCORE_DIMENSIONS: list = [
        "逻辑性",
        "技术深度",
        "业务贡献",
        "排版美观",
    ]

    # === 模板行业分类 ===
    SUPPORTED_INDUSTRIES: list = [
        "大模型应用",
        "量化交易",
        "新能源",
        "电商",
        "SaaS",
    ]

    @classmethod
    def validate(cls) -> bool:
        """验证配置完整性"""
        has_api_key = cls.OPENAI_API_KEY or cls.GEMINI_API_KEY or cls.MINIMAX_API_KEY
        if not has_api_key:
            print("⚠️ 警告: 未设置API密钥，环境变量: OPENAI_API_KEY / GEMINI_API_KEY / MINIMAX_API_KEY")
            print("请设置后重试，或使用模拟模式运行")
            return False
        return True

    @classmethod
    def ensure_dirs(cls) -> None:
        """确保必要目录存在"""
        cls.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


# 全局单例
config = AppConfig()
