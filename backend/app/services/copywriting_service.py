"""
AI 文案改写服务
- 接入大模型 API（兼容 OpenAI 格式）
- 一键改写原创文案，降低重复度
- 支持多种改写模式：同义替换、句式重组、风格转换
- 保留时间戳和分镜结构
"""
import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import get_settings

settings = get_settings()

# 改写模式配置
REWRITE_MODES = {
    "synonym": {
        "name": "同义改写",
        "desc": "保持原意，替换同义词，降低重复度",
        "system_prompt": "你是一个专业的短视频文案改写专家。请对用户提供的文案进行同义词替换和轻微句式调整，保持原意不变，但确保与原文有足够差异以降低查重率。只输出改写后的文案，不要解释。",
    },
    "rewrite": {
        "name": "深度改写",
        "desc": "大幅调整句式结构，重新组织语言",
        "system_prompt": "你是一个专业的短视频文案改写专家。请对用户提供的文案进行深度改写，大幅调整句式结构、语序和表达方式，但保持核心信息和节奏感不变。改写后的文案应该读起来自然流畅，适合短视频口播。只输出改写后的文案。",
    },
    "style_change": {
        "name": "风格转换",
        "desc": "转换为幽默/专业/情感等不同风格",
        "system_prompt": "你是一个专业的短视频文案改写专家。请将用户提供的文案转换为更加口语化、轻松幽默的风格，适合短视频平台传播。保持核心信息不变，但让表达更生动有趣。只输出改写后的文案。",
    },
    "optimize": {
        "name": "爆款优化",
        "desc": "优化开头钩子、节奏感和结尾引导",
        "system_prompt": "你是一个爆款短视频文案策划专家。请对用户提供的文案进行优化，重点改进：1)开头3秒钩子要足够吸引人；2)中间内容节奏紧凑有起伏；3)结尾要有引导互动的话术。保持原主题不变。只输出优化后的文案。",
    },
}


class CopywritingService:
    """AI 文案改写服务"""

    def __init__(self, api_base: Optional[str] = None, api_key: Optional[str] = None, model: str = "agnes-2.0-flash"):
        self.api_base = api_base or getattr(settings, "OPENAI_API_BASE", "https://apihub.agnes-ai.com/v1")
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self.model = model

    async def rewrite_script(
        self,
        script: str,
        mode: str = "synonym",
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        改写完整文案脚本
        :param script: 原始文案（可以是纯文本或JSON格式的脚本）
        :param mode: 改写模式 (synonym/rewrite/style_change/optimize)
        :param temperature: 创造性程度 (0-1)
        :return: 改写结果
        """
        mode_config = REWRITE_MODES.get(mode, REWRITE_MODES["synonym"])

        # 判断脚本格式
        is_json = False
        try:
            parsed = json.loads(script)
            if isinstance(parsed, list):
                is_json = True
        except (json.JSONDecodeError, TypeError):
            pass

        if is_json:
            # JSON 格式脚本：逐段改写
            result = await self._rewrite_json_script(script, mode_config["system_prompt"], temperature)
        else:
            # 纯文本：直接改写
            result = await self._rewrite_text(script, mode_config["system_prompt"], temperature)

        return {
            "original": script,
            "rewritten": result,
            "mode": mode,
            "mode_name": mode_config["name"],
            "word_count_original": len(script),
            "word_count_rewritten": len(result),
        }

    async def _rewrite_text(self, text: str, system_prompt: str, temperature: float) -> str:
        """改写纯文本"""
        if not self.api_key:
            raise RuntimeError("未配置 AI API Key")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text},
                    ],
                    "temperature": temperature,
                    "max_tokens": 4096,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")

    async def _rewrite_json_script(self, script_json: str, system_prompt: str, temperature: float) -> str:
        """改写 JSON 格式的脚本（保留结构）"""
        try:
            # 提取文本内容
            data = json.loads(script_json)
            texts_to_rewrite = []
            text_indices = []

            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        text = item.get("text", "") or item.get("script", "") or item.get("voiceover", "")
                        if text:
                            texts_to_rewrite.append(text)
                            text_indices.append(i)
                    elif isinstance(item, str) and item.strip():
                        texts_to_rewrite.append(item)
                        text_indices.append(None)

            if not texts_to_rewrite:
                return script_json

            # 批量改写
            rewritten_texts = await self._batch_rewrite(texts_to_rewrite, system_prompt, temperature)

            # 重建 JSON
            result = json.loads(script_json)
            for idx, orig_idx in enumerate(text_indices):
                if orig_idx is not None and orig_idx < len(result):
                    item = result[orig_idx]
                    if isinstance(item, dict):
                        # 找到第一个文本字段并替换
                        for key in ["text", "script", "voiceover", "description"]:
                            if key in item:
                                item[key] = rewritten_texts[idx]
                                break
                    else:
                        result[orig_idx] = rewritten_texts[idx]

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            # JSON 解析失败，降级为纯文本改写
            return await self._rewrite_text(script_json, system_prompt, temperature)

    async def _batch_rewrite(self, texts: List[str], system_prompt: str, temperature: float) -> List[str]:
        """批量改写多条文本（逐条发送，控制并发）"""
        results = []
        semaphore = asyncio.Semaphore(3)  # 最多3个并发

        async def rewrite_single(text: str):
            async with semaphore:
                return await self._rewrite_text(text, system_prompt, temperature)

        tasks = [rewrite_single(t) for t in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for r in results:
            if isinstance(r, Exception):
                final_results.append(f"[改写异常: {str(r)}]")
            else:
                final_results.append(r)

        return final_results

    async def optimize_script_for_platform(
        self,
        script: str,
        platform: str = "douyin",
    ) -> Dict[str, Any]:
        """
        针对特定平台优化文案
        :param script: 原始文案
        :param platform: 目标平台 (douyin/kuaishou/xiaohongshu)
        :return: 优化结果
        """
        platform_prompts = {
            "douyin": "请针对抖音平台优化这段短视频文案：1)开头要用强钩子抓住注意力；2)控制在15-30秒口播时长；3)加入互动引导话术；4)语言要接地气、有网感。",
            "kuaishou": "请针对快手平台优化这段短视频文案：1)风格要朴实亲切；2)内容要有烟火气；3)适当加入方言感表达；4)结尾引导关注点赞。",
            "xiaohongshu": "请针对小红书平台优化这段短视频文案：1)开头要制造共鸣或悬念；2)内容要有干货价值；3)语气像朋友分享；4)结尾引导收藏评论。",
        }

        prompt = platform_prompts.get(platform, platform_prompts["douyin"])

        if not self.api_key:
            raise RuntimeError("未配置 AI API Key")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": script},
                    ],
                    "temperature": 0.8,
                    "max_tokens": 2048,
                },
            )
            if response.status_code == 200:
                data = response.json()
                optimized = data["choices"][0]["message"]["content"].strip()
                return {
                    "original": script,
                    "optimized": optimized,
                    "platform": platform,
                    "similarity_estimate": "low",
                }
            else:
                raise RuntimeError(f"HTTP {response.status_code}")


# 全局单例
copywriting_service = CopywritingService()