"""
MiniMax API 客户端
用于与 MiniMax 大模型进行交互
"""
import json
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, Any


class MiniMaxClient:
    """MiniMax API 客户端，封装与 MiniMax 大模型交互的逻辑"""

    provider = "minimax"
    # Coding Plan (sk-cp-) keys use China endpoint
    DEFAULT_BASE_URL = "https://api.minimaxi.com/v1"
    # Coding Plan includes MiniMax-M2.7 model
    DEFAULT_MODEL = "MiniMax-M2.7"

    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        model: str = None,
        temperature: float = 0.7,
        timeout: int = 120,
    ):
        """
        初始化 MiniMax 客户端

        Args:
            api_key: MiniMax API 密钥
            base_url: API 基础 URL，默认使用中国区节点
            model: 模型名称，默认使用 MiniMax-M2.7
            temperature: 生成温度参数
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or self.DEFAULT_MODEL
        self.temperature = temperature
        self.timeout = timeout

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        生成文本回复

        Args:
            prompt: 用户输入的提示词
            system: 系统提示词（可选）

        Returns:
            模型生成的文本回复

        Raises:
            Exception: 当API返回错误时抛出异常
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        url = f"{self.base_url}/text/chatcompletion_v2"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 16000,
        }

        # 使用 urllib 避免 requests session 复用问题
        import urllib.request
        import urllib.error

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"MiniMax API HTTP Error {e.code}: {error_body}")

        # 检查API错误
        if result.get("base_resp", {}).get("status_code", 0) != 0:
            error_msg = result.get("base_resp", {}).get("status_msg", "Unknown error")
            raise Exception(f"MiniMax API Error [{result['base_resp']['status_code']}]: {error_msg}")

        # 检查choices
        if not result.get("choices"):
            raise Exception("MiniMax API returned no choices")

        return result["choices"][0]["message"]["content"]

    def generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """
        生成 JSON 格式的回复

        Args:
            prompt: 用户输入的提示词
            system: 系统提示词（可选）

        Returns:
            解析后的 JSON 对象
        """
        text = self.generate(prompt, system)
        # 尝试提取 JSON 部分
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            return json.loads(json_match.group())
        # 如果没有找到 JSON，尝试直接解析
        return json.loads(text)

    async def generate_async(self, prompt: str, system: Optional[str] = None) -> str:
        """
        异步生成文本回复（使用 asyncio）

        Args:
            prompt: 用户输入的提示词
            system: 系统提示词（可选）

        Returns:
            模型生成的文本回复
        """
        import asyncio

        def _sync_call():
            return self.generate(prompt, system)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_call)
