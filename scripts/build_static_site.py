#!/usr/bin/env python3

from __future__ import annotations

import html
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = ROOT / "content"
CONTENT_KNOWLEDGE = CONTENT_ROOT / "knowledge"
CONTENT_PAGES = CONTENT_ROOT / "pages"
KNOWLEDGE_BASE_URL = "/knowledge"

SITE = {
    "title": "橘子豆的AI工坊",
    "author": "橘子豆",
    "description": "已识乾坤大，犹怜草木青",
    "email": "976448731@qq.com",
    "github": "https://github.com/OrangeJessie",
    "avatar": "/assets/img/beautiful_fighter.png",
}

PAPER_SOURCES: dict[str, dict[str, str]] = {
    "Learning Deep Structured Semantic Models for Web Search using Clickthrough Data": {
        "source_name": "Microsoft Research",
        "source_url": "https://www.microsoft.com/en-us/research/publication/learning-deep-structured-semantic-models-for-web-search-using-clickthrough-data/",
        "excerpt": "It uses a DNN to map high-dimensional sparse text features into low-dimensional dense features in a semantic space.",
    },
    "Deep Neural Networks for YouTube Recommendations": {
        "source_name": "Google Research",
        "source_url": "https://research.google/pubs/pub45530/",
        "excerpt": "Deep candidate generation model architecture showing embedded sparse features concatenated with dense features.",
    },
    "Sampling-bias-corrected neural modeling for large corpus item recommendations": {
        "source_name": "Google Research",
        "source_url": "https://research.google/pubs/sampling-bias-corrected-neural-modeling-for-large-corpus-item-recommendations/",
    },
    "Embedding-based Retrieval in Facebook Search": {
        "source_name": "KDD 2020",
        "source_url": "https://www.kdd.org/kdd2020/accepted-papers/view/embedding-based-retrieval-in-facebook-search.html",
        "excerpt": "Besides the query text, it is important to take into account the searcher’s context to provide relevant results.",
    },
    "MOBIUS: Towards the Next Generation of Query-Ad Matching in Baidu’s Sponsored Search": {
        "source_name": "KDD 2019",
        "source_url": "https://www.kdd.org/kdd2019/accepted-papers/view/mobius-towards-the-next-generation-of-query-ad-matching-in-baidus-sponsored",
    },
    "Deep Match to Rank Model for Personalized Click-Through Rate Prediction": {
        "source_name": "AAAI 2020",
        "source_url": "https://doi.org/10.1609/aaai.v34i01.5346",
        "excerpt": "Existing works in the field of CTR prediction mainly focus on user representation and pay less attention on representing the relevance between user and item.",
    },
    "Deep Retrieval: Learning A Retrievable Structure for Large-Scale Recommendations": {
        "source_name": "arXiv",
        "source_url": "https://arxiv.org/abs/2007.07203",
        "excerpt": "We present Deep Retrieval (DR), to learn a retrievable structure directly with user-item interaction data.",
    },
    "Multi-Interest Network with Dynamic Routing for Recommendation at Tmall": {
        "source_name": "CIKM 2019",
        "source_url": "https://researchportal.hkust.edu.hk/en/publications/multi-interest-network-with-dynamic-routing-for-recommendation-at-2",
        "excerpt": "We approach the learning of user representations from a different view, by representing a user with multiple representation vectors.",
    },
    "Controllable Multi-Interest Framework for Recommendation": {
        "source_name": "arXiv",
        "source_url": "https://arxiv.org/abs/2005.09347",
        "excerpt": "Our multi-interest module captures multiple interests from user behavior sequences.",
    },
    "Sparse-Interest Network for Sequential Recommendation": {
        "source_name": "WSDM 2021",
        "source_url": "https://doi.org/10.1145/3437963.3441811",
    },
    "Octopus: Comprehensive and Elastic User Representation for the Generation of Recommendation Candidates": {
        "source_name": "Microsoft Research",
        "source_url": "https://www.microsoft.com/en-us/research/?p=683799",
        "excerpt": "Octopus also generates multiple vectors for the comprehensive representation of user’s diverse interests.",
    },
    "Rethinking Multi-Interest Learning for Candidate Matching in Recommender Systems": {
        "source_name": "RecSys 2023",
        "source_url": "https://researchportal.hkust.edu.hk/en/publications/rethinking-multi-interest-learning-for-candidate-matching-in-reco-2",
        "excerpt": "This work revisits the training framework and uncovers two major problems hindering the expressiveness of learned multi-interest representations.",
    },
    "PinnerSage: Multi-Modal User Embedding Framework for Recommendations at Pinterest": {
        "source_name": "KDD 2020",
        "source_url": "https://www.kdd.org/kdd2020/accepted-papers/view/pinnersage-multi-modal-user-embedding-framework-for-recommendations-at-pint.html",
        "excerpt": "Most prior work infers a single high dimensional embedding to represent a user.",
    },
    "A Dual Augmented Two-tower Model for Online Large-scale Recommendation": {
        "source_name": "DLP-KDD 2021",
        "source_url": "https://dlp-kdd.github.io/assets/pdf/DLP-KDD_2021_paper_4.pdf",
        "excerpt": "The model suffers from lack of information interaction between the two towers.",
    },
    "Mixed Negative Sampling for Learning Two-tower Neural Networks in Recommendations": {
        "source_name": "Google Research",
        "source_url": "https://research.google/pubs/mixed-negative-sampling-for-learning-two-tower-neural-networks-in-recommendations/",
        "excerpt": "MNS uses a mixture of batch and uniformly sampled negatives to tackle the selection bias of implicit user feedback.",
    },
    "Decoupled Contrastive Learning": {
        "source_name": "OpenReview",
        "source_url": "https://openreview.net/forum?id=sxpUavxXE0v",
        "excerpt": "We identify a noticeable negative-positive-coupling (NPC) effect in the widely used cross-entropy loss.",
    },
    "ProtoNCE": {
        "source_name": "OpenReview",
        "source_url": "https://openreview.net/forum?id=KmykpuSrjcq",
        "paper_title": "Prototypical Contrastive Learning of Unsupervised Representations",
        "excerpt": "PCL bridges contrastive learning with clustering and proposes ProtoNCE loss.",
    },
    "Debiased Contrastive Learning": {
        "source_name": "arXiv",
        "source_url": "https://arxiv.org/abs/2007.00224",
        "excerpt": "Without access to labels, dissimilar points are typically taken to be randomly sampled datapoints.",
    },
    "Contrastive Learning with Hard Negative Samples": {
        "source_name": "OpenReview",
        "source_url": "https://openreview.net/forum?id=CR1XOQ0UTh-",
        "excerpt": "Learning contrastive representations benefits from hard negative samples.",
    },
    "Understanding Dimensional Collapse in Contrastive Self-supervised Learning": {
        "source_name": "OpenReview",
        "source_url": "https://openreview.net/forum?id=YevsQ05DEN7",
        "excerpt": "Here, we show that dimensional collapse also happens in contrastive learning.",
    },
    "Learning Tree-based Deep Model for Recommender Systems": {
        "source_name": "KDD 2018",
        "source_url": "https://www.kdd.org/kdd2018/accepted-papers/view/learning-tree-based-deep-model-for-recommender-systems",
        "excerpt": "We propose a novel tree-based method which can provide logarithmic complexity w.r.t. corpus size.",
    },
    "Recommender Forest for Efficient Retrieval": {
        "source_name": "NeurIPS 2022",
        "source_url": "https://papers.nips.cc/paper_files/paper/2022/hash/fe2fe749d329627f161484876630c689-Abstract-Conference.html",
        "excerpt": "We propose the Recommender Forest (a.k.a., RecForest), which jointly learns latent embedding and index.",
    },
}

NAV = [
    ("首页", "/"),
    ("关于我", "/aboutme/"),
    ("Contact", "/contact/"),
]

SECTION_ORDER = ["papers", "ai-tools", "experience", "game-space"]

PANDOC_FROM = "markdown+fenced_code_blocks+pipe_tables+raw_html+auto_identifiers+smart+autolink_bare_uris"


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


def section_url(section_key: str) -> str:
    return f"{KNOWLEDGE_BASE_URL}/{section_key}/"


def tags_url() -> str:
    return f"{KNOWLEDGE_BASE_URL}/tags/"


def post_url(section_key: str, slug: str) -> str:
    return f"{KNOWLEDGE_BASE_URL}/{section_key}/{slug}/"


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
    cleaned = markdown_text.replace("\f", "\n")
    cleaned = cleaned.replace("{% toc %}", "")
    cleaned = re.sub(r"\{\{.*?\}\}", "", cleaned, flags=re.S)
    url_chunk = r"[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]"
    url_continuation = r"[A-Za-z0-9][A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]*"
    wrapped_url_pattern = re.compile(rf"https?://{url_chunk}+(?:\s*\n\s*(?!https?://){url_continuation})+")
    cleaned = wrapped_url_pattern.sub(lambda match: re.sub(r"\s+", "", match.group(0)), cleaned)
    bare_url_pattern = re.compile(rf"(?<![<\\(\\[\"'=])(?P<url>https?://{url_chunk}+)")
    cleaned = bare_url_pattern.sub(lambda match: f"<{match.group('url')}>", cleaned)
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


def render_citation_note(title: str, meta: dict[str, str]) -> str:
    display_title = meta.get("paper_title", title)
    excerpt = meta.get("excerpt", "").strip()
    excerpt_html = (
        f'<p class="citation-note__excerpt">"{html.escape(excerpt)}"</p>'
        if excerpt
        else ""
    )
    return (
        '<div class="citation-row">'
        '<details class="citation-note">'
        '<summary>论文链接</summary>'
        '<div class="citation-note__card">'
        f'<div class="citation-note__source">{html.escape(meta["source_name"])}</div>'
        f'<p class="citation-note__title">{html.escape(display_title)}</p>'
        f"{excerpt_html}"
        f'<a href="{html.escape(meta["source_url"])}" target="_blank" rel="noreferrer">打开论文原文</a>'
        "</div>"
        "</details>"
        "</div>"
    )


def inject_paper_citations(content_html: str) -> str:
    updated = content_html
    for title, meta in PAPER_SOURCES.items():
        title_html = html.escape(title)
        pattern = re.compile(
            rf"(<blockquote>\s*<p>{re.escape(title_html)}</p>\s*</blockquote>)",
            re.S,
        )
        updated = pattern.sub(
            lambda match: match.group(1) + render_citation_note(title, meta),
            updated,
            count=1,
        )
    return updated


def wrap_paper_cards(content_html: str) -> str:
    h2_sections = re.split(r"(?=<h2\b)", content_html)
    if len(h2_sections) < 3 or "论文对比" not in content_html:
        return content_html

    leading = h2_sections[0]
    wrapped: list[str] = []
    for chunk in h2_sections[1:]:
        heading_match = re.search(r"<h2\b[^>]*>(.*?)</h2>", chunk, re.S | re.I)
        if not heading_match:
            wrapped.append(chunk)
            continue
        heading_text = strip_tags(heading_match.group(1))
        card_class = "article-overview-card" if heading_text == "论文对比" else "paper-card"
        wrapped.append(f'<section class="{card_class}">{chunk}</section>')
    return leading + "".join(wrapped)


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
        if level != 2 or text == "论文对比":
            continue
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
    html_fragment = inject_paper_citations(html_fragment)
    html_fragment = wrap_paper_cards(html_fragment)
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
    for relative in [
        "index.html",
        "404.html",
        ".nojekyll",
        "knowledge",
        "aboutme",
        "contact",
        "papers",
        "ai-tools",
        "experience",
        "game-space",
        "career",
        "tags",
    ]:
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
        <p>{html.escape(SITE['description'])}</p>
      </div>
      <div class="site-footer__links">
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


def render_home(section_pages: dict[str, MarkdownPage], posts: list[Post]) -> str:
    cards = []
    for index, section_key in enumerate(SECTION_ORDER, start=1):
        meta = section_pages[section_key].meta
        intro = str(meta.get("intro", meta.get("subtitle", ""))).strip()
        cards.append(
            f"""
            <a class="topic-card topic-card--link" href="{section_url(section_key)}">
              <div class="topic-card__index">{index:02d}</div>
              <div class="topic-card__body">
                <div class="topic-card__heading">
                  <h3>{html.escape(str(meta.get("title", section_key)))}</h3>
                  <span class="topic-card__arrow" aria-hidden="true">↗</span>
                </div>
                <p>{html.escape(intro)}</p>
              </div>
            </a>
            """
        )

    body = f"""
    <section class="site-shell home-hero">
      <div class="home-hero__panel">
        <div class="home-profile">
          <img class="profile-avatar" src="{SITE['avatar']}" alt="{html.escape(SITE['author'])}">
          <div class="home-profile__body">
            <h1>{html.escape(SITE['author'])}</h1>
            <p>沪漂算法女工，搜广推+ai search</p>
            <p>论文 | 职场 | 项目 | 有关ai的想法以及其他</p>
            <p>文明 | 饥荒缺氧泰拉瑞亚 | 星露谷农夫 | LOL金铲铲 等游戏六级爱好者</p>
          </div>
        </div>
      </div>
    </section>

    <section class="site-shell section-block">
      <div class="topic-grid">{''.join(cards)}</div>
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
    empty_text = str(page_meta.get("empty_text", "这个板块正在整理中，很快会补充内容。"))
    listing_html = "".join(render_post_card(post) for post in posts)
    if not listing_html:
        listing_html = f'<div class="empty-state"><p>{html.escape(empty_text)}</p></div>'
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
        {listing_html}
      </div>
    </section>
    """
    return page_shell(
        Page(
            title=f"{title} | {SITE['title']}",
            subtitle=subtitle,
            body_html=body,
            path=section_url(section_key),
            description=subtitle,
            active_nav=section_url(section_key),
            body_class="page-section",
        )
    )


def render_prose_page(
    page_meta: dict[str, object],
    content_html: str,
    *,
    path: str,
    active_nav: str,
    body_class: str,
    eyebrow: str,
) -> str:
    title = str(page_meta.get("title", "页面"))
    subtitle = str(page_meta.get("subtitle", ""))
    body = f"""
    <section class="site-shell page-hero">
      <div class="eyebrow">{html.escape(eyebrow)}</div>
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
            path=path,
            description=subtitle or "关于橘子豆的简介",
            active_nav=active_nav,
            body_class=body_class,
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
            path=tags_url(),
            description="博客标签索引",
            active_nav=tags_url(),
            body_class="page-tags",
        )
    )


def render_post(post: Post, previous_post: Post | None, next_post: Post | None) -> str:
    tag_html = "".join(f"<a href='{tags_url()}#tag-{html.escape(tag)}'>{html.escape(tag)}</a>" for tag in post.tags)

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
    for path in sorted(CONTENT_KNOWLEDGE.glob("*/*.md")):
        raw_text = path.read_text(encoding="utf-8")
        meta, markdown_body = parse_front_matter(raw_text)
        section_key = path.parent.relative_to(CONTENT_KNOWLEDGE).parts[0]
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
                section=section_key,
                section_label=str(meta.get("section_label", section_key)),
                url=post_url(section_key, path.stem),
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
    contact_page = load_markdown_page("contact.md")
    papers_page = load_markdown_page("papers.md")
    ai_tools_page = load_markdown_page("ai-tools.md")
    experience_page = load_markdown_page("experience.md")
    game_space_page = load_markdown_page("game-space.md")
    section_pages = {
        "papers": papers_page,
        "ai-tools": ai_tools_page,
        "experience": experience_page,
        "game-space": game_space_page,
    }

    tag_map: dict[str, list[Post]] = {}
    for post in posts:
        for tag in post.tags:
            tag_map.setdefault(tag, []).append(post)

    ordered_tags = {tag: tag_map[tag] for tag in sorted(tag_map)}

    write_text("index.html", render_home(section_pages, posts))
    write_text(
        "aboutme/index.html",
        render_prose_page(
            about_page.meta,
            about_page.body_html,
            path="/aboutme/",
            active_nav="/aboutme/",
            body_class="page-about",
            eyebrow="ABOUT",
        ),
    )
    write_text(
        "contact/index.html",
        render_prose_page(
            contact_page.meta,
            contact_page.body_html,
            path="/contact/",
            active_nav="/contact/",
            body_class="page-contact",
            eyebrow="CONTACT",
        ),
    )
    write_text(
        "knowledge/papers/index.html",
        render_section("papers", papers_page.meta, [p for p in posts if p.section == "papers"]),
    )
    write_text(
        "knowledge/ai-tools/index.html",
        render_section("ai-tools", ai_tools_page.meta, [p for p in posts if p.section == "ai-tools"]),
    )
    write_text(
        "knowledge/experience/index.html",
        render_section("experience", experience_page.meta, [p for p in posts if p.section == "experience"]),
    )
    write_text(
        "knowledge/game-space/index.html",
        render_section("game-space", game_space_page.meta, [p for p in posts if p.section == "game-space"]),
    )
    write_text("knowledge/tags/index.html", render_tags(ordered_tags))
    write_text("404.html", render_404())

    for idx, post in enumerate(posts):
        previous_post = posts[idx + 1] if idx + 1 < len(posts) else None
        next_post = posts[idx - 1] if idx - 1 >= 0 else None
        write_text(f"{post.url.strip('/')}/index.html", render_post(post, previous_post, next_post))

    write_text(".nojekyll", "")


if __name__ == "__main__":
    build()
