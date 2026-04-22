#!/usr/bin/env python3

from __future__ import annotations

import html
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = ROOT / "content"
CONTENT_POSTS = CONTENT_ROOT / "posts"
CONTENT_PAGES = CONTENT_ROOT / "pages"

SITE = {
    "title": "橘子豆的个人博客",
    "author": "橘子豆",
    "description": "记录论文解读、工程实践与职场思考",
    "email": "976448731@qq.com",
    "github": "https://github.com/OrangeJessie",
    "avatar": "/assets/img/beautiful_fighter.png",
}

NAV = [
    ("首页", "/"),
    ("论文解读", "/papers/"),
    ("职场那些事儿", "/career/"),
    ("关于我", "/aboutme/"),
    ("标签", "/tags/"),
]

PANDOC_FROM = "markdown+fenced_code_blocks+pipe_tables+raw_html+auto_identifiers+smart"


@dataclass
class Page:
    title: str
    subtitle: str
    body_html: str
    path: str
    description: str
    active_nav: str | None = None
    extra_head: str = ""
    body_class: str = ""


@dataclass
class MarkdownPage:
    meta: dict[str, object]
    body_html: str


@dataclass
class Post:
    title: str
    subtitle: str
    summary: str
    date: datetime
    tags: list[str]
    section: str
    section_label: str
    url: str
    source_path: Path
    html: str
    toc: str


def parse_front_matter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    header = parts[0][4:]
    body = parts[1]
    data: dict[str, object] = {}
    for raw_line in header.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
        elif value.lower() in {"true", "false"}:
            data[key] = value.lower() == "true"
        else:
            data[key] = value.strip("'\"")
    return data, body


def run_pandoc(markdown_text: str) -> str:
    completed = subprocess.run(
        ["pandoc", f"--from={PANDOC_FROM}", "--to=html5", "--wrap=none"],
        input=markdown_text,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def clean_markdown(markdown_text: str) -> str:
    cleaned = markdown_text.replace("{% toc %}", "")
    cleaned = re.sub(r"\{\{.*?\}\}", "", cleaned, flags=re.S)
    cleaned = re.sub(r"(?<!\n)(\s#{2,6}\s)", r"\n\n\1", cleaned)
    lines = cleaned.strip().splitlines()
    normalized: list[str] = []

    def append_blank_line() -> None:
        if normalized and normalized[-1] != "":
            normalized.append("")

    for line in lines:
        stripped = line.strip()

        if re.match(r"^\d+\.\s", stripped) or stripped.startswith("> "):
            append_blank_line()
            normalized.append(line)
            continue

        if stripped.startswith("```"):
            append_blank_line()
            normalized.append(line)
            continue

        normalized.append(line)

    return "\n".join(normalized).strip() + "\n"


def strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def remove_missing_images(content_html: str, source_dir: Path) -> str:
    pattern = re.compile(r"<img\b[^>]*\bsrc=\"([^\"]+)\"[^>]*>", re.I)

    def replace(match: re.Match[str]) -> str:
        src = html.unescape(match.group(1))
        if src.startswith(("http://", "https://", "/", "data:")):
            return match.group(0)
        if (source_dir / src).exists():
            return match.group(0)
        return ""

    return pattern.sub(replace, content_html)


def wrap_tables(content_html: str) -> str:
    return re.sub(
        r"(<table[\s\S]*?</table>)",
        r'<div class="table-wrap">\1</div>',
        content_html,
        flags=re.I,
    )


def add_heading_ids_and_toc(content_html: str) -> tuple[str, str]:
    headings: list[tuple[int, str, str]] = []
    counter = {"value": 0}
    pattern = re.compile(r"<h([23])([^>]*)>(.*?)</h\1>", re.S | re.I)

    def replace(match: re.Match[str]) -> str:
        level = int(match.group(1))
        attrs = match.group(2)
        inner = match.group(3)
        text = strip_tags(inner)
        if not text:
            return match.group(0)
        existing = re.search(r'\bid=\"([^\"]+)\"', attrs)
        if existing:
            anchor = existing.group(1)
        else:
            counter["value"] += 1
            anchor = f"section-{counter['value']}"
            attrs = f'{attrs} id="{anchor}"'
        headings.append((level, anchor, text))
        return f"<h{level}{attrs}>{inner}</h{level}>"

    updated = pattern.sub(replace, content_html)

    if not headings:
        return updated, ""

    items = []
    for level, anchor, text in headings:
        items.append(
            f'<li class="toc-level-{level}"><a href="#{html.escape(anchor)}">{html.escape(text)}</a></li>'
        )

    toc_html = (
        '<aside class="article-toc">'
        '<div class="article-toc__title">目录</div>'
        f"<ul>{''.join(items)}</ul>"
        "</aside>"
    )
    return updated, toc_html


def markdown_to_html(markdown_text: str, source_dir: Path) -> tuple[str, str]:
    html_fragment = run_pandoc(clean_markdown(markdown_text))
    html_fragment = remove_missing_images(html_fragment, source_dir)
    html_fragment = wrap_tables(html_fragment)
    html_fragment, toc_html = add_heading_ids_and_toc(html_fragment)
    return html_fragment, toc_html


def format_date(date_value: datetime) -> str:
    return date_value.strftime("%Y.%m.%d")


def output_path(relative_path: str) -> Path:
    return ROOT / relative_path.lstrip("/")


def write_text(relative_path: str, content: str) -> None:
    target = output_path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def remove_output(target: Path) -> None:
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()


def clean_generated_outputs(posts: list["Post"]) -> None:
    for relative in ["index.html", "404.html", ".nojekyll", "aboutme", "papers", "career", "tags"]:
        remove_output(ROOT / relative)

    for child in ROOT.iterdir():
        if child.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}-", child.name):
            shutil.rmtree(child)

    for post in posts:
        remove_output(ROOT / post.url.strip("/"))


def page_shell(page: Page) -> str:
    title = html.escape(page.title)
    description = html.escape(page.description)
    nav_html = []
    for label, href in NAV:
        active = ' class="is-active"' if href == page.active_nav else ""
        nav_html.append(f'<a href="{href}"{active}>{html.escape(label)}</a>')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="author" content="{html.escape(SITE['author'])}">
  <link rel="icon" href="{SITE['avatar']}">
  <link rel="stylesheet" href="/assets/css/site.css">
  {page.extra_head}
</head>
<body class="{html.escape(page.body_class)}">
  <header class="site-header">
    <div class="site-shell site-header__inner">
      <a class="site-brand" href="/">{html.escape(SITE['title'])}</a>
      <nav class="site-nav">{''.join(nav_html)}</nav>
    </div>
  </header>

  <main class="site-main">
    {page.body_html}
  </main>

  <footer class="site-footer">
    <div class="site-shell site-footer__inner">
      <div>
        <strong>{html.escape(SITE['author'])}</strong>
        <p>{html.escape(SITE['description'])}</p>
      </div>
      <div class="site-footer__links">
        <a href="mailto:{html.escape(SITE['email'])}">Email</a>
        <a href="{html.escape(SITE['github'])}" target="_blank" rel="noreferrer">GitHub</a>
      </div>
    </div>
  </footer>
</body>
</html>
"""


def render_post_card(post: Post) -> str:
    tags = "".join(f"<span>{html.escape(tag)}</span>" for tag in post.tags)
    return f"""
    <article class="listing-card">
      <div class="listing-card__eyebrow">{html.escape(post.section_label)}</div>
      <h3><a href="{post.url}">{html.escape(post.title)}</a></h3>
      <p>{html.escape(post.summary)}</p>
      <div class="listing-card__meta">
        <time datetime="{post.date.date().isoformat()}">{format_date(post.date)}</time>
        <div class="listing-card__tags">{tags}</div>
      </div>
    </article>
    """


def render_home(posts: list[Post]) -> str:
    papers = [post for post in posts if post.section == "papers"]
    career = [post for post in posts if post.section == "career"]

    def render_preview(items: Iterable[Post]) -> str:
        return "".join(render_post_card(post) for post in list(items)[:3])

    body = f"""
    <section class="site-shell home-hero">
      <div class="home-hero__panel">
        <div class="home-hero__copy">
          <div class="eyebrow">PERSONAL BLOG</div>
          <h1>把论文、工程和职场思考，写成真正能读下去的内容</h1>
          <p class="lead">这里暂时专注两类主题：一类是把复杂论文拆开讲清楚，另一类是把一线工作里的踩坑、复盘和成长，写成更真实的记录。</p>
          <div class="button-row">
            <a class="button button--primary" href="/papers/">进入论文解读</a>
            <a class="button button--secondary" href="/career/">进入职场那些事儿</a>
          </div>
        </div>
        <aside class="home-hero__aside">
          <img class="profile-avatar" src="{SITE['avatar']}" alt="{html.escape(SITE['author'])}">
          <div class="glass-card">
            <strong>{html.escape(SITE['author'])}</strong>
            <p>关注算法、工程实践和表达方式，想把“看懂”和“说清楚”这两件事都做好。</p>
          </div>
          <div class="mini-grid">
            <div class="mini-card">
              <span>论文解读</span>
              <strong>{len(papers)}</strong>
              <p>经典模型、方法拆解、实验脉络。</p>
            </div>
            <div class="mini-card">
              <span>职场那些事儿</span>
              <strong>{len(career)}</strong>
              <p>工程踩坑、工作复盘、成长记录。</p>
            </div>
          </div>
        </aside>
      </div>
    </section>

    <section class="site-shell section-block">
      <div class="section-head">
        <div>
          <div class="eyebrow">CONTENT MAP</div>
          <h2>先把长期会持续写的两类内容打磨出来</h2>
        </div>
      </div>
      <div class="topic-grid">
        <article class="topic-card">
          <div class="topic-card__index">01</div>
          <h3>论文解读</h3>
          <p>不堆术语，重点写清楚问题背景、核心方法、关键实验和我自己的理解。</p>
          <a href="/papers/">查看这个板块</a>
        </article>
        <article class="topic-card">
          <div class="topic-card__index">02</div>
          <h3>职场那些事儿</h3>
          <p>把一线开发、问题排查、协作沟通和成长复盘，沉淀成有温度的职业记录。</p>
          <a href="/career/">查看这个板块</a>
        </article>
      </div>
    </section>

    <section class="site-shell section-block">
      <div class="section-head">
        <div>
          <div class="eyebrow">LATEST IN PAPERS</div>
          <h2>论文解读</h2>
        </div>
        <a class="section-link" href="/papers/">查看全部</a>
      </div>
      <div class="listing-grid">{render_preview(papers)}</div>
    </section>

    <section class="site-shell section-block section-block--last">
      <div class="section-head">
        <div>
          <div class="eyebrow">LATEST AT WORK</div>
          <h2>职场那些事儿</h2>
        </div>
        <a class="section-link" href="/career/">查看全部</a>
      </div>
      <div class="listing-grid">{render_preview(career)}</div>
    </section>
    """
    return page_shell(
        Page(
            title=SITE["title"],
            subtitle="",
            body_html=body,
            path="/",
            description=SITE["description"],
            active_nav="/",
            body_class="page-home",
        )
    )


def render_section(section_key: str, page_meta: dict[str, object], posts: list[Post]) -> str:
    title = str(page_meta.get("title", section_key))
    subtitle = str(page_meta.get("subtitle", ""))
    intro = str(page_meta.get("intro", ""))
    body = f"""
    <section class="site-shell page-hero">
      <div class="eyebrow">SECTION</div>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(subtitle)}</p>
    </section>
    <section class="site-shell section-list">
      <div class="intro-card">
        <p>{html.escape(intro)}</p>
      </div>
      <div class="listing-grid">
        {''.join(render_post_card(post) for post in posts)}
      </div>
    </section>
    """
    return page_shell(
        Page(
            title=f"{title} | {SITE['title']}",
            subtitle=subtitle,
            body_html=body,
            path=f"/{section_key}/",
            description=subtitle,
            active_nav=f"/{section_key}/",
            body_class="page-section",
        )
    )


def render_about(page_meta: dict[str, object], content_html: str) -> str:
    title = str(page_meta.get("title", "关于我"))
    subtitle = str(page_meta.get("subtitle", ""))
    body = f"""
    <section class="site-shell page-hero">
      <div class="eyebrow">ABOUT</div>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(subtitle)}</p>
    </section>
    <section class="site-shell prose-card">
      <article class="prose prose--about">{content_html}</article>
    </section>
    """
    return page_shell(
        Page(
            title=f"{title} | {SITE['title']}",
            subtitle="",
            body_html=body,
            path="/aboutme/",
            description=subtitle or "关于橘子豆的简介",
            active_nav="/aboutme/",
            body_class="page-about",
        )
    )


def render_tags(tag_map: dict[str, list[Post]]) -> str:
    tag_buttons = "".join(
        f'<a class="tag-chip" href="#tag-{html.escape(tag)}">{html.escape(tag)} <span>{len(items)}</span></a>'
        for tag, items in tag_map.items()
    )

    sections = []
    for tag, items in tag_map.items():
        cards = "".join(render_post_card(post) for post in items)
        sections.append(
            f"""
            <section id="tag-{html.escape(tag)}" class="tag-section">
              <div class="section-head">
                <h2>{html.escape(tag)}</h2>
                <span class="tag-count">{len(items)} 篇</span>
              </div>
              <div class="listing-grid">{cards}</div>
            </section>
            """
        )

    body = f"""
    <section class="site-shell page-hero">
      <div class="eyebrow">TAGS</div>
      <h1>标签索引</h1>
      <p>按主题快速浏览已有内容。</p>
    </section>
    <section class="site-shell tags-page">
      <div class="tag-cloud">{tag_buttons}</div>
      {''.join(sections)}
    </section>
    """
    return page_shell(
        Page(
            title=f"标签 | {SITE['title']}",
            subtitle="",
            body_html=body,
            path="/tags/",
            description="博客标签索引",
            active_nav="/tags/",
            body_class="page-tags",
        )
    )


def render_post(post: Post, previous_post: Post | None, next_post: Post | None) -> str:
    tag_html = "".join(f"<a href='/tags/#tag-{html.escape(tag)}'>{html.escape(tag)}</a>" for tag in post.tags)

    nav_cards = []
    if previous_post:
        nav_cards.append(
            f"""
            <a class="post-nav-card" href="{previous_post.url}">
              <span>上一篇</span>
              <strong>{html.escape(previous_post.title)}</strong>
            </a>
            """
        )
    if next_post:
        nav_cards.append(
            f"""
            <a class="post-nav-card" href="{next_post.url}">
              <span>下一篇</span>
              <strong>{html.escape(next_post.title)}</strong>
            </a>
            """
        )

    body = f"""
    <section class="site-shell report-hero">
      <div class="eyebrow">{html.escape(post.section_label)}</div>
      <h1>{html.escape(post.title)}</h1>
      <p class="report-hero__subtitle">{html.escape(post.subtitle)}</p>
      <div class="report-meta">
        <span>{format_date(post.date)}</span>
        <span>{len(post.tags)} 个标签</span>
      </div>
      <div class="report-tags">{tag_html}</div>
    </section>
    <section class="site-shell report-layout">
      {post.toc}
      <article class="report-article prose">{post.html}</article>
    </section>
    <section class="site-shell post-nav-grid">
      {''.join(nav_cards)}
    </section>
    """
    return page_shell(
        Page(
            title=f"{post.title} | {SITE['title']}",
            subtitle=post.subtitle,
            body_html=body,
            path=post.url,
            description=post.summary or post.subtitle,
            body_class="page-post",
        )
    )


def render_404() -> str:
    body = """
    <section class="site-shell page-hero page-hero--compact">
      <div class="eyebrow">404</div>
      <h1>页面不存在</h1>
      <p>这个地址现在没有内容，回首页继续看。</p>
      <div class="button-row button-row--center">
        <a class="button button--primary" href="/">回到首页</a>
      </div>
    </section>
    """
    return page_shell(
        Page(
            title=f"404 | {SITE['title']}",
            subtitle="",
            body_html=body,
            path="/404.html",
            description="页面不存在",
            body_class="page-404",
        )
    )


def load_posts() -> list[Post]:
    posts: list[Post] = []
    for path in sorted(CONTENT_POSTS.glob("*.md")):
        raw_text = path.read_text(encoding="utf-8")
        meta, markdown_body = parse_front_matter(raw_text)
        date_part = path.stem[:10]
        date_value = datetime.strptime(date_part, "%Y-%m-%d")
        html_fragment, toc_html = markdown_to_html(markdown_body, path.parent)
        posts.append(
            Post(
                title=str(meta.get("title", path.stem)),
                subtitle=str(meta.get("subtitle", "")),
                summary=str(meta.get("summary", "")),
                date=date_value,
                tags=list(meta.get("tags", [])),
                section=str(meta.get("section", "")),
                section_label=str(meta.get("section_label", meta.get("section", ""))),
                url=f"/{path.stem}/",
                source_path=path,
                html=html_fragment,
                toc=toc_html,
            )
        )
    posts.sort(key=lambda item: (item.date, item.title), reverse=True)
    return posts


def load_markdown_page(source_file: str) -> MarkdownPage:
    page_path = CONTENT_PAGES / source_file
    raw_text = page_path.read_text(encoding="utf-8")
    meta, markdown_body = parse_front_matter(raw_text)
    html_fragment, _ = markdown_to_html(markdown_body, page_path.parent)
    return MarkdownPage(meta=meta, body_html=html_fragment)


def build() -> None:
    posts = load_posts()
    clean_generated_outputs(posts)
    about_page = load_markdown_page("about.md")
    papers_page = load_markdown_page("papers.md")
    career_page = load_markdown_page("career.md")

    tag_map: dict[str, list[Post]] = {}
    for post in posts:
        for tag in post.tags:
            tag_map.setdefault(tag, []).append(post)

    ordered_tags = {tag: tag_map[tag] for tag in sorted(tag_map)}

    write_text("index.html", render_home(posts))
    write_text("aboutme/index.html", render_about(about_page.meta, about_page.body_html))
    write_text(
        "papers/index.html",
        render_section("papers", papers_page.meta, [p for p in posts if p.section == "papers"]),
    )
    write_text(
        "career/index.html",
        render_section("career", career_page.meta, [p for p in posts if p.section == "career"]),
    )
    write_text("tags/index.html", render_tags(ordered_tags))
    write_text("404.html", render_404())

    for idx, post in enumerate(posts):
        previous_post = posts[idx + 1] if idx + 1 < len(posts) else None
        next_post = posts[idx - 1] if idx - 1 >= 0 else None
        write_text(f"{post.url.strip('/')}/index.html", render_post(post, previous_post, next_post))

    write_text(".nojekyll", "")


if __name__ == "__main__":
    build()
