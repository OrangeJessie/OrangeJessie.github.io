(() => {
  const container = document.querySelector('#guestbook .giscus');
  const status = document.querySelector('[data-guestbook-status]');
  if (!container || !status) return;

  const origin = 'https://giscus.app';
  const repo = 'OrangeJessie/OrangeJessie.github.io';
  const timeout = window.setTimeout(() => {
    showError();
  }, 20000);

  function showError() {
    window.clearTimeout(timeout);
    status.hidden = false;
    status.textContent = '留言区暂时无法连接，请刷新重试，或通过下方 GitHub 链接留言。';
  }

  window.addEventListener('message', (event) => {
    const frame = container.querySelector('iframe.giscus-frame');
    if (event.origin !== origin || !frame || event.source !== frame.contentWindow) return;
    const message = event.data && event.data.giscus;
    if (!message || typeof message !== 'object') return;
    if (message.error) {
      // A new guestbook has no discussion until its first comment is posted.
      if (!message.error.includes('Discussion not found')) showError();
      return;
    }
    if (message.resizeHeight || Object.hasOwn(message, 'discussion')) {
      window.clearTimeout(timeout);
      status.hidden = true;
    }
  });

  function load() {
    try {
      const script = document.createElement('script');
      script.src = `${origin}/client.js`;
      script.async = true;
      script.crossOrigin = 'anonymous';
      const attributes = {
        repo,
        'repo-id': 'R_kgDOIxIuQg',
        category: 'Announcements',
        'category-id': 'DIC_kwDOIxIuQs4DGAah',
        mapping: 'specific',
        term: '/aboutme/profile/',
        strict: '1',
        'reactions-enabled': '0',
        'emit-metadata': '1',
        'input-position': 'top',
        theme: 'light',
        lang: 'zh-CN',
        loading: 'eager',
      };
      for (const [key, value] of Object.entries(attributes)) {
        script.setAttribute(`data-${key}`, value);
      }
      script.onerror = showError;
      container.appendChild(script);
    } catch {
      showError();
    }
  }

  load();
})();
