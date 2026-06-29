# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class OcrWord:
    text: str
    location: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OcrResult:
    text: str
    words: List[OcrWord] = field(default_factory=list)


class OCRProvider(ABC):
    """OCR 服务抽象基类。"""

    name: str = "base"

    @abstractmethod
    async def recognize(self, image_path: str) -> OcrResult:
        """识别图片中的文字，返回文本内容和位置信息。"""
        pass

    async def recognize_multiple(self, image_paths: list[str]) -> OcrResult:
        """识别多张图片中的文字，按顺序拼接成一篇文章。"""
        if not image_paths:
            return OcrResult(text="", words=[])

        results = []
        words = []
        for path in image_paths:
            result = await self.recognize(path)
            results.append(result.text)
            words.extend(result.words)

        # 用换行拼接，保留各图片的段落结构
        return OcrResult(text="\n".join(results), words=words)
