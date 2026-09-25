"""Encrypted education modules. Plaintext and passwords never enter public output."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
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
    payloads, updates = {}, {}
    for key, module in MODULES.items():
        target = root / "assets" / "data" / f"education-{key}.json"
        existing = json.loads(target.read_text()) if target.exists() else None
        password = os.environ.get(module["password_env"])
        sources = sorted((root / ".private" / "education" / key).glob("*.md"))
        if sources:
            cards = []
            for source in sources:
                meta, body = parse_front_matter(source.read_text(encoding="utf-8"))
                fragment, _ = markdown_to_html(body, source.parent)
                cards.append(f'<article class="prose education-lesson"><h2>{html.escape(str(meta.get("title", source.stem)))}</h2>{fragment}</article>')
            content = "\n".join(cards).encode()
        elif existing:
            # A clean checkout has ciphertext only. Password rotation can decrypt it.
            if not password:
                payloads[key] = existing["payload"]
                continue
            try:
                content = decrypt(existing["payload"], password, key)
            except Exception as exc:
                raise ValueError(f"{module['title']}：更换密码前请恢复本地 Markdown 源文件。") from exc
        else:
            content = f'<div class="empty-state"><p>{module["title"]}内容正在整理中，敬请期待。</p></div>'.encode()
        digest = hashlib.sha256(content).hexdigest()
        if existing and existing["content_sha256"] == digest:
            if not password:
                payloads[key] = existing["payload"]
                continue
            try:
                if decrypt(existing["payload"], password, key) == content:
                    payloads[key] = existing["payload"]
                    continue
            except Exception:
                pass
        if not password:
            raise ValueError(f"{module['title']}：请运行 python3 scripts/set_education_passwords.py 设置密码并构建。")
        payloads[key] = encrypt(content, password, key)
        updates[target] = {"content_sha256": digest, "payload": payloads[key]}
    # Only write after both modules have passed validation.
    for target, data in updates.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    return payloads


def render_education() -> str:
    cards = []
    for key, module in MODULES.items():
        cards.append(f'''
        <a class="education-card" href="/knowledge/ai-tools/{key}/">
          <div class="education-card__top"><span>{module['number']}</span><span class="education-badge">密码访问</span></div>
          <p class="eyebrow">{module['eyebrow']}</p>
          <h2>{module['title']}</h2><p>{module['description']}</p>
          <span class="education-card__link">进入学习 <span aria-hidden="true">↗</span></span>
        </a>''')
    return f'''
    <section class="site-shell page-hero education-hero">
      <p class="eyebrow">ORANGE EDUCATION</p><h1>橘子教育</h1>
      <p>从求职准备到 AI 实践，一起把知识变成能力。</p>
    </section>
    <section class="site-shell education-grid" aria-label="学习模块">{''.join(cards)}</section>
    <p class="education-note">两个学习模块分别使用独立的访问密码。</p>'''


def render_locked_module(key: str, payload: dict) -> str:
    module = MODULES[key]
    return f'''
    <section class="site-shell education-module" data-education-module="{key}">
      <a class="education-back" href="/knowledge/ai-tools/">← 返回橘子教育</a>
      <div class="education-module__heading"><h1>{module['title']}</h1><button class="education-lock" type="button" data-lock hidden>锁定模块</button></div>
      <div class="education-gate" data-gate>
        <span class="education-badge">专属学习空间</span>
        <h2>输入密码，开始学习</h2><p>请输入「{module['title']}」的访问密码。</p>
        <form data-unlock-form>
          <label for="module-password">访问密码</label>
          <div class="education-password"><input id="module-password" type="password" autocomplete="current-password" required aria-describedby="unlock-status"><button type="button" data-toggle-password aria-label="显示密码" aria-pressed="false">显示</button></div>
          <button class="education-submit" type="submit">解锁{module['title']}</button>
          <p class="education-status" id="unlock-status" role="status" aria-live="polite"></p>
        </form>
        <noscript><p>请启用 JavaScript 后输入密码解锁。</p></noscript>
      </div>
      <div data-education-content hidden></div>
      <script type="application/json" data-encrypted-payload>{json.dumps(payload, separators=(',', ':'))}</script>
    </section>'''
