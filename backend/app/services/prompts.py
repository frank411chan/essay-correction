# -*- coding: utf-8 -*-
"""作文批改 Prompt 模板。"""
from typing import List, Optional


def split_paragraphs(text: str) -> List[str]:
    """将识别文本拆分为段落列表。

    优先按双换行拆分；若结果只有一段且文本含多个单换行，则按单换行拆分。
    过滤空行，保留非空段落。
    """
    if not text:
        return []

    # 统一换行符
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    # 先尝试双换行
    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]

    # 如果只有一段，但内部有多个单换行，则按单换行拆分
    if len(paragraphs) <= 1 and "\n" in normalized:
        paragraphs = [p.strip() for p in normalized.split("\n") if p.strip()]

    return paragraphs


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


# ============== 通用批改要求（始终生效） ==============
GENERAL_CORRECTION_REQUIREMENTS = """
通用批改要求：
1. 紧扣题目：文章是否围绕标题展开，立意是否切合题意，有无偏题、跑题或套作痕迹。
2. 中心明确：是否有清晰的主旨或中心论点，能否在关键位置（开头、结尾、段首）得到体现。
3. 结构完整：开头、主体、结尾是否完整，段落划分是否合理，过渡是否自然。
4. 内容充实：选材是否具体、真实、有细节，避免空泛说教或简单罗列。
5. 语言规范：用词准确，语句通顺，修辞得当；重点纠正错别字、病句、标点误用。
6. 书写工整：卷面整洁、字迹清晰（根据 OCR 识别情况综合判断）。
7. 鼓励为主：在指出问题的同时，发掘学生作文的亮点，给出可操作的修改建议。
"""


# ============== 深圳中考作文批改标准 ==============
SHENZHEN_GRADING_REQUIREMENTS = """
【深圳中考作文评分标准】先定档，再按细则加减分。

档位（满分 45）：
一类文 40–45：立意深刻紧扣题，素材真实细腻以小见大，有心理/场景细节，情感真挚有成长感悟，构思新颖详略完美；语言流畅优美善用修辞，无病句；结构严谨开头点题结尾升华；卷面工整。
二类文 35–39：立意正确中心明确，选材具体有真情，详略得当；语言通顺少量修辞偶有轻微语病；结构完整分段清晰首尾呼应；卷面整洁。
三类文 30–34：立意基本贴题，素材单薄细节少情感平淡，详略失衡；语言基本通顺有多处语病、用词平淡；结构完整但过渡生硬；卷面一般。
四类文 25–29：立意偏离，选材不贴题内容空洞叙事不完整；语句不通语病多几乎无描写；结构残缺分段混乱；卷面潦草。
五类文 <25：严重偏题、套作抄袭、内容空洞、文体混乱。
六类文 ≤10：完全离题、字数不足 300、抄题干、只写标题。

硬性扣分：
- 字数：不足 600 每少 50 扣 1；350–599 最高 24；300 以内 ≤15；200 以内 ≤10；不足 100 给 0–5。
- 错别字：每字扣 1，重复错字只扣 1 次，累计最多扣 3。
- 标点：3 处以上明显误用或一逗到底，扣 1–2。
- 卷面潦草/涂改多：降 1 档（最多扣 5）。
- 泄露真实校名/人名：扣 1–2。
- 套作/抄袭：直接 <25 分。

高分关键：拒空洞模板（雨夜送伞、生病补课等老套路）；优先真实个人经历；第一人称写出“从前→转变→感悟”；虚实结合；记叙文为王。

阅卷流程：双评分差 ≤3 取平均，>3 三评；审题权重最高，语言结构次之。
"""


def build_topic_analysis_prompt(title: str, grade: str, genre: Optional[str] = None) -> str:
    """根据作文题目生成审题 Prompt。"""
    if genre and genre in GENRE_TEMPLATES:
        template = GENRE_TEMPLATES[genre]
        genre_section = f"- 文体：{template['name']}"
        genre_focus = f"\n\n{template['focus']}"
    else:
        genre_section = "- 文体：未指定"
        genre_focus = ""

    return f"""你是一位资深的语文教师，请先对下面这篇作文的题目进行审题分析。

作文信息：
- 标题：{title or "未提供"}
- 年级：{grade}
{genre_section}
{genre_focus}

请严格按照以下 JSON 格式返回审题结论，不要包含任何其他内容：
{{
  "topic_keywords": ["关键词1", "关键词2"],
  "core_requirements": "题目对立意、内容的核心要求",
  "writing_focus": "写作时应重点突出的方向",
  "common_pitfalls": "学生容易出现的偏题、失分问题",
  "grading_emphasis": "批改评分时应特别关注的维度"
}}

注意：
- 所有字段必须存在，如果没有内容请使用空字符串或空数组。
- 只返回 JSON，不要包含 markdown 代码块标记。
"""


def build_correction_prompt(
    recognized_text: str,
    title: str,
    grade: str,
    genre: Optional[str] = None,
    topic_analysis: dict = None,
) -> str:
    """生成融合审题结论与通用批改要求的批改 Prompt。"""
    if genre and genre in GENRE_TEMPLATES:
        template = GENRE_TEMPLATES[genre]
        genre_section = f"- 文体：{template['name']}\n\n{template['focus']}\n"
    else:
        genre_section = "- 文体：未指定\n\n"

    topic_section = ""
    if topic_analysis:
        topic_section = f"""【审题结论】
- 题目关键词：{", ".join(topic_analysis.get("topic_keywords", []))}
- 核心要求：{topic_analysis.get("core_requirements", "")}
- 写作重点：{topic_analysis.get("writing_focus", "")}
- 常见失分点：{topic_analysis.get("common_pitfalls", "")}
- 评分侧重点：{topic_analysis.get("grading_emphasis", "")}

"""

    paragraphs = split_paragraphs(recognized_text)
    paragraph_mapping = "\n".join(
        [f"第 {i + 1} 段：{p[:60]}{'...' if len(p) > 60 else ''}" for i, p in enumerate(paragraphs)]
    ) if paragraphs else "（未识别到段落）"

    return f"""你是一位经验丰富、熟悉深圳中考阅卷标准的语文教师。请对以下学生作文按照深圳中考作文批改标准进行专业批改。

作文信息：
- 标题：{title or "未提供"}
- 年级：{grade}
{genre_section}{topic_section}{GENERAL_CORRECTION_REQUIREMENTS}

{SHENZHEN_GRADING_REQUIREMENTS}

作文原文如下（位于 === 之间）：
===
{recognized_text}
===

【段落划分】
请严格按照以下已划分好的段落进行精细化批改，不要合并或拆分段落：
{paragraph_mapping}

请严格按照以下 JSON 格式返回，不要包含任何其他内容：
{{
  "recognized_text": "",
  "total_score": 0,
  "shenzhen_score": 0,
  "shenzhen_level": "档位名称",
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
  "suggestions": [
    {{
      "problem": "具体问题描述",
      "advice": "具体可落地的修改建议，说明补什么细节、怎么改",
      "original": "文中需要修改的原文片段",
      "suggested": "建议修改后的具体片段"
    }}
  ],
  "corrected_sentences": [
    {{"original": "病句原文", "corrected": "修改后"}}
  ],
  "topic_analysis": {{
    "topic_keywords": ["关键词1"],
    "core_requirements": "",
    "writing_focus": "",
    "common_pitfalls": "",
    "grading_emphasis": ""
  }},
  "general_requirements": "本次批改依据的通用要求概述（100字左右）",
  "paragraph_reviews": [
    {{
      "paragraph_index": 1,
      "original": "该段原文",
      "comment": "对该段的批改意见",
      "typos": [
        {{"wrong": "错字", "correct": "正字"}}
      ],
      "sentence_corrections": [
        {{"original": "病句", "corrected": "修改后"}}
      ]
    }}
  ],
  "highlights": ["本次亮点1", "本次亮点2"],
  "deep_diagnosis": {{
    "problem": "核心问题描述",
    "cause": "出现原因分析",
    "suggestion": "改进方向建议"
  }},
  "writing_improvement": {{
    "example_author": "名家/范文出处",
    "example_analysis": "名家写法分析",
    "summary": "可迁移的写作方法总结"
  }}
}}

注意：
- shenzhen_score 必须是 0–45 之间的整数，代表深圳中考作文得分。请严格按照深圳中考档位标准先定档，再按字数、错别字、标点、卷面等细则加减分。
- shenzhen_level 必须与 shenzhen_score 严格对应：40–45 为一类文，35–39 为二类文，30–34 为三类文，25–29 为四类文，10–24 为五类文，0–9 为六类文。
- total_score 是 shenzhen_score 按百分制换算后的整数，计算公式：round(shenzhen_score * 100 / 45)。
- content 满分 30，structure 满分 20，language 满分 25，writing 满分 25；四个维度得分之和应等于 total_score。
- 字数判定：请根据 recognized_text 估算字数（不含标题），并按深圳标准扣减 shenzhen_score。
- 错别字：请逐字逐句检查，每个错别字在 typos 中列出，但 shenzhen_score 中最多扣 3 分。
- 套作/抄袭嫌疑：如发现明显套作、抄袭，shenzhen_score 直接降至 25 分以下，并在 comments 中说明。
- paragraph_reviews 必须严格按照【段落划分】中的段落顺序列出，段落数量必须与【段落划分】一致，每个段落生成一条 review。original 字段只需摘录该段开头 10–20 字，不要复制整段原文。
- typos 中的 wrong 和 correct 尽量为单个汉字或词语；请认真检查形近字、音近字、漏字、多字。
- suggestions 必须给出 2–3 条最重要的、具体可落地的修改建议。每条建议必须包含：problem（问题，一句话概括）、advice（具体修改方向，说明补什么细节或怎么改，不少于 30 字）、original（需要修改的原文片段，30–80 字，必须真实出自原文）、suggested（你修改后的完整片段，30–80 字，要自然流畅，可直接替换原文）。要像教师面批一样：先指出具体问题，再告诉学生补哪些细节，最后给出一段可以直接替换进原文的改写示例。
- 请保持输出简洁：comments.overall 200 字以内，paragraph_reviews 每段评论 80 字以内，suggestions 每条 advice 30–80 字。
- 请根据作文实际质量严格评分，不能千篇一律。
- recognized_text 字段留空即可，系统会自动填入原文。
- 所有字段必须存在，如果没有内容请使用空字符串或空数组。
- 只返回 JSON，不要包含 markdown 代码块标记。
"""
