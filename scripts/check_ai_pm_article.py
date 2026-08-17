#!/usr/bin/env python3
"""检查 AI 产品经理专业文章中的占位符和常见风格偏差。"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PLACEHOLDER_PATTERNS = (
    re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b", re.IGNORECASE),
    re.compile(r"\{\{[^}\n]+\}\}"),
    re.compile(r"\[(?:待补|待写|补数据|补来源|插入案例|此处补充)[^]\n]*\]"),
)

EMPTY_OPENINGS = (
    "在当今快速发展的时代",
    "随着人工智能技术的不断发展",
    "随着AI技术的不断发展",
    "随着大模型技术的不断发展",
    "众所周知",
    "不难发现",
    "本文将从",
    "这篇文章将从",
)

MODEL_ROAD_SIGNS = (
    "值得注意的是",
    "需要指出的是",
    "更深一层",
    "更深层的问题",
    "更微妙的是",
    "真正的问题",
    "从某种意义上说",
    "说白了",
    "说穿了",
    "先说结论",
    "归根结底",
)

SPOKEN_FILLERS = (
    "我感觉",
    "其实",
    "说实在的",
    "有点意思",
    "有说法",
)

SPOKEN_REPETITIONS = (
    re.compile(r"(?:真正的\s*){2,}"),
    re.compile(r"(?:其实[，,、\s]*){2,}"),
)

HYPE_OR_AGGRESSION = (
    "颠覆性",
    "革命性",
    "重新定义一切",
    "炸裂",
    "封神",
    "吊打",
    "降维打击",
    "遥遥领先",
    "干死",
    "傻干",
    "吃饱撑的",
    "给一板砖",
    "洗脑",
    "割韭菜",
    "智商税",
)

ABSOLUTE_WORDS = (
    "所有人",
    "所有产品",
    "必然",
    "一定会",
    "从来不会",
    "从来都是",
    "完全没有",
    "毫无疑问",
    "唯一答案",
    "唯一真实",
    "根本不可能",
)

HUMOR_MARKERS = (
    "哈哈",
    "笑死",
    "离谱",
    "打脸",
    "翻车",
    "毕业",
    "祖传",
    "交学费",
    "打地鼠",
)

TITLE_WEIGHT_WORDS = (
    "必然",
    "唯一",
    "彻底",
    "一定",
    "真正",
    "本质",
    "分水岭",
)

EXPERIENCE_MARKERS = (
    "我曾经",
    "我做过",
    "我亲自",
    "我的项目",
    "我们团队",
    "我们当时",
    "我负责",
    "我上线",
)

COUNTER_TERMS = (
    "限制",
    "边界",
    "例外",
    "反方",
    "另一种解释",
    "成立条件",
    "代价",
    "风险",
    "未知",
    "另一方面",
)

USER_TERMS = (
    "用户",
    "客户",
    "使用者",
    "付费方",
    "使用场景",
    "用户任务",
)

BUSINESS_TERMS = (
    "商业",
    "业务",
    "付费",
    "收入",
    "成本",
    "转化",
    "留存",
    "增长",
    "价值",
)

THESIS_TERMS = (
    "我认为",
    "我的判断",
    "应该",
    "建议",
    "关键",
    "取决于",
    "意味着",
    "问题",
    "值得",
    "更适合",
)

REVERSAL_PATTERNS = (
    re.compile(r"(?:并)?不是[^。！？\n]{0,90}而是"),
    re.compile(r"并非[^。！？\n]{0,90}而是"),
    re.compile(r"不在于[^。！？\n]{0,90}而在于"),
    re.compile(r"与其说[^。！？\n]{0,90}(?:不如|倒不如|毋宁)"),
    re.compile(r"你以为[^。！？\n]{0,90}(?:其实|实际)"),
    re.compile(r"(?:表面|看似)[^。！？\n]{0,90}(?:其实|实际|实则)"),
)


@dataclass
class Paragraph:
    line: int
    text: str
    han: int
    sentences: int


def han_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def line_number(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def excerpt(text: str, width: int = 48) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    return value if len(value) <= width else value[: width - 1] + "…"


def mask_non_prose(text: str) -> str:
    """屏蔽代码和网址，同时保留位置与换行。"""

    def mask(match: re.Match[str]) -> str:
        return "".join("\n" if char == "\n" else " " for char in match.group())

    patterns = (
        re.compile(r"\A---\s*\n.*?\n---\s*(?:\n|\Z)", re.DOTALL),
        re.compile(r"```.*?```", re.DOTALL),
        re.compile(r"`[^`\n]*`"),
        re.compile(r"!\[[^\]\n]*\]\([^\n)]*\)"),
        re.compile(r"\]\([^\n)]*\)"),
        re.compile(r"https?://[^\s)>]+"),
    )
    masked = text
    for pattern in patterns:
        masked = pattern.sub(mask, masked)
    return masked


def all_matches(text: str, patterns: tuple[re.Pattern[str], ...]):
    matches = []
    for pattern in patterns:
        matches.extend(pattern.finditer(text))
    return sorted(matches, key=lambda match: match.start())


def term_hits(text: str, terms: tuple[str, ...]):
    hits = []
    for term in terms:
        hits.extend((match.start(), term) for match in re.finditer(re.escape(term), text))
    return sorted(hits)


def prose_paragraphs(text: str) -> list[Paragraph]:
    paragraphs = []
    cursor = 0
    for block in re.split(r"\n\s*\n", text):
        position = text.find(block, cursor)
        cursor = max(cursor, position + len(block))
        clean = re.sub(r"[>*_`]", "", block).strip()
        if not clean or clean.startswith(("#", "http", "![", "```", "|")):
            continue
        if re.match(r"^(?:[-+*]|\d+[.、])\s", clean):
            continue
        count = han_count(clean)
        if count < 6:
            continue
        sentences = max(1, len(re.findall(r"[。！？!?]", clean)))
        paragraphs.append(
            Paragraph(line_number(text, position), clean, count, sentences)
        )
    return paragraphs


def short_streak(paragraphs: list[Paragraph], limit: int = 4):
    streak = []
    for paragraph in paragraphs:
        if paragraph.han <= 22 and paragraph.sentences <= 1:
            streak.append(paragraph)
            if len(streak) >= limit:
                return streak
        else:
            streak = []
    return None


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 AI 产品经理专业文章")
    parser.add_argument(
        "--mode",
        choices=("professional", "essay"),
        default="professional",
        help="professional 检查专业文章，essay 检查个人观察型产品随笔",
    )
    parser.add_argument("path", help="Markdown 或文本文件路径，使用 - 从标准输入读取")
    args = parser.parse_args()

    try:
        original = read_text(args.path)
    except (OSError, UnicodeError) as error:
        print(f"无法读取稿件。{error}", file=sys.stderr)
        return 2

    prose = mask_non_prose(original)
    total_han = han_count(prose)
    if total_han == 0:
        print("没有检测到汉字。", file=sys.stderr)
        return 2

    failures: list[str] = []
    warnings: list[str] = []

    placeholders = all_matches(prose, PLACEHOLDER_PATTERNS)
    for match in placeholders:
        failures.append(
            f"未完成占位符，第 {line_number(original, match.start())} 行，"
            f"“{excerpt(match.group())}”"
        )

    opening_body = re.sub(r"(?m)^\s*#+.*$", "", prose).strip()[:320]
    opening_hits = [term for term in EMPTY_OPENINGS if term in opening_body]
    if opening_hits:
        warnings.append(
            "开头出现空泛铺垫：" + "、".join(opening_hits) + "。直接进入观点或产品问题。"
        )
    if total_han >= 800 and not any(term in opening_body for term in THESIS_TERMS):
        warnings.append("开头 320 字内没有识别到明确判断。确认读者是否足够早地拿到观点。")

    road_hits = term_hits(prose, MODEL_ROAD_SIGNS)
    if road_hits:
        samples = "、".join(dict.fromkeys(term for _, term in road_hits))
        warnings.append(f"出现 {len(road_hits)} 处模型化路标：{samples}。能直接陈述时删除。")

    filler_hits = term_hits(prose, SPOKEN_FILLERS)
    spoken_repetitions = all_matches(prose, SPOKEN_REPETITIONS)
    filler_limit = max(4, total_han // 600)
    if len(filler_hits) > filler_limit or spoken_repetitions:
        samples = "、".join(dict.fromkeys(term for _, term in filler_hits))
        repeat_note = "，并出现口头重复" if spoken_repetitions else ""
        warnings.append(
            f"聊天式填充词共 {len(filler_hits)} 处，当前提醒线为 {filler_limit} 处{repeat_note}。"
            f"重点检查 {samples or '重复表达'}，保留直接感但整理成书面判断。"
        )

    hype_hits = term_hits(prose, HYPE_OR_AGGRESSION)
    if hype_hits:
        samples = "、".join(dict.fromkeys(term for _, term in hype_hits))
        warnings.append(f"出现 {len(hype_hits)} 处营销化或攻击性表达：{samples}。检查是否符合克制语气。")

    reversals = all_matches(prose, REVERSAL_PATTERNS)
    if len(reversals) >= 2:
        samples = "；".join(
            f"第 {line_number(original, match.start())} 行“{excerpt(match.group(), 34)}”"
            for match in reversals[:4]
        )
        warnings.append(f"翻案句共 {len(reversals)} 处，个人风格默认最多保留一处。{samples}")

    title_lines = re.findall(r"(?m)^#{1,4}\s+(.+)$", original)
    weighted_titles = [
        title
        for title in title_lines
        if any(term in title for term in TITLE_WEIGHT_WORDS)
    ]
    if weighted_titles:
        samples = "；".join(excerpt(title, 36) for title in weighted_titles[:4])
        warnings.append(
            "标题或小标题出现偏重判断词。确认范围和证据足以支持：" + samples
        )

    absolute_hits = term_hits(prose, ABSOLUTE_WORDS)
    absolute_limit = max(3, total_han // 500)
    if len(absolute_hits) > absolute_limit:
        samples = "、".join(dict.fromkeys(term for _, term in absolute_hits))
        warnings.append(
            f"绝对化表达共 {len(absolute_hits)} 处，当前提醒线为 {absolute_limit} 处。"
            f"重点检查 {samples}。"
        )

    humor_hits = term_hits(prose, HUMOR_MARKERS)
    if len(humor_hits) > 2:
        samples = "、".join(dict.fromkeys(term for _, term in humor_hits))
        warnings.append(f"轻松或玩笑表达共 {len(humor_hits)} 处：{samples}。个人风格默认最多保留一两处。")

    experience_hits = term_hits(prose, EXPERIENCE_MARKERS)
    if experience_hits:
        lines = "、".join(
            dict.fromkeys(str(line_number(original, position)) for position, _ in experience_hits)
        )
        warnings.append(
            f"第 {lines} 行出现第一人称项目经历。确认这些经历均由用户明确提供或授权。"
        )

    question_count = prose.count("？") + prose.count("?")
    question_limit = max(3, total_han // 700)
    if question_count > question_limit:
        warnings.append(
            f"问号共 {question_count} 个，当前提醒线为 {question_limit} 个。检查是否用反问代替论证。"
        )

    exclamation_count = prose.count("！") + prose.count("!")
    if exclamation_count > 2:
        warnings.append(f"感叹号共 {exclamation_count} 个。专业文章通常不需要持续抬高语气。")

    punctuation_count = prose.count("：") + prose.count(":") + prose.count("—")
    punctuation_limit = max(8, total_han // 140)
    if punctuation_count > punctuation_limit:
        warnings.append(
            f"冒号和破折号共 {punctuation_count} 处，当前提醒线为 {punctuation_limit} 处。"
            "检查是否依赖标点批量制造力度。"
        )

    paragraphs = prose_paragraphs(prose)
    streak = short_streak(paragraphs)
    if streak:
        warnings.append(
            f"从第 {streak[0].line} 行起连续出现 {len(streak)} 个短促单句段。"
            "检查是否在排队写金句。"
        )
    if len(paragraphs) >= 10:
        single_ratio = sum(p.sentences <= 1 for p in paragraphs) / len(paragraphs)
        if single_ratio >= 0.7:
            warnings.append(f"可识别段落中有 {single_ratio:.0%} 只有一句话，段落形状可能过于统一。")

    heading_count = len(re.findall(r"(?m)^#{2,4}\s+\S", original))
    if args.mode == "professional" and total_han >= 1500 and heading_count < 2:
        warnings.append("长文的小标题少于两个。确认复杂观点是否已经清楚分层。")
    if heading_count > 10:
        warnings.append(f"二到四级小标题共 {heading_count} 个。检查框架是否切得过碎。")

    if total_han >= 1200 and not any(term in prose for term in COUNTER_TERMS):
        warnings.append("长文未识别到限制、边界、例外或反方。确认文章是否处理了观点成立条件。")
    if total_han >= 1200 and not any(term in prose for term in USER_TERMS):
        warnings.append("长文未识别到用户或使用场景。确认技术判断是否已经落到用户任务。")
    if (
        args.mode == "professional"
        and total_han >= 1200
        and not any(term in prose for term in BUSINESS_TERMS)
    ):
        warnings.append("长文未识别到商业或业务条件。确认这项缺口是否会影响产品判断。")

    has_numeric_claim = bool(re.search(r"\d+(?:\.\d+)?\s*(?:%|％|倍|万|亿|元|人|次|天|月|年)", prose))
    has_source_signal = bool(
        re.search(r"https?://|\]\(|来源|数据截至|官方文档|论文|报告", original)
    )
    if total_han >= 1000 and has_numeric_claim and not has_source_signal:
        warnings.append("文章包含数字性判断，但未识别到来源信号。确认数字来自用户材料或可靠来源。")

    print(f"汉字数 {total_han}")
    print(
        f"占位符 {len(placeholders)}，模型路标 {len(road_hits)}，"
        f"聊天式填充词 {len(filler_hits)}，"
        f"营销或攻击表达 {len(hype_hits)}，翻案句 {len(reversals)}，"
        f"绝对化表达 {len(absolute_hits)}，轻松表达 {len(humor_hits)}，"
        f"第一人称经历 {len(experience_hits)}，问号 {question_count}，"
        f"感叹号 {exclamation_count}，小标题 {heading_count}"
    )

    if failures:
        print("\n需要修改")
        for item in failures:
            print(f"- {item}")

    if warnings:
        print("\n需要人工判断")
        for item in warnings:
            print(f"- {item}")

    if not failures and not warnings:
        print("\n未发现这份检查器覆盖的问题。")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
