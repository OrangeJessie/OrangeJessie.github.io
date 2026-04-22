---
title: 召回方法整理：非双塔结构
subtitle: TDM、Deep Retrieval、RecForest
section: papers
section_label: 论文解读
summary: 整理召回方法文档中“非双塔结构”部分的论文与笔记内容，仅做排版整理。
tags: [recsys,retrieval,indexing]
---

## 阿里 TDM 2018 KDD

Learning Tree-based Deep Model for Recommender Systems

### 解决问题

user 和 item 之间没有交叉，减少 item 候选数量

### 模型结构

树的叶子节点为 item，其余节点为 item 的集合，树的双亲节点概率取子节点中最大的概率：

### 损失函数

叶子节点为正样本，所有到根节点的节点都为正样本，每一层的其他节点随机采样作为负样本。

### 召回方法

每一层只需要算选中的 node 下的 item，减少了大量的 candidate。

### 树的构建

初始化：随机排序 category，并将 category 下的 item 随机排序（如果 item 属于多个

category，随机给一个），然后将这些 item 分为两部分直到不可以再分（二叉树举例），作为初

始化的树。

学习：K-means 聚类。

### 训练步骤

1) Construct an initial tree and train the model till converging;

2) Learn to get a new tree structure in basis of trained leaf nodes’ embeddings;

3) Train the model again with the learnt new tree structure.

### 效果

## 字节 DR 2021

Deep Retrieval: Learning A Retrievable Structure for Large-Scale Recommendations

## 微软 RecForest 2022 NIPS

Recommender Forest for Efficient Retrieval

### 解决问题

索引构建和学习向量表达是解耦的，可能引入不一致。

### 模型结构

### ANN 索引

1. 树方法，如 KD-tree

2. 哈希方法，如 Local Sensitive Hashing (LSH)

3. 矢量量化方法，如 Product Quantization (PQ)

4. 近邻图方法，如 Hierarchical Navigable Small World (HNSW) HNSW
