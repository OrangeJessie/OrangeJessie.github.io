---
title: 召回方法整理：双塔召回多样性
subtitle: MIND、ComiRec、SINE、Octopus、REMI、PinnerSage、DAT
section: papers
section_label: 论文解读
summary: 基于原论文与现有笔记，按统一模板整理多兴趣召回相关论文，并在文首做论文对比。
tags: [recsys,retrieval,multi-interest]
---

## 论文对比

| 论文 | 主要解决问题 | 待改进方向 |
| --- | --- | --- |
| MIND 2019 | 单一 user vector 难以表示多兴趣 | 胶囊网络与动态路由计算开销大 |
| ComiRec 2020 | 多兴趣召回既要准确也要可控地兼顾多样性 | aggregation 模块和多样性控制带来额外部署复杂度 |
| SINE 2021 | 多兴趣方法难处理大规模概念原型与稀疏兴趣激活 | 依赖概念原型池与稀疏激活设计 |
| Octopus 2020 | 多通道兴趣表示容易引入无关候选且成本高 | quota 分配与弹性通道增加 serving 成本 |
| REMI 2023 | 多兴趣学习更大的瓶颈在训练而非结构本身 | 训练框架更复杂，需要 negative mining 和 regularization |
| PinnerSage 2020 | 单 embedding 不能完整表达用户多兴趣 | 聚类复杂度高，异构行为难处理 |
| DAT 2021 | 双塔缺少交互且类别不平衡 | 额外辅助向量和对齐损失增加训练复杂度 |

## 阿里 MIND 2019

> Multi-Interest Network with Dynamic Routing for Recommendation at Tmall

### 解决问题

- 现有深度推荐方法通常只用一个向量表示用户，难以表达大规模用户的多样兴趣。
- matching 阶段尤其依赖更细粒度的 user interest representation。

### 模型结构

- 使用多个 interest vectors 表示一个用户。
- 核心模块是基于 capsule routing 的 multi-interest extractor。
- 使用 label-aware attention 帮助学习多兴趣用户表示。
- 原笔记补充了 dynamic routing、shared transformation matrix 和动态兴趣数等实现点。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/mind-architecture.png" alt="MIND 模型结构图">
  <figcaption>MIND 论文结构图：行为序列经多兴趣提取器得到多个 interest capsules，再通过 label-aware attention 参与训练。</figcaption>
</figure>

### 样本构造

- 论文是典型的推荐学习设置：用户历史行为序列配合目标 item 监督。
- 原笔记记录：label-aware attention 会根据目标 item 选择更相关的 interest capsule。

### 关键信息

- dynamic routing 的目标是把用户历史行为聚成多个兴趣簇。
- routing logits 采用随机初始化，有利于学出不同兴趣方向。
- label-aware attention 是训练阶段的重要组件。

### 实验结论

- 官方摘要明确写到：在多个公开 benchmark 和一个大规模 Tmall 工业数据集上，MIND 优于 state-of-the-art。
- 论文同时说明该方法已在 Mobile Tmall 首页主流量上线。

## 阿里 ComiRec 2020

> Controllable Multi-Interest Framework for Recommendation

### 解决问题

- 单一 user embedding 无法反映用户一段时间内的多个兴趣。
- 多兴趣召回不仅要提升准确率，还要显式控制多样性。

### 模型结构

- 包含 multi-interest module，用来从行为序列中提取多个兴趣向量。
- 包含 aggregation module，用于从多兴趣召回结果中得到整体推荐。
- 论文强调 controllable factor，用来平衡 accuracy 和 diversity。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/comirec-architecture.png" alt="ComiRec 模型结构图">
  <figcaption>ComiRec 结构图：先进行 multi-interest extraction，再在 serving 侧通过 aggregation module 平衡精度与多样性。</figcaption>
</figure>

### 关键信息

- 论文提供 Dynamic Routing 与 Self-Attention 两种多兴趣提取方式。
- aggregation module 不只是简单拼接 topK 候选，而是显式引入 diversity 控制。
- `Diversity@N` 是论文强调的指标之一。

### 实验结论

- 论文摘要明确给出：在两个真实数据集 Amazon 和 Taobao 上，相比现有多兴趣方法有显著提升。
- 论文同时说明该框架已在阿里离线分布式平台部署。

## 阿里 SINE 2021

> Sparse-Interest Network for Sequential Recommendation

### 解决问题

- 用户行为序列常常包含多个概念不同的 item，统一 embedding 容易被最近高频行为主导。
- 现有多兴趣方法通常只发现少量概念簇，难以匹配真实系统里的大规模 concept pool。
- 用户真正活跃的兴趣通常是稀疏的。

### 模型结构

- SINE 包含 sparse-interest module，从大概念池中为每个用户自适应激活少量概念原型。
- 再用 interest aggregation module 主动预测当前意图，并聚合多个 interest embeddings。
- 原笔记补充：模块中包含 concept activation、prototype assignment 和 aggregation。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/sine-architecture.png" alt="SINE 模型结构图">
  <figcaption>SINE 结构图：从 concept pool 中做 sparse activation，再通过 intention selector 完成兴趣聚合。</figcaption>
</figure>

### 关键信息

- SINE 的核心不是简单增加 interest 数量，而是从大原型池中做 sparse activation。
- 与部分多兴趣方法不同，SINE 最终输出是聚合后的用户表示。

### 实验结论

- 官方摘要明确给出：在多个公开 benchmark 和一个大规模工业数据集上，SINE 相比 SOTA 有 substantial improvement。

## 微软 Octopus 2020

> Octopus: Comprehensive and Elastic User Representation for the Generation of Recommendation Candidates

### 解决问题

- candidate generation 既要全面覆盖用户兴趣，又要保持检索效率。
- 传统单向量用户表示不足以覆盖多兴趣。
- 一些 multi-channel 方法虽然更全面，但也更容易带来无关候选和更高成本。

### 模型结构

- Octopus 为用户生成多个兴趣向量。
- 与常规 multi-channel 结构不同，Octopus 的表示是 elastic 的：通道规模和类型会根据用户自适应确定。
- 原笔记补充：通过 grouping head、通道分配和 quota 机制控制不同兴趣通道。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/octopus-framework.png" alt="Octopus 框架图">
  <figcaption>Octopus 框架图：通过 channel activation 和 grouped attentive aggregation 生成弹性的多通道用户表示。</figcaption>
</figure>

### 关键信息

- 论文的重点不只是“多兴趣”，而是“全面 + 弹性 + 可落地”。
- 原笔记里记录的 quota allocation 是 serving 侧的重要设计。
- elasticity 的意义是减少无关表示和无效计算。

### 实验结论

- Microsoft 官方摘要明确指出：在工业和公开数据集上，相比 SOTA baselines 验证了 Octopus 的有效性。

## 微软 REMI 2023

> Rethinking Multi-Interest Learning for Candidate Matching in Recommender Systems

### 解决问题

- 现有多兴趣 candidate matching 工作更关注模型结构，而忽略训练框架本身。
- 论文指出两大核心问题：
  1. uniformly sampled softmax 带来过多 easy negatives；
  2. routing collapse，使每个兴趣只由极少数 item 决定。

### 模型结构

- 论文重点不是重新设计复杂 backbone，而是重做训练框架。
- 关键组件包括：
  - IHN（interest-aware negative mining）
  - RR（routing regularization）

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/remi-ihn.png" alt="REMI IHN 算法图">
  <figcaption>REMI 中的 IHN 训练算法：围绕 interest-aware negative mining 重构 sampled softmax 训练过程。</figcaption>
</figure>

### 样本构造

- 基于 sampled softmax 的训练框架。
- IHN 会更倾向采到对当前兴趣向量更难区分的负样本。

### 关键信息

- 这篇论文最重要的视角是：多兴趣学习的瓶颈不一定在结构，而在训练。
- RR 用来缓解 attention / routing 的稀疏塌缩问题。

### 实验结论

- HKUST 论文摘要明确指出：通过重新审视训练框架，解决 easy negatives 和 routing collapse 后，多兴趣表示的表达性得到改善。
- 原笔记补充了不同采样方式和消融实验。

## PinnerSage 2020

> PinnerSage: Multi-Modal User Embedding Framework for Recommendations at Pinterest

### 解决问题

- 单个高维 user embedding 不足以完整理解用户多兴趣。
- 工业系统需要既可解释、又可扩展的多兴趣表示。

### 模型结构

- 通过 hierarchical clustering（Ward）把用户行为聚成多个概念一致的簇。
- 再用 representative pins（Medoids）表示每个兴趣簇。
- 再为不同簇估计 importance，用于后续召回。

### 样本构造

- 原笔记记录：对用户近 90 天行为做聚类。

### 关键信息

- Ward clustering + Medoids 是论文最有辨识度的结构设计。
- Medoid 设计兼顾效率、鲁棒性和可解释性。
- cluster importance 用来控制多兴趣检索成本。

### 实验结论

- KDD 官方摘要明确给出：线上和线下 A/B 实验都表明 PinnerSage 显著优于 single embedding methods。

## 美团 DAT 2021

> A Dual Augmented Two-tower Model for Online Large-scale Recommendation

### 解决问题

- two-tower 缺少 tower 间信息交互。
- category data imbalance 会削弱长尾类目效果。

### 模型结构

- DAT 在双塔基础上加入 AMM（Adaptive-Mimic Mechanism）。
- 同时加入 CAL（Category Alignment Loss）对齐不同类别 item representation。
- 原笔记补充了 mimic loss 与 category alignment 的实现理解。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/dat-architecture.png" alt="DAT 模型结构图">
  <figcaption>DAT 结构图：在双塔检索框架上增加辅助向量、mimic loss 与 category alignment loss。</figcaption>
</figure>

### 关键信息

- AMM 通过为 query 和 item 定制 augmented vector，缓解双塔缺少交互的问题。
- CAL 处理类目不平衡。

### 实验结论

- 官方摘要明确给出：DAT 在大规模离线数据集上优于 baseline，且在线 A/B testing 也带来推荐质量提升。
