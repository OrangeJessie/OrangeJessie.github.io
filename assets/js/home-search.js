(function () {
  const FIELD_WEIGHTS = {
    title: 4.8,
    subtitle: 2.4,
    summary: 2.8,
    tags: 3.2,
    sectionLabel: 1.3,
    content: 1.0,
  };

  const FIELD_NAMES = Object.keys(FIELD_WEIGHTS);
  const K1 = 1.2;
  const B = 0.75;

  function normalizeText(text) {
    return (text || "")
      .toString()
      .normalize("NFKC")
      .toLowerCase()
      .replace(/\s+/g, " ")
      .trim();
  }

  function tokenize(text) {
    const normalized = normalizeText(text);
    if (!normalized) return [];

    const tokens = [];
    const latinTokens = normalized.match(/[a-z0-9]+/g) || [];
    latinTokens.forEach((token) => {
      if (token.length >= 2 || /^\d+$/.test(token)) {
        tokens.push(token);
      }
    });

    const cjkRuns = normalized.match(/[\u3400-\u9fff]+/g) || [];
    cjkRuns.forEach((run) => {
      if (run.length === 1) {
        tokens.push(run);
        return;
      }
      for (let index = 0; index < run.length - 1; index += 1) {
        tokens.push(run.slice(index, index + 2));
      }
      if (run.length <= 4) {
        tokens.push(run);
      }
    });

    return tokens;
  }

  function makeFieldIndex(text) {
    const tokens = tokenize(text);
    const tf = new Map();
    tokens.forEach((token) => {
      tf.set(token, (tf.get(token) || 0) + 1);
    });
    return {
      tokens,
      tf,
      length: Math.max(tokens.length, 1),
    };
  }

  function buildStats(documents) {
    const stats = { totalDocs: documents.length };
    FIELD_NAMES.forEach((field) => {
      let totalLength = 0;
      const df = new Map();

      documents.forEach((doc) => {
        const fieldIndex = doc.index[field];
        totalLength += fieldIndex.length;
        const uniqueTokens = new Set(fieldIndex.tokens);
        uniqueTokens.forEach((token) => {
          df.set(token, (df.get(token) || 0) + 1);
        });
      });

      stats[field] = {
        avgLen: documents.length ? totalLength / documents.length : 1,
        df,
      };
    });
    return stats;
  }

  function bm25(tf, df, docLen, avgLen, totalDocs) {
    if (!tf || !df) return 0;
    const idf = Math.log(1 + (totalDocs - df + 0.5) / (df + 0.5));
    const norm = tf + K1 * (1 - B + B * (docLen / Math.max(avgLen, 1)));
    return idf * ((tf * (K1 + 1)) / norm);
  }

  function buildQuery(query) {
    const normalized = normalizeText(query);
    const tokens = Array.from(new Set(tokenize(query)));
    return { normalized, tokens };
  }

  function scoreDocument(doc, query, stats) {
    let score = 0;

    query.tokens.forEach((token) => {
      FIELD_NAMES.forEach((field) => {
        const fieldIndex = doc.index[field];
        const tf = fieldIndex.tf.get(token) || 0;
        if (!tf) return;
        const fieldStats = stats[field];
        const df = fieldStats.df.get(token) || 0;
        score += FIELD_WEIGHTS[field] * bm25(tf, df, fieldIndex.length, fieldStats.avgLen, stats.totalDocs);
      });
    });

    const phrase = query.normalized;
    if (!phrase) return score;

    if (doc.norm.title.includes(phrase)) score += 8;
    if (doc.norm.title.startsWith(phrase)) score += 2.8;
    if (doc.norm.tags.includes(phrase)) score += 5;
    if (doc.norm.summary.includes(phrase)) score += 3.5;
    if (doc.norm.subtitle.includes(phrase)) score += 2.4;
    if (doc.norm.sectionLabel.includes(phrase)) score += 1.4;
    if (doc.norm.content.includes(phrase)) score += Math.min(3.2, 0.8 + phrase.length * 0.18);

    if (query.tokens.length && query.tokens.every((token) => doc.norm.title.includes(token))) {
      score += 3.2;
    }

    return score;
  }

  function escapeHtml(text) {
    return (text || "")
      .toString()
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function buildSnippet(doc, query) {
    const queryText = query.normalized;
    const preferred = doc.summary || doc.subtitle;
    if (preferred) return preferred;

    const source = doc.content || "";
    if (!source) return "";

    if (!queryText) {
      return source.slice(0, 120);
    }

    const index = normalizeText(source).indexOf(queryText);
    if (index < 0) {
      return source.slice(0, 120);
    }

    const start = Math.max(0, index - 24);
    const end = Math.min(source.length, index + 96);
    const prefix = start > 0 ? "..." : "";
    const suffix = end < source.length ? "..." : "";
    return `${prefix}${source.slice(start, end)}${suffix}`;
  }

  function renderResults(container, documents, query) {
    container.innerHTML = documents
      .map((doc) => {
        const snippet = buildSnippet(doc, query);
        const tags = doc.tags && doc.tags.length ? `<div class="search-result__tags">${escapeHtml(doc.tags.join(" · "))}</div>` : "";
        return `
          <a class="search-result" href="${doc.url}">
            <div class="search-result__meta">
              <span class="search-result__section">${escapeHtml(doc.section_label)}</span>
              <span>${escapeHtml(doc.date)}</span>
            </div>
            <h3>${escapeHtml(doc.title)}</h3>
            <p>${escapeHtml(snippet)}</p>
            ${tags}
          </a>
        `;
      })
      .join("");
  }

  async function init() {
    const root = document.querySelector("[data-home-search]");
    if (!root) return;

    const input = root.querySelector(".home-search__input");
    const status = root.querySelector("[data-search-status]");
    const results = root.querySelector("[data-search-results]");

    let documents = [];
    let stats = null;

    function updateIdleState() {
      status.hidden = true;
      status.textContent = "";
      results.hidden = true;
      results.innerHTML = "";
    }

    function runSearch() {
      const rawQuery = input.value.trim();
      if (!rawQuery) {
        updateIdleState();
        return;
      }

      if (!documents.length || !stats) {
        status.hidden = false;
        status.textContent = "搜索索引还在加载，稍等一下。";
        return;
      }

      const query = buildQuery(rawQuery);
      if (!query.normalized) {
        updateIdleState();
        return;
      }

      const matched = documents
        .map((doc) => ({ doc, score: scoreDocument(doc, query, stats) }))
        .filter((item) => item.score > 0)
        .sort((left, right) => {
          if (right.score !== left.score) return right.score - left.score;
          return right.doc.date.localeCompare(left.doc.date);
        })
        .slice(0, 8)
        .map((item) => item.doc);

      if (!matched.length) {
        status.hidden = true;
        results.hidden = false;
        results.innerHTML = '<div class="search-empty">换个更具体的关键词试试，比如论文名、方法名、模型名或标签。</div>';
        return;
      }

      status.hidden = true;
      results.hidden = false;
      renderResults(results, matched, query);
    }

    input.addEventListener("input", runSearch);

    try {
      const response = await fetch("/assets/data/search-index.json");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = await response.json();
      documents = (payload.documents || []).map((doc) => {
        const title = doc.title || "";
        const subtitle = doc.subtitle || "";
        const summary = doc.summary || "";
        const tagsText = (doc.tags || []).join(" ");
        const sectionLabel = doc.section_label || "";
        const content = doc.content || "";

        return {
          ...doc,
          norm: {
            title: normalizeText(title),
            subtitle: normalizeText(subtitle),
            summary: normalizeText(summary),
            tags: normalizeText(tagsText),
            sectionLabel: normalizeText(sectionLabel),
            content: normalizeText(content),
          },
          index: {
            title: makeFieldIndex(title),
            subtitle: makeFieldIndex(subtitle),
            summary: makeFieldIndex(summary),
            tags: makeFieldIndex(tagsText),
            sectionLabel: makeFieldIndex(sectionLabel),
            content: makeFieldIndex(content),
          },
        };
      });

      stats = buildStats(documents);
      runSearch();
    } catch (error) {
      console.error("Failed to load search index", error);
      status.hidden = false;
      status.textContent = "搜索索引加载失败了，刷新页面再试一次。";
      results.hidden = true;
    }
  }

  window.addEventListener("DOMContentLoaded", init);
})();
