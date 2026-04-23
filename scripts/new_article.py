#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path

from build_static_site import CONTENT_KNOWLEDGE, SECTION_GROUPS


SECTION_LABELS = {
    "papers": "论文解读",
    "ai-tools": "AI工具",
    "experience": "经验分享",
    "game-space": "游戏空间",
}

TEMPLATES = {
    "paper-series": """## 论文对比

| 论文 | 主要解决问题 | 待改进方向 |
| --- | --- | --- |
| 论文 A |  |  |
| 论文 B |  |  |

## 论文一

> 论文标题

### 解决问题

- 

### 模型结构

- 

### 样本构造

- 

### 关键信息

- 

### 实验结论

- 

## 论文二

> 论文标题

### 解决问题

- 

### 模型结构

- 

### 样本构造

- 

### 关键信息

- 

### 实验结论

- 
""",
    "single-card": """## 背景


## 核心问题


## 方法

### 关键点一


### 关键点二


## 实践观察


## 总结

""",
}


def prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{text}{suffix}: ").strip()
    return value or (default or "")


def slugify(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.replace("——", "-").replace("—", "-").replace("–", "-")
    normalized = normalized.replace("：", "-").replace(":", "-")
    normalized = normalized.replace("/", "-").replace("\\", "-")
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[^\w\-\u4e00-\u9fff]+", "", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized


def parse_tags(raw: str) -> list[str]:
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def choose_section(section: str | None) -> str:
    if section:
        return section
    default_section = "experience"
    section_keys = ", ".join(SECTION_LABELS)
    return prompt(f"模块（{section_keys}）", default_section)


def choose_group(section: str, group: str | None) -> str:
    if group:
        return group
    available = SECTION_GROUPS.get(section, [])
    if not available:
        return prompt("分组", "general")
    default_group = available[0][0]
    choices = ", ".join(f"{key}({label})" for key, label in available)
    return prompt(f"分组（{choices}）", default_group)


def build_front_matter(
    *,
    title: str,
    subtitle: str,
    summary: str,
    section: str,
    group: str,
    tags: list[str],
    single_card: bool,
) -> str:
    tag_str = ",".join(tags)
    lines = [
        "---",
        f"title: {title}",
        f"subtitle: {subtitle}",
        f"section: {section}",
        f"section_label: {SECTION_LABELS[section]}",
        f"group: {group}",
    ]
    if single_card:
        lines.append("single_card: true")
    lines.extend(
        [
            f"summary: {summary}",
            f"tags: [{tag_str}]",
            "---",
            "",
        ]
    )
    return "\n".join(lines)


def create_article(
    *,
    section: str,
    group: str,
    title: str,
    subtitle: str,
    summary: str,
    tags: list[str],
    template: str,
    slug: str | None,
    date_str: str | None,
    build_after: bool,
) -> Path:
    section_dir = CONTENT_KNOWLEDGE / section
    section_dir.mkdir(parents=True, exist_ok=True)

    date_prefix = date_str or datetime.now().strftime("%Y-%m-%d")
    resolved_slug = slugify(slug or title)
    if not resolved_slug:
        resolved_slug = datetime.now().strftime("article-%H%M%S")

    filename = f"{date_prefix}-{resolved_slug}.md"
    target = section_dir / filename
    if target.exists():
        raise FileExistsError(f"文件已存在：{target}")

    single_card = template == "single-card"
    content = build_front_matter(
        title=title,
        subtitle=subtitle,
        summary=summary,
        section=section,
        group=group,
        tags=tags,
        single_card=single_card,
    ) + TEMPLATES[template]

    target.write_text(content, encoding="utf-8")

    if build_after:
        subprocess.run(["python3", "scripts/build_static_site.py"], check=True)

    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="创建新文章脚手架")
    parser.add_argument("--section", choices=sorted(SECTION_LABELS), help="模块目录")
    parser.add_argument("--group", help="分组 key")
    parser.add_argument("--title", help="文章标题")
    parser.add_argument("--subtitle", help="副标题")
    parser.add_argument("--summary", help="摘要")
    parser.add_argument("--tags", help="逗号分隔标签")
    parser.add_argument(
        "--template",
        choices=sorted(TEMPLATES),
        default="single-card",
        help="single-card 为单卡片文章，paper-series 为论文整理模板",
    )
    parser.add_argument("--slug", help="文件名 slug，默认从标题生成")
    parser.add_argument("--date", help="日期前缀，格式 YYYY-MM-DD，默认今天")
    parser.add_argument("--build", action="store_true", help="创建后立即重建静态站")
    args = parser.parse_args()

    section = choose_section(args.section)
    if section not in SECTION_LABELS:
        raise SystemExit(f"不支持的模块：{section}")

    group = choose_group(section, args.group)
    title = args.title or prompt("标题")
    subtitle = args.subtitle or prompt("副标题", "")
    summary = args.summary or prompt("摘要", "")
    tags = parse_tags(args.tags) if args.tags is not None else parse_tags(prompt("标签（逗号分隔）", ""))

    target = create_article(
        section=section,
        group=group,
        title=title,
        subtitle=subtitle,
        summary=summary,
        tags=tags,
        template=args.template,
        slug=args.slug,
        date_str=args.date,
        build_after=args.build,
    )
    print(target)


if __name__ == "__main__":
    main()
