#!/usr/bin/env python3
"""PDF 文本提取工具 — 支持章节识别和分段输出"""

import sys
import re
import pdfplumber
from pathlib import Path


def extract_text(pdf_path: str) -> dict:
    """从 PDF 提取全文文本，按页组织，识别章节结构"""
    pages = []
    full_text = ""
    total_chars = 0

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                pages.append({"page": i, "text": text})
                full_text += f"\n--- 第{i}页 ---\n{text}"
                total_chars += len(text)

    # 识别章节标题（中文常见模式：第X章、数字标题、摘要、目录等）
    chapters = _identify_chapters(full_text)

    return {
        "total_pages": total_pages,
        "total_chars": total_chars,
        "has_text_layer": total_chars > 100,  # 少于100字符可能是扫描版
        "chapters": chapters,
        "full_text": full_text,
        "pages": pages,
    }


def extract_core_sections(full_text: str, chapters: list) -> str:
    """针对硕博论文，只提取核心章节文本"""
    core_keywords = [
        "摘要", "绪论", "引言", "研究背景", "文献综述",
        "研究设计", "研究方法", "研究框架",
        "案例", "实证", "数据分析", "调查",
        "结论", "讨论", "建议", "展望",
    ]

    # 找到核心章节对应的页码范围
    core_chapters = []
    for ch in chapters:
        title_lower = ch["title"].lower()
        for kw in core_keywords:
            if kw in title_lower:
                core_chapters.append(ch)
                break

    if not core_chapters:
        # 没找到匹配章节，返回前30%+后20%的文本（通常包含摘要绪论和结论）
        total_len = len(full_text)
        head = full_text[: int(total_len * 0.3)]
        tail = full_text[-int(total_len * 0.2) :]
        return head + "\n\n... [中间章节已省略] ...\n\n" + tail

    # 拼接核心章节文本
    result = ""
    for ch in sorted(core_chapters, key=lambda x: x["start_pos"]):
        result += f"\n\n## {ch['title']}\n"
        result += full_text[ch["start_pos"] : ch["end_pos"]]

    return result


def _identify_chapters(text: str) -> list:
    """识别文本中的章节标题"""
    chapter_patterns = [
        r"第[一二三四五六七八九十\d]+章\s*[^\n]*",  # 第X章
        r"\n\d+\.\d*\s+[^\n]{2,30}\n",  # 数字编号标题
        r"\n(摘要|ABSTRACT|目录|绪论|引言|前言|结论|展望|参考文献|致谢|附录)\s*\n",
    ]

    chapters = []
    for pattern in chapter_patterns:
        for match in re.finditer(pattern, text):
            title = match.group().strip()
            start = match.start()
            chapters.append({
                "title": title,
                "start_pos": start,
                "end_pos": len(text),  # 先设到末尾，后面排序修正
            })

    # 按位置排序，修正 end_pos
    chapters.sort(key=lambda x: x["start_pos"])
    for i, ch in enumerate(chapters):
        if i + 1 < len(chapters):
            ch["end_pos"] = chapters[i + 1]["start_pos"]

    return chapters


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_extract.py <pdf_path> [--core-only]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    core_only = "--core-only" in sys.argv

    if not Path(pdf_path).exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    result = extract_text(pdf_path)
    print(f"总页数: {result['total_pages']}")
    print(f"总字符: {result['total_chars']}")
    print(f"文字层: {'有' if result['has_text_layer'] else '无(可能是扫描版)'}")
    print(f"识别章节: {len(result['chapters'])} 个")
    for ch in result["chapters"]:
        print(f"  - {ch['title']}")

    if core_only:
        core_text = extract_core_sections(result["full_text"], result["chapters"])
        output_path = Path(pdf_path).stem + "_core.txt"
        Path(output_path).write_text(core_text)
        print(f"\n核心章节已输出到: {output_path} ({len(core_text)} 字符)")
    else:
        output_path = Path(pdf_path).stem + "_full.txt"
        Path(output_path).write_text(result["full_text"])
        print(f"\n全文已输出到: {output_path} ({len(result['full_text'])} 字符)")
