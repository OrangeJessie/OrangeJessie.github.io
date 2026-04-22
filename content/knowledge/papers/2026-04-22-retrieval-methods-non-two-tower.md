---
title: 召回方法整理：非双塔结构
subtitle: TDM、Deep Retrieval、RecForest
section: papers
section_label: 论文解读
summary: 整理召回方法文档中“非双塔结构”部分的论文与笔记内容，并按论文笔记结构重新整理排版。
tags: [recsys,retrieval,indexing]
---

## 阿里 TDM 2018 KDD

> Learning Tree-based Deep Model for Recommender Systems

### 解决问题

user 和 item 之间没有交叉，希望通过树结构减少 item 候选数量。

### 模型结构

- 树的叶子节点为 item，其余节点为 item 的集合。
- 树的双亲节点概率取子节点中最大的概率。

### 损失函数

- 叶子节点为正样本。
- 从叶子到根路径上的所有节点都视为正样本。
- 每一层的其他节点随机采样作为负样本。

### 召回方法

- 每一层只需要计算选中 node 下的 item，从而减少大量 candidate。

### 树的构建

#### 初始化

随机排序 category，并将 category 下的 item 随机排序；如果 item 属于多个 category，则随机分到其中一个。之后不断将这些 item 递归地二分，直到不能继续划分，作为初始化树。

#### 学习

- 使用 K-means 聚类。

### 训练步骤

1. Construct an initial tree and train the model till converging.
2. Learn to get a new tree structure in basis of trained leaf nodes' embeddings.
3. Train the model again with the learnt new tree structure.

## 字节 DR 2021

> Deep Retrieval: Learning A Retrievable Structure for Large-Scale Recommendations

## 微软 RecForest 2022 NeurIPS

> Recommender Forest for Efficient Retrieval

### 解决问题

索引构建和向量表达学习是解耦的，这可能引入不一致。

### ANN 索引

1. 树方法，例如 KD-tree。
2. 哈希方法，例如 Local Sensitive Hashing（LSH）。
3. 矢量量化方法，例如 Product Quantization（PQ）。
4. 近邻图方法，例如 Hierarchical Navigable Small World（HNSW）。
