(() => {
  "use strict";
  const root = document.querySelector("[data-education-module]");
  if (!root) return;
  const form = root.querySelector("[data-unlock-form]");
  const input = form.querySelector("input");
  const submit = form.querySelector('[type="submit"]');
  const toggle = form.querySelector("[data-toggle-password]");
  const status = root.querySelector("[role=status]");
  const gate = root.querySelector("[data-gate]");
  const content = root.querySelector("[data-education-content]");
  const lock = root.querySelector("[data-lock]");
  const payload = JSON.parse(root.querySelector("[data-encrypted-payload]").textContent);
  const bytes = (value) => Uint8Array.from(atob(value), (char) => char.charCodeAt(0));
  const encoder = new TextEncoder();
  let generation = 0;

  function reset() {
    generation += 1;
    content.replaceChildren();
    content.hidden = true;
    lock.hidden = true;
    gate.hidden = false;
    form.reset();
    input.type = "password";
    toggle.textContent = "显示";
    toggle.setAttribute("aria-label", "显示密码");
    toggle.setAttribute("aria-pressed", "false");
    input.removeAttribute("aria-invalid");
    status.textContent = "";
    submit.disabled = false;
  }
  lock.addEventListener("click", () => { reset(); input.focus(); });
  // Clear unlocked DOM before it can be restored from the back/forward cache.
  window.addEventListener("pagehide", reset);
  toggle.addEventListener("click", () => {
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    toggle.textContent = show ? "隐藏" : "显示";
    toggle.setAttribute("aria-label", show ? "隐藏密码" : "显示密码");
    toggle.setAttribute("aria-pressed", String(show));
  });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submit.disabled) return;
    if (!window.crypto?.subtle) {
      status.textContent = "当前浏览器无法解锁，请使用支持 HTTPS 的新版浏览器。";
      return;
    }
    submit.disabled = true;
    const attempt = generation;
    input.removeAttribute("aria-invalid");
    status.textContent = "正在解锁…";
    try {
      const material = await crypto.subtle.importKey("raw", encoder.encode(input.value), "PBKDF2", false, ["deriveKey"]);
      const key = await crypto.subtle.deriveKey(
        { name: "PBKDF2", salt: bytes(payload.salt), iterations: payload.iterations, hash: "SHA-256" },
        material, { name: "AES-GCM", length: 256 }, false, ["decrypt"]
      );
      const plaintext = await crypto.subtle.decrypt(
        { name: "AES-GCM", iv: bytes(payload.iv), additionalData: encoder.encode(root.dataset.educationModule) },
        key, bytes(payload.ciphertext)
      );
      if (attempt !== generation) return;
      content.innerHTML = new TextDecoder("utf-8", { fatal: true }).decode(plaintext);
      input.value = "";
      gate.hidden = true;
      content.hidden = false;
      lock.hidden = false;
      status.textContent = "";
      lock.focus();
      if (window.MathJax?.typesetPromise) window.MathJax.typesetPromise([content]).catch(() => {});
    } catch (_) {
      status.textContent = "密码不正确，请输入此模块对应的密码。";
      input.setAttribute("aria-invalid", "true");
      input.focus();
      input.select();
    } finally {
      submit.disabled = false;
    }
  });
})();
