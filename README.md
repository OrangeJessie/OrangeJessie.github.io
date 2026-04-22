# OrangeJessie.github.io

这是一个纯静态博客仓库。

页面发布方式：

- GitHub Pages 直接托管仓库根目录里的 HTML / CSS / JS
- 仓库里不再依赖 Jekyll、Liquid、主题模板或 Ruby 构建链

## 仓库结构

- `content/posts/*.md`
  - 文章内容源
- `content/pages/*.md`
  - 页面内容源
- `scripts/build_static_site.py`
  - 静态站生成脚本，读取 `content/` 下的 Markdown，调用 `pandoc` 生成最终页面
- `assets/css/site.css`
  - 主样式文件
- `index.html` `404.html` `aboutme/` `contact/` `papers/` `ai-tools/` `experience/` `game-space/` `tags/` `2023-*/`
  - 生成后的最终静态页面
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
