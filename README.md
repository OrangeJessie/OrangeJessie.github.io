# OrangeJessie.github.io

这是一个纯静态博客仓库。

线上地址：

- [https://orangejessie.github.io/](https://orangejessie.github.io/)

页面发布方式：

- GitHub Pages 直接托管仓库根目录里的 HTML / CSS / JS
- 仓库里不再依赖 Jekyll、Liquid、主题模板或 Ruby 构建链

## 仓库结构

- `content/pages/*.md`
  - 页面内容源
- `content/knowledge/papers/*.md`
- `content/knowledge/ai-tools/*.md`
- `content/knowledge/experience/*.md`
- `content/knowledge/game-space/*.md`
  - 各个知识模块的文章内容源，按模块分目录管理
- `scripts/build_static_site.py`
  - 静态站生成脚本，读取 `content/` 下的 Markdown，调用 `pandoc` 生成最终页面
- `scripts/new_article.py`
  - 新文章脚手架，默认按当前“论文解读风格”创建文章 Markdown
- `assets/css/site.css`
  - 主样式文件
- `index.html` `404.html` `aboutme/`
  - 首页和基础页面
- `knowledge/papers/` `knowledge/ai-tools/` `knowledge/experience/` `knowledge/game-space/` `knowledge/tags/`
  - 生成后的知识模块页、文章页和标签页
- `.nojekyll`
  - 告诉 GitHub Pages 直接按静态文件托管，不走 Jekyll 处理

## 本地生成

要求本地有：

- `python3`
- `pandoc`

执行：

```bash
python3 scripts/build_static_site.py
```

## 新建文章

默认可以直接交互式创建：

```bash
python3 scripts/new_article.py
```

也可以一次性带参数：

```bash
python3 scripts/new_article.py \
  --section experience \
  --group projects \
  --title "推荐系统的多样性提升实践" \
  --subtitle "指标、召回优化、排序策略与频控" \
  --summary "从指标、召回优化、排序策略和频控四个角度整理推荐系统多样性提升方法。" \
  --tags "recsys,diversity,ranking" \
  --template single-card \
  --build
```

模板说明：

- `single-card`
  - 单篇文章，正文会按当前论文解读页的单卡片风格生成，适合经验分享、工具总结、项目实践
- `paper-series`
  - 多论文整理模板，带 `论文对比 / 解决问题 / 模型结构 / 样本构造 / 关键信息 / 实验结论`

## 更新流程

1. 修改 `content/` 下的 Markdown 内容和页面元信息
2. 执行构建脚本
3. 提交生成后的静态页面
4. 推送到 GitHub

```bash
python3 scripts/build_static_site.py
git add .
git commit -m "Update site"
git push origin master
```

## CI

`.github/workflows/ci.yml` 会在 GitHub Actions 上：

- 安装 `pandoc`
- 运行 `python3 scripts/build_static_site.py`
- 检查生成结果是否已提交

如果你改了 `content/` 或生成逻辑，但忘了把产物一起提交，CI 会直接失败。
