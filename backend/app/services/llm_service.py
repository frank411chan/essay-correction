# -*- coding: utf-8 -*-
import json
import re
from typing import Optional

from openai import OpenAI

from app.config import get_settings
from app.services.prompts import build_correction_prompt, build_topic_analysis_prompt

settings = get_settings()

kimi_client = OpenAI(
    api_key=settings.moonshot_api_key,
    base_url=settings.moonshot_base_url,
)

deepseek_client = None
if settings.deepseek_api_key:
    deepseek_client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
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


def _call_llm_json_client(
    client: OpenAI,
    model: str,
    prompt: str,
    system_prompt: str = "你是一个专业语文教师，擅长作文批改与审题分析。",
    max_tokens: int = 4096,
    retries: int = 2,
) -> dict:
    """使用指定客户端调用 LLM 并解析 JSON，带重试。"""
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            result = extract_json(content)

            if result is None:
                raise ValueError(f"无法从模型响应中解析 JSON: {content[:200]}")

            return result
        except Exception as e:
            last_error = e
            if attempt < retries:
                continue

    raise Exception(f"LLM 调用失败（已重试 {retries} 次）: {str(last_error)}")


def _call_llm_json(prompt: str, max_tokens: int = 4096, retries: int = 2) -> dict:
    """默认使用 Kimi 调用 LLM 并解析 JSON，带重试。"""
    return _call_llm_json_client(
        kimi_client,
        settings.moonshot_model,
        prompt,
        max_tokens=max_tokens,
        retries=retries,
    )


def _normalize_score(score) -> int:
    """将模型返回的分数规范化为整数。"""
    try:
        return int(round(float(score)))
    except (TypeError, ValueError):
        return 0


def normalize_result(result: dict, original_text: str) -> dict:
    """规范化批改结果，填充默认值，并确保 recognized_text 为原始 OCR 文本。"""
    # 强制使用原始识别文本，避免模型在 JSON 中生成非法字符串
    result["recognized_text"] = original_text
    result.setdefault("total_score", 0)
    result.setdefault("shenzhen_score", 0)
    result.setdefault("shenzhen_level", "")
    result.setdefault("dimension_scores", {})
    result.setdefault("comments", {"overall": "", "strengths": [], "weaknesses": []})
    result.setdefault("paragraph_comments", [])
    result.setdefault("suggestions", [])
    result.setdefault("corrected_sentences", [])

    # 新增字段默认值
    result.setdefault("topic_analysis", None)
    result.setdefault("general_requirements", "")
    result.setdefault("paragraph_reviews", [])
    result.setdefault("highlights", [])
    result.setdefault("deep_diagnosis", None)
    result.setdefault("writing_improvement", None)

    # 数值规范化
    result["total_score"] = _normalize_score(result.get("total_score"))
    result["shenzhen_score"] = _normalize_score(result.get("shenzhen_score"))

    # 如果没有 shenzhen_score 但有 total_score，按比例换算
    if result["shenzhen_score"] == 0 and result["total_score"] > 0:
        result["shenzhen_score"] = _normalize_score(result["total_score"] * 45 / 100)

    # 如果只有 shenzhen_score，换算 total_score
    if result["total_score"] == 0 and result["shenzhen_score"] > 0:
        result["total_score"] = _normalize_score(result["shenzhen_score"] * 100 / 45)

    # 修正档位与分数不一致的情况（兜底）
    result["shenzhen_level"] = _score_to_level(result["shenzhen_score"])

    return result


def _score_to_level(score: int) -> str:
    """根据深圳中考分数返回档位。"""
    if score >= 40:
        return "一类文"
    elif score >= 35:
        return "二类文"
    elif score >= 30:
        return "三类文"
    elif score >= 25:
        return "四类文"
    elif score >= 10:
        return "五类文"
    else:
        return "六类文"


async def analyze_topic(title: Optional[str], grade: str, genre: Optional[str] = None) -> Optional[dict]:
    """根据作文题目进行审题分析。"""
    prompt = build_topic_analysis_prompt(title, grade, genre)
    result = _call_llm_json(prompt, max_tokens=2048, retries=2)
    return result


def _single_correct(
    client: OpenAI,
    model: str,
    recognized_text: str,
    title: Optional[str],
    grade: str,
    genre: Optional[str] = None,
    topic_analysis: dict = None,
    max_tokens: int = 4096,
) -> dict:
    """使用指定模型进行一次批改。"""
    prompt = build_correction_prompt(recognized_text, title, grade, genre, topic_analysis)
    result = _call_llm_json_client(
        client,
        model,
        prompt,
        system_prompt="你是一位经验丰富、熟悉深圳中考阅卷标准的语文教师。",
        max_tokens=max_tokens,
        retries=2,
    )
    return normalize_result(result, recognized_text)


def _merge_dual_results(
    result_a: dict,
    result_b: dict,
    original_text: str,
) -> dict:
    """根据深圳中考双评机制合并两份批改结果。"""
    score_a = result_a.get("shenzhen_score", 0)
    score_b = result_b.get("shenzhen_score", 0)

    # 双评分差 <= 3 分，取平均分
    if abs(score_a - score_b) <= 3:
        final_shenzhen = int(round((score_a + score_b) / 2))
        # 选择更详细/分数更接近最终结果的作为主体，再补充另一份评语
        base = result_a.copy() if abs(score_a - final_shenzhen) <= abs(score_b - final_shenzhen) else result_b.copy()
        base["shenzhen_score_first"] = score_a
        base["shenzhen_score_second"] = score_b
        base["shenzhen_score"] = final_shenzhen
        base["total_score"] = _normalize_score(final_shenzhen * 100 / 45)
        base["recognized_text"] = original_text
        base["shenzhen_level"] = _score_to_level(final_shenzhen)

        # 合并亮点与建议；建议为结构化 dict，按 JSON 字符串去重
        base["highlights"] = list(dict.fromkeys(
            (result_a.get("highlights") or []) + (result_b.get("highlights") or [])
        ))
        combined_suggestions = (result_a.get("suggestions") or []) + (result_b.get("suggestions") or [])
        seen = set()
        unique_suggestions = []
        for sg in combined_suggestions:
            key = json.dumps(sg, ensure_ascii=False, sort_keys=True) if isinstance(sg, dict) else str(sg)
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(sg)
        base["suggestions"] = unique_suggestions[:3]  # 最多保留 3 条

        # 总体评语补充双评信息
        overall_a = (result_a.get("comments") or {}).get("overall", "")
        overall_b = (result_b.get("comments") or {}).get("overall", "")
        comments = base.get("comments") or {"overall": "", "strengths": [], "weaknesses": []}
        comments["overall"] = (
            f"【双评结果】第一评 {score_a} 分，第二评 {score_b} 分，最终 {final_shenzhen} 分。\n"
            f"第一评评语：{overall_a}\n"
            f"第二评评语：{overall_b}"
        )
        base["comments"] = comments
        return base

    # 分差 > 3 分，进行三评（使用 Kimi 再次严格评审）
    third = _single_correct(
        kimi_client,
        settings.moonshot_model,
        original_text,
        result_a.get("title"),
        result_a.get("grade", "初中"),
        result_a.get("genre"),
        result_a.get("topic_analysis"),
        max_tokens=8192,
    )
    score_c = third.get("shenzhen_score", 0)
    scores = sorted([score_a, score_b, score_c])
    final_shenzhen = scores[1]  # 取中位数

    base = third.copy()
    base["shenzhen_score_first"] = score_a
    base["shenzhen_score_second"] = score_b
    base["shenzhen_score_third"] = score_c
    base["shenzhen_score"] = final_shenzhen
    base["total_score"] = _normalize_score(final_shenzhen * 100 / 45)
    base["recognized_text"] = original_text
    base["shenzhen_level"] = _score_to_level(final_shenzhen)
    base["suggestions"] = (base.get("suggestions") or [])[:3]

    overall_a = (result_a.get("comments") or {}).get("overall", "")
    overall_b = (result_b.get("comments") or {}).get("overall", "")
    overall_c = (third.get("comments") or {}).get("overall", "")
    comments = base.get("comments") or {"overall": "", "strengths": [], "weaknesses": []}
    comments["overall"] = (
        f"【三评结果】第一评 {score_a} 分，第二评 {score_b} 分，第三评 {score_c} 分，最终 {final_shenzhen} 分。\n"
        f"第一评评语：{overall_a}\n"
        f"第二评评语：{overall_b}\n"
        f"第三评评语：{overall_c}"
    )
    base["comments"] = comments
    return base


async def correct_text(
    recognized_text: str,
    title: Optional[str],
    grade: str,
    genre: Optional[str] = None,
    topic_analysis: dict = None,
    use_dual_evaluation: bool = True,
) -> dict:
    """对已经识别出的文本进行批改，默认启用 Kimi + DeepSeek 双评机制。"""
    # 第一评：Kimi
    result_a = _single_correct(
        kimi_client,
        settings.moonshot_model,
        recognized_text,
        title,
        grade,
        genre,
        topic_analysis,
        max_tokens=8192,
    )

    # 第二评：DeepSeek（如果配置了 API key 且启用双评）
    if use_dual_evaluation and deepseek_client:
        result_b = _single_correct(
            deepseek_client,
            settings.deepseek_model,
            recognized_text,
            title,
            grade,
            genre,
            topic_analysis,
            max_tokens=8192,
        )
        return _merge_dual_results(result_a, result_b, recognized_text)

    # 未启用双评，直接返回第一评结果，并补齐双评字段
    result_a["shenzhen_score_first"] = result_a.get("shenzhen_score", 0)
    result_a["shenzhen_score_second"] = None
    return result_a
