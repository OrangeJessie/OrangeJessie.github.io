---
title: 召回索引建模
subtitle: TDM、Deep Retrieval、RecForest
section: papers
section_label: 论文解读
group: retrieval
summary: 基于原论文与现有笔记，按统一模板整理非双塔结构的召回论文，并在文首做论文对比。
tags: [recsys,retrieval,indexing]
---

## 论文对比

| 论文 | 主要解决问题 | 待改进方向 |
| --- | --- | --- |
| TDM 2018 | 大规模 item corpus 下无法对所有 item 做精细打分 | 树结构学习与更新成本较高 |
| Deep Retrieval 2020 | embedding + ANN 两步法存在结构与目标不一致 | 离散结构学习与 beam search 训练更复杂 |
| RecForest 2022 | 表示学习与 ANN 索引解耦，导致准确率损失 | 多树索引和 decoder routing 增加建模复杂度 |

## 阿里 TDM 2018

> Learning Tree-based Deep Model for Recommender Systems

### 解决问题

- 大规模推荐中，如果对全量 item 都做精细预测，计算成本太高，难以做 full corpus retrieval。
- 传统做法往往退回到 inner product + ANN，但这会限制模型表达能力，尤其是更复杂的 user-item interaction。

### 模型结构

- TDM 使用 tree-based retrieval。
- item 位于树叶节点，其余内部节点代表 item 集合。
- 预测时从 coarse 到 fine，自顶向下遍历树节点，判断每个 user-node pair 是否继续向下展开。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/tdm-architecture.png" alt="TDM 模型结构图">
  <figcaption>TDM 结构图：把 item corpus 组织成树，并在多层时间窗口与节点表示上完成逐层检索。</figcaption>
</figure>

### 样本构造

- 原笔记记录：
  - 叶子节点为正样本；
  - 从叶子到根路径上的节点都视为正样本；
  - 每一层其他节点随机采样作为负样本。

### 关键信息

- 论文关键不只是“用树做索引”，而是“树结构与模型一起学习”。
- 原笔记保留的树构建流程包括：
  - 初始化：按 category / item 排序后递归切分；
  - 学习：用 leaf embeddings 迭代更新树结构，可结合 K-means。

### 实验结论

- KDD 官方摘要明确写到：在两个大规模真实数据集上，TDM 显著优于传统方法。
- 同时，淘宝展示广告平台的线上 A/B test 也验证了它的效果。

## 字节 Deep Retrieval 2020

> Deep Retrieval: Learning A Retrievable Structure for Large-Scale Recommendations

### 解决问题

- 大规模推荐希望以子线性复杂度召回 top relevant candidates。
- 传统“先学 inner-product model，再套 ANN”的两步法依赖欧式空间假设，而且结构与目标函数不完全一致。

### 模型结构

- DR 直接学习一个 retrievable structure。
- candidate items 被编码进 discrete latent space。
- latent codes 是模型参数的一部分，会和其他神经网络参数一起联合学习。
- 检索时通过 beam search 在结构上做搜索。

### 关键信息

- DR 的关键思想是：把“可检索结构”本身纳入学习，而不是后处理。
- 这使得模型不必依赖 ANN 的欧式空间假设。

### 实验结论

- 论文摘要明确表述：DR 能在 large-scale recommendation 中同时做到更高质量召回和高效检索。

## 微软 RecForest 2022

> Recommender Forest for Efficient Retrieval

### 解决问题

- 推荐系统通常先学习 user/item embeddings，再依赖 ANN 检索。
- 但 representation learning 与 ANN index construction 是独立的，这会导致两者不兼容，损失推荐精度。

### 模型结构

- RecForest jointly 学习 embedding 和 index。
- index 由多个 k-ary trees 组成，每棵树通过 hierarchical balanced clustering 对 item set 做划分。
- 每个 item 在每棵树中对应一条从 root 到 leaf 的唯一路径。
- 检索网络采用 encoder-decoder routing：
  - encoder 编码 user context；
  - transformer-based decoder 通过 beam search 找 top-N items。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/recforest-architecture.png" alt="RecForest 模型结构图">
  <figcaption>RecForest 结构图：encoder-decoder 检索网络与多棵平衡树索引联合学习。</figcaption>
</figure>

### 关键信息

- multiple trees 能缓解边界 item 被错误分区的问题。
- transformer decoder 提升 routing 精度。
- 树参数跨层共享，因此 index 本身更省内存。

### 实验结论

- NeurIPS 官方摘要明确给出：在 5 个推荐数据集上，RecForest 以更简单的训练成本，同时优于现有方法的推荐准确率和效率。
