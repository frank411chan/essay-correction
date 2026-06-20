# -*- coding: utf-8 -*-
"""作文批改 Prompt 模板。"""

GENRE_TEMPLATES = {
    "narrative": {
        "name": "记叙文",
        "focus": """
记叙文批改要点：
- 内容：事件是否完整、具体、有真情实感
- 结构：时间/空间顺序是否清晰，开头结尾是否呼应
- 语言：描写是否生动，修辞运用是否恰当
- 书写：卷面整洁、字迹清晰
""",
    },
    "argumentation": {
        "name": "议论文",
        "focus": """
议论文批改要点：
- 内容：论点是否明确、正确，论据是否充分、典型
- 结构：引论、本论、结论是否完整，论证层次是否清晰
- 语言：逻辑严密，说理透彻，语言准确
- 书写：卷面整洁、字迹清晰
""",
    },
    "description": {
        "name": "说明文",
        "focus": """
说明文批改要点：
- 内容：说明对象是否明确，特征是否抓准
- 结构：说明顺序是否合理，条理是否清晰
- 语言：准确、简明、通俗，说明方法运用得当
- 书写：卷面整洁、字迹清晰
""",
    },
    "prose": {
        "name": "散文",
        "focus": """
散文批改要点：
- 内容：立意是否新颖，情感是否真挚
- 结构：形散神聚，线索清晰
- 语言：语言优美，意境深远，善用修辞
- 书写：卷面整洁、字迹清晰
""",
    },
}


def get_genre_name(genre: str) -> str:
    return GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["narrative"])["name"]


def build_correction_prompt(
    recognized_text: str,
    title: str,
    grade: str,
    genre: str = "narrative",
) -> str:
    template = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["narrative"])

    return f"""你是一位经验丰富的语文教师。请对以下学生作文进行批改。

作文信息：
- 标题：{title or "未提供"}
- 年级：{grade}
- 文体：{template['name']}

{template['focus']}

作文原文如下（位于 === 之间）：
===
{recognized_text}
===

评分标准：
- 优秀（90-100）：中心突出、结构完整、语言流畅、书写工整
- 良好（80-89）：中心明确、结构较完整、语言较流畅、书写较工整
- 中等（70-79）：中心基本明确、结构基本完整、语言基本通顺、书写一般
- 及格（60-69）：中心不够明确、结构不够完整、语言不够通顺、书写较差
- 不及格（0-59）：偏离题意、结构混乱、语句不通、书写潦草

请严格按照以下 JSON 格式返回，不要包含任何其他内容：
{{
  "recognized_text": "",
  "total_score": 0,
  "dimension_scores": {{
    "content": 0,
    "structure": 0,
    "language": 0,
    "writing": 0
  }},
  "comments": {{
    "overall": "总体评语",
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["不足1", "不足2"]
  }},
  "paragraph_comments": [
    {{
      "paragraph_index": 1,
      "comment": "这一段..."
    }}
  ],
  "suggestions": ["建议1", "建议2"],
  "corrected_sentences": [
    {{"original": "病句原文", "corrected": "修改后"}}
  ]
}}

注意：
- total_score 必须是 0-100 之间的整数，根据作文实际质量评分，严禁固定给 85
- content 满分 30，structure 满分 20，language 满分 25，writing 满分 25
- 四个维度得分之和应等于 total_score
- 请根据作文实际质量严格评分，不能千篇一侓
- recognized_text 字段留空即可，系统会自动填入原文
- 所有字段必须存在，如果没有内容请使用空字符串或空数组
- 只返回 JSON，不要包含 markdown 代码块标记
"""
