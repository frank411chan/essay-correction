# -*- coding: utf-8 -*-
import json
import re
from typing import Optional

from openai import OpenAI

from app.config import get_settings
from app.services.prompts import build_correction_prompt

settings = get_settings()
client = OpenAI(
    api_key=settings.moonshot_api_key,
    base_url=settings.moonshot_base_url,
)


def extract_json(text: str) -> Optional[dict]:
    """从模型返回中提取 JSON。"""
    text = text.strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 代码块
    code_block_pattern = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
    match = code_block_pattern.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试提取花括号内容
    brace_pattern = re.compile(r"(\{.*\})", re.DOTALL)
    match = brace_pattern.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None


def normalize_result(result: dict, original_text: str) -> dict:
    """规范化批改结果，填充默认值，并确保 recognized_text 为原始 OCR 文本。"""
    # 强制使用原始识别文本，避免模型在 JSON 中生成非法字符串
    result["recognized_text"] = original_text
    result.setdefault("total_score", 0)
    result.setdefault("dimension_scores", {})
    result.setdefault("comments", {"overall": "", "strengths": [], "weaknesses": []})
    result.setdefault("paragraph_comments", [])
    result.setdefault("suggestions", [])
    result.setdefault("corrected_sentences", [])
    return result


async def correct_text(
    recognized_text: str,
    title: Optional[str],
    grade: str,
    genre: str = "narrative",
) -> dict:
    """使用 Kimi 对已经识别出的文本进行批改。"""
    prompt = build_correction_prompt(recognized_text, title, grade, genre)

    max_retries = 2
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=settings.moonshot_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业语文教师，擅长作文批改。",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.3,
                max_tokens=4096,
            )

            content = response.choices[0].message.content
            result = extract_json(content)

            if result is None:
                raise ValueError(f"无法从模型响应中解析 JSON: {content[:200]}")

            return normalize_result(result, recognized_text)

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue

    raise Exception(f"批改失败（已重试 {max_retries} 次）: {str(last_error)}")
