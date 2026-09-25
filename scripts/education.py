"""Encrypted education modules. Plaintext and passwords never enter public output."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
from pathlib import Path

MODULES = {
    "interview-coaching": {
        "title": "面试辅导", "eyebrow": "CAREER & INTERVIEW", "number": "01",
        "description": "梳理知识体系，打磨项目表达，从容走进下一场面试。",
        "password_env": "EDUCATION_INTERVIEW_PASSWORD",
    },
    "ai-tutorials": {
        "title": "AI教程", "eyebrow": "LEARN & BUILD WITH AI", "number": "02",
        "description": "从工具使用到工作流实践，把 AI 融入真实的学习与工作。",
        "password_env": "EDUCATION_AI_PASSWORD",
    },
}
ITERATIONS = 600_000


def encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def decrypt(payload: dict, password: str, module: str) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(payload["salt"]), payload["iterations"], 32)
    return AESGCM(key).decrypt(base64.b64decode(payload["iv"]), base64.b64decode(payload["ciphertext"]), module.encode())


def encrypt(content: bytes, password: str, module: str) -> dict:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, iv = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS, 32)
    return {
        "version": 1, "module": module, "iterations": ITERATIONS,
        "salt": encode(salt), "iv": encode(iv),
        "ciphertext": encode(AESGCM(key).encrypt(iv, content, module.encode())),
    }


def prepare_payloads(root: Path, markdown_to_html, parse_front_matter) -> dict:
    """Publish article titles and ciphertext; private Markdown never leaves the machine."""
    manifests, updates = {}, {}
    for key, module in MODULES.items():
        target = root / "assets" / "data" / f"education-{key}.json"
        existing = json.loads(target.read_text()) if target.exists() else None
        source_dir = root / ".private" / "education" / key
        password = os.environ.get(module["password_env"])
        if not source_dir.exists():
            if existing and existing.get("version") != 2:
                raise ValueError(f"{module['title']}：请恢复本地文章源文件后迁移旧模块密文。")
            manifests[key] = existing or {"version": 2, "articles": []}
            continue
        previous = {article["slug"]: article for article in (existing or {}).get("articles", [])}
        articles = []
        for source in sorted(source_dir.glob("*.md"), reverse=True):
            meta, body = parse_front_matter(source.read_text(encoding="utf-8"))
            if meta.get("draft") is True:
                continue
            slug = source.stem
            if not re.fullmatch(r"[\w-]+", slug):
                raise ValueError(f"文章文件名只支持文字、数字、下划线和连字符：{source.name}")
            title = str(meta.get("title", slug))
            fragment, _ = markdown_to_html(body, source.parent)
            content = f'<article class="prose education-lesson">{fragment}</article>'.encode()
            digest = hashlib.sha256(content).hexdigest()
            scope = f"{key}/{slug}"
            cached = previous.get(slug)
            reusable = cached and cached["content_sha256"] == digest
            if reusable and password:
                try:
                    reusable = decrypt(cached["payload"], password, scope) == content
                except Exception:
                    reusable = False
            if reusable:
                payload = cached["payload"]
            else:
                if not password:
                    raise ValueError(f"{module['title']}：文章变化，请设置对应密码后重新构建。")
                payload = encrypt(content, password, scope)
            articles.append({"slug": slug, "title": title, "content_sha256": digest, "payload": payload})
        manifests[key] = {"version": 2, "articles": articles}
        updates[target] = manifests[key]
    # Validate all modules before replacing any published manifests.
    for target, data in updates.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    return manifests


def render_education() -> str:
    cards = []
    for key, module in MODULES.items():
        cards.append(f'''
        <a class="education-card" href="/knowledge/ai-tools/{key}/">
          <div class="education-card__top"><span>{module['number']}</span><span class="education-badge">学习模块</span></div>
          <p class="eyebrow">{module['eyebrow']}</p>
          <h2>{module['title']}</h2><p>{module['description']}</p>
          <span class="education-card__link">进入学习 <span aria-hidden="true">↗</span></span>
        </a>''')
    return f'''
    <section class="site-shell page-hero education-hero">
      <p class="eyebrow">ORANGE EDUCATION</p><h1>橘子教育</h1>
    </section>
    <section class="site-shell education-grid" aria-label="学习模块">{''.join(cards)}</section>
'''


def render_history() -> str:
    return """
    <details class="education-history">
      <summary><h2>历史咨询</h2><span class="history-expand">展开 <span aria-hidden="true">＋</span></span><span class="history-collapse">收起 <span aria-hidden="true">−</span></span></summary>
      <div class="education-history__gallery">
        <figure><a href="/assets/img/education/consultation-feedback.png" target="_blank" rel="noopener"><img src="/assets/img/education/consultation-feedback.png" alt="历史咨询的聊天反馈" width="852" height="1076" loading="lazy"></a><figcaption>咨询反馈</figcaption></figure>
        <figure><a href="/assets/img/education/mentor-certificate.jpg" target="_blank" rel="noopener"><img src="/assets/img/education/mentor-certificate.jpg" alt="2026 她行春季项目导师参与证书" width="1170" height="1667" loading="lazy"></a><figcaption>导师参与证书</figcaption></figure>
      </div>
    </details>
    """


def render_module(key: str, manifest: dict) -> str:
    module = MODULES[key]
    articles = "".join(
        f'<a class="education-article-link" href="/knowledge/ai-tools/{key}/{html.escape(article["slug"])}/"><span>{html.escape(article["title"])}</span><span class="education-badge">密码阅读 ↗</span></a>'
        for article in manifest["articles"]
    ) or '<div class="empty-state"><p>文章正在整理中，敬请期待。</p></div>'
    return f'''
    <section class="site-shell education-module">
      <a class="education-back" href="/knowledge/ai-tools/">← 返回橘子教育</a>
      <div class="education-module__heading"><h1>{module['title']}</h1></div>
      {render_history() if key == "interview-coaching" else ""}
      <section class="education-articles" aria-label="文章列表"><h2>文章</h2>{articles}</section>
    </section>'''


def render_locked_article(key: str, article: dict) -> str:
    module = MODULES[key]
    title = html.escape(article["title"])
    scope = html.escape(f"{key}/{article['slug']}")
    return f'''
    <section class="site-shell education-module" data-education-article="{scope}">
      <a class="education-back" href="/knowledge/ai-tools/{key}/">← 返回{module['title']}</a>
      <div class="education-module__heading"><h1>{title}</h1><button class="education-lock" type="button" data-lock hidden>锁定文章</button></div>
      <div class="education-gate" data-gate>
        <span class="education-badge">密码阅读</span>
        <h2>输入密码，阅读文章</h2><p>请输入「{module['title']}」文章的访问密码。</p>
        <form data-unlock-form>
          <label for="article-password">访问密码</label>
          <div class="education-password"><input id="article-password" type="password" autocomplete="current-password" required aria-describedby="unlock-status"><button type="button" data-toggle-password aria-label="显示密码" aria-pressed="false">显示</button></div>
          <button class="education-submit" type="submit">解锁文章</button>
          <p class="education-status" id="unlock-status" role="status" aria-live="polite"></p>
        </form>
        <noscript><p>请启用 JavaScript 后输入密码解锁。</p></noscript>
      </div>
      <div data-education-content hidden></div>
      <script type="application/json" data-encrypted-payload>{json.dumps(article['payload'], separators=(',', ':'))}</script>
    </section>'''
