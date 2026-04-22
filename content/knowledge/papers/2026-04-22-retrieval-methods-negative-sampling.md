---
title: 召回方法整理：负采样
subtitle: MNS、InfoNCE 改进、DCL、ProtoNCE、Debias CL、CLHNS、DirectCLR
section: papers
section_label: 论文解读
summary: 整理召回方法文档中“负采样”部分的论文与笔记内容，并按论文笔记结构重新整理排版。
tags: [recsys,retrieval,negative-sampling]
---

## 谷歌 MNS 2020

> Mixed Negative Sampling for Learning Two-tower Neural Networks in Recommendations

### 解决的问题

1. batch 内负采样存在选择偏差：没有点击的样本不会成为负样本。
2. 调整采样分布时缺少灵活性：采样分布取决于训练数据，不能灵活调整，可能与真实分布存在较大差异。

### Mixed Negative Sampling

点击数据生成一组 logits 矩阵；另一组 logits 来自从 item 库中随机抽样的样本，再与 query 组合。两部分横向拼接，形成更大的训练矩阵。

原笔记里的结论是：

- 这种做法减少了选择偏差，因为每个样本都有机会成为负样本。
- 同时可以通过调整采样策略，更灵活地调整数据分布。

### 相关方法

infoNCE 的改进方法包括：

- ProtoNCE[63]
- DCL[71]
- DirectNCE[72]
- SCL[8]
- FNCL[35]

其中：

- DirectNCE：只取前 `d` 个维度计算损失。
- SCL：面向有监督学习。
- FNCL：目标是去除伪负样本。

## DCL 2022 ICLR

> Decoupled Contrastive Learning

### 解决的问题

1. InfoNCE 对 batch size 敏感。
2. 需要大量负样本。

### 推导

- 在损失函数的梯度中，可以分解出一个正负样本耦合（NPC）因子。
- 图 a：随着 batch size 增大，变异系数减小，NPC 波动减小，NPC 增大。
- 图 b：随着 batch size 增大，NPC 更容易接近 1。

基于这个观察，本文在损失函数中去掉了正负样本耦合的部分，并增加权重系数，使正样本之间隔得越远时具有更大的权重。

### 实验结果

- batch size 越小时，去掉 NPC 的效果比带 NPC 的提升更明显。

## ProtoNCE 2021 ICLR

用原型 prototype 替代负样本，用集中程度代替温度系数；通过 EM 算法估计 prototype 的分布参数。

## Debias CL 2020 NeurIPS

> Debias Contrastive Learning

### 解决的问题

采样样本中包含伪负样本，会导致 performance 降低。

### 方法

用先验的样本类概率，以及正样本和样本的采样概率，来替代负样本采样概率，并据此设计纠偏损失函数。

### 存在的问题

1. 需要预估类先验概率，超参数选择对结果影响较大。
2. 假设数据的类是均匀分布。

### 推导过程

#### 原始损失函数与理想无偏损失函数

假设存在潜在类标签分配函数 `h`，可以将样本分类；并假设分类符合均匀分布。正例类 `c` 的概率是 `ρ(n) = n+`，其他类的概率是 `τ- = 1 - n+`。

- 采样到数据 `n'` 来自正例同一类的概率。
- 采样到数据 `n'` 来自正例不同类的概率。

原笔记还记录：其中 `Q` 是权重系数，假设 `Q = N`。但在实际中，不能只从不同类样本中负采样，负样本只能从整个数据集采样，因此其中有 `τ+` 的概率来自于正样本同一类。

#### 分析有偏损失函数与无偏损失函数之间的 gap

原笔记里的结论是：

1. 当无偏损失函数值越小（负样本乘项越小），第二项值越大，因此有偏和无偏损失函数之间的 gap 越大。
2. 优化有偏和无偏损失函数得到的数据表达差异很大。

因此希望实际损失函数更接近无偏损失函数。

#### 推导更接近无偏损失函数的实际损失

- 与正样本不同类中负采样的概率是未知的，可以根据条件概率得到采样数据 `n'` 的概率。
- 从与正样本不同类中采样的概率可以进一步代入无偏损失函数。
- 最终仍然从整个样本库中负采样，但新增了一项从正样本类中采样的补偿项。
- 其中 `τ+` 是超参数。

### 实验结果

1. 超参数 `τ+` 对结果影响较大，难以选择。
2. 负样本数 `N` 在某个特定范围内效果最好。
3. 正样本数 `M` 越大效果越好。

## CLHNS 2021 ICLR

> Contrastive Learning with Hard Negative Samples

### 解决的问题

采样负样本时，希望构造难负样本，同时平衡负样本难度和伪负样本问题。

### 方法

假设负样本服从 von Mises-Fisher 分布，对损失函数进行化简，通过调整集中参数 `β` 来增大难负样本的权重。

### 存在的问题

1. 需要做类先验概率预估，超参数选择对结果影响较大。
2. 假设数据的类是均匀分布。
3. 在下游任务中效果不一定都更好。

### 推导过程

#### 好的难负样本标准

原笔记先讨论了“什么是好的 hard negative”。

#### 假设负样本来自 von Mises-Fisher 分布

- `β >= 0` 是集中参数。
- 当正负样本距离越近时，`β` 越大，被采样的概率权重越高。
- 从负样本中采样的概率，可以表示成从所有样本和正样本中共同采样。
- 因此可以将损失函数进一步改写。

### 实验结果

原笔记记录了对应实验结果，但没有在提取文本中保留具体数值。

## DirectCLR 2022 ICLR

> Understanding Dimensional Collapse in Contrastive Self-supervised Learning

### 其他

- <https://cloud.tencent.com/developer/article/2313165>

### 对比

- <https://zhuanlan.zhihu.com/p/642797247>

## Self-Attentive Sequential Recommendation

> BERT4Rec: Sequential Recommendation with Bidirectional Encoder Representations from Transformer
