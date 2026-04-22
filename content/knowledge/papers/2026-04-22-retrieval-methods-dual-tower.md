---
title: 召回方法整理：双塔召回
subtitle: DSSM、YouTubeDNN、谷歌双塔、Facebook 双塔、MOBIUS、DMR、Deep Retrieval
section: papers
section_label: 论文解读
summary: 基于原论文与现有笔记，按统一模板整理双塔召回相关论文，并在文首做论文对比。
tags: [recsys,retrieval,dual-tower]
---

## 论文对比

| 论文 | 主要解决问题 | 模型结构关键词 | 样本构造 | 实验结论 |
| --- | --- | --- | --- | --- |
| DSSM 2013 | 语义匹配难以覆盖 query-document 深层语义 | 双塔语义投影、word hashing、cosine similarity | clickthrough 数据，点击文档为正样本 | 在真实 Web ranking 数据上优于当时 latent semantic baselines |
| YouTubeDNN 2016 | 超大规模视频推荐的 candidate generation 与 ranking | candidate generation DNN、user embedding、sampled softmax | 用户观看序列构造监督信号，负样本通过采样获得 | 论文强调深度学习带来显著线上效果提升 |
| Google 双塔 2019 | in-batch negative 的采样偏差会伤害大规模召回 | two-tower、item content tower、logQ correction | streaming data + in-batch negatives | 离线与在线实验都支持 sampling bias correction 有效 |
| Facebook 双塔 2020 | 社交搜索需要同时建模文本与搜索者上下文 | 独立 query/document encoder、ANN 检索、hard mining | click / impression / hard negative / hard positive | 多个 vertical 上取得显著线上收益 |
| MOBIUS 2019 | matching 层只看相关性，商业指标在 ranking 层才引入，导致整体回报不足 | matching + CTR 目标、active learning、ANN / MIPS | billions of query-ad pairs，主动学习补 bad cases | 作为百度广告召回系统首版落地，提升商业回报与检索效率 |
| DMR 2020 | CTR 预测中缺少显式 user-item relevance 建模 | User-to-Item、Item-to-Item、match-to-rank | 基于 CTR prediction 数据训练 | 在 public + industrial datasets 上显著优于 baseline |
| Deep Retrieval 2020 | ANN 两步法依赖欧式空间假设，结构学习与检索解耦 | discrete latent codes、beam search、joint structure learning | user-item interaction（如 clicks） | 在大规模推荐中同时兼顾准确率与子线性检索效率 |

## 微软 DSSM 2013

> Learning Deep Structured Semantic Models for Web Search using Clickthrough Data

### 解决问题

- 传统 keyword matching 很难处理 query 和 document 的深层语义匹配。
- 传统 latent semantic methods 在大规模 Web 搜索下表达能力和可扩展性不足。

### 模型结构

- query tower 和 document tower 将两侧文本映射到同一个低维语义空间。
- 相关性通过 query/document 表示之间的距离来计算，文中使用 cosine similarity。
- 为了支持大词表，论文使用 word hashing，将词映射成 letter-trigram 表示。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/dssm-architecture.png" alt="DSSM 模型结构图">
  <figcaption>DSSM 论文结构图：query 与 document 经过双塔投影后在共享语义空间内做相似度计算。</figcaption>
</figure>

### 样本构造

- 使用 clickthrough data。
- 给定 query，被点击的 document 作为正样本。
- 未点击 document 用作负样本。

### 关键信息

- 训练目标是最大化 clicked documents 在给定 query 条件下的条件似然。
- 论文强调该方法是 discriminative training，而不是单纯学习无监督语义空间。
- word hashing 是论文能落到 Web-scale 的关键工程点。

### 实验结论

- 在真实 Web document ranking 数据集上，DSSM 最优模型显著优于此前的 latent semantic baselines。

## YouTubeDNN 2016

> Deep Neural Networks for YouTube Recommendations

### 解决问题

- YouTube 推荐规模极大，需要同时做好 candidate generation 和 ranking。
- 传统方法难以处理海量用户行为与大规模视频库。

### 模型结构

- 论文将系统拆成 candidate generation 和 ranking 两阶段。
- 你当前这篇召回笔记里主要对应 candidate generation：使用用户历史行为、搜索历史、人口属性等特征，生成 user embedding。
- 输出层对视频 vocabulary 做 softmax，可视作 item embedding 参数化的一部分。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/youtube-dnn-architecture.png" alt="YouTubeDNN 模型结构图">
  <figcaption>YouTubeDNN 候选召回结构图：多路用户特征汇总为 user vector，再通过近邻检索生成候选视频。</figcaption>
</figure>

### 样本构造

- 正样本来自用户真实观看行为。
- 训练时通过采样方式近似 softmax，并引入负样本。

### 关键信息

- 论文明确强调这是工业系统论文，重点是“候选召回 + 精排”二阶段架构。
- 在候选召回部分，样本 age 特征被用来缓解内容流行度随时间剧烈变化的问题。
- 原笔记记录：search query 做 unigram / bigram tokenization 并 embedding。

### 实验结论

- Google 官方摘要只明确指出：深度学习带来了 dramatic performance improvements。

## 谷歌双塔 2019

> Sampling-bias-corrected neural modeling for large corpus item recommendations

### 解决问题

- 大规模 item retrieval 中，in-batch negatives 虽然高效，但会引入 sampling bias。
- item 频率分布高度偏斜时，这种偏差会明显伤害模型效果。

### 模型结构

- two-tower neural network。
- item tower 编码丰富的 item content features。
- 打分使用 user tower 与 item tower 的相似性。
- 核心新增点不是 backbone，而是 training objective 里的 sampling bias correction。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/google-two-tower-architecture.png" alt="谷歌双塔模型结构图">
  <figcaption>谷歌采样纠偏双塔结构图：用户侧与候选侧独立编码，并在 in-batch softmax 目标下完成训练。</figcaption>
</figure>

### 样本构造

- 使用 streaming data 训练。
- 正样本来自真实用户点击 / 观看行为。
- 负样本主要来自 random mini-batch 中的 in-batch items。

### 关键信息

- 论文提出 item frequency estimation 方法，用 streaming data 估计 item 出现频率。
- 通过 `logQ correction` 对 logits 做修正，以减轻热门 item 在 batch 中更容易出现所带来的偏差。
- 原笔记里额外保留了一段实现层的补充，指出 market-aware 场景下概率估计很容易写错。

### 实验结论

- Google 官方摘要明确给出：理论分析、模拟实验、两个真实数据集离线实验，以及 YouTube live A/B tests 都支持 sampling bias correction 的有效性。

## Facebook 双塔 2020

> Embedding-based Retrieval in Facebook Search

### 解决问题

- Facebook Search 不仅依赖 query text，还强依赖搜索者上下文与社交图信息。
- Boolean matching 难以兼顾个性化语义召回和系统效率。

### 模型结构

- query encoder 与 document encoder 分别建模两侧输入。
- 论文将 embedding-based retrieval 接入典型 search system，并结合 ANN 检索。
- 论文还讨论了向量量化和系统级优化。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/facebook-search-architecture.png" alt="Facebook Search 双塔结构图">
  <figcaption>Facebook Search 论文中的统一 embedding 架构：query encoder 与 document encoder 分别建模检索两侧输入。</figcaption>
</figure>

### 样本构造

- 原笔记记录：click 和 impression 都被用于构造正样本。
- 负样本包括随机负采样和 harder negatives。
- 同时还做了 hard positive mining。

### 关键信息

- Facebook 论文特别强调：除了文本，还要建模 social context。
- 原笔记记录了两类 hard negative：
  1. online hard negative：在 batch 内选最相近但不匹配的 doc。
  2. offline hard negative：离线构造更难的样本。
- 系统侧重点还包括 ANN 参数调优和 full-stack optimization。

### 实验结论

- 官方摘要只明确给出：在 Facebook Search 的 selected verticals 上观测到显著线上指标收益。

## 百度 MOBIUS 2019

> MOBIUS: Towards the Next Generation of Query-Ad Matching in Baidu’s Sponsored Search

### 解决问题

- 传统 sponsored search 是 funnel-shaped 三层结构。
- matching 层只负责相关性，ranking 层才考虑 CPM、ROI 等商业指标，导致整体 commercial return 偏低。

### 模型结构

- 用 CTR prediction 直接训练 matching layer，不再只优化 query-ad relevance。
- 引入 active learning，解决 matching 层 click history 不足的问题。
- 系统侧用 ANN / MIPS 做大规模 ad retrieval。
- 原笔记提到 `Pr(click)` 和 `Pr(bad)` 两个输出：前者用于 CTR 预估，后者用于过滤 bad cases。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/mobius-training-framework.png" alt="MOBIUS 训练框架图">
  <figcaption>MOBIUS 训练与数据增强流程图：点击模型、relevance judger 和 augmented buffer 共同参与 matching 训练。</figcaption>
</figure>

### 样本构造

- 论文明确写的是 billions of query-ad pairs。
- 原笔记和论文摘要都指出：通过 active learning 补充 bad cases。

### 关键信息

- 这是把商业目标前移到 matching 层的一篇工业系统论文。
- active learning 是论文的重要训练机制。
- ANN / MIPS 是满足低时延检索约束的关键工程组件。

### 实验结论

- KDD 页面和论文摘要都表明：MOBIUS-V1 作为百度下一代 query-ad matching 首版系统，兼顾了检索效率和商业收益目标。

## 阿里 DMR 2020

> Deep Match to Rank Model for Personalized Click-Through Rate Prediction

### 解决问题

- 现有 CTR 预测模型更关注 user representation，本身对 user-item relevance 的显式建模不足。
- 排序任务里需要更直接地表达用户对 target item 的偏好强度。

### 模型结构

- DMR 将 matching 的思想引入 ranking。
- 包含 User-to-Item Network 和 Item-to-Item Network 两条子网络，分别刻画两种 user-item relevance。
- 再结合传统 rec model features 输入到 MLP 做 CTR prediction。

### 样本构造

- 论文基于 CTR prediction 数据训练。

### 关键信息

- User-to-Item relevance 通过 embedding space 内积表示。
- Item-to-Item relevance 通过用户历史 item 与 target item 的关系建模。
- 论文本质上是 “match-to-rank”。

### 实验结论

- 论文摘要明确给出：在 public 和 industrial datasets 上显著优于 state-of-the-art baselines。

### 参考代码

- <https://github.com/lvze92/DMR>

## 字节 Deep Retrieval 2020

> Deep Retrieval: Learning A Retrievable Structure for Large-Scale Recommendations

### 解决问题

- 大规模推荐中，希望在子线性复杂度下准确召回 top candidates。
- 传统方法通常是先学 inner-product model，再用 ANN 检索；这种两步法依赖欧式空间假设，并且结构学习与检索解耦。

### 模型结构

- DR 直接学习一个 retrievable structure，而不是先学 embedding 再套 ANN。
- candidate items 被编码到 discrete latent space。
- candidate latent codes 与其他网络参数一起联合学习。
- 检索时使用 beam search。

### 样本构造

- 论文摘要明确给出：使用 user-item interaction data，例如 clicks。

### 关键信息

- 这是“把检索结构直接纳入学习目标”的代表性工作。
- 与传统 two-tower + ANN 路线相比，DR 不再依赖 ANN 的欧式空间假设。

### 实验结论

- 论文摘要指出：在大规模推荐场景中，DR 能兼顾高精度召回与高效率检索。
