---
title: 召回方法整理：负采样
subtitle: MNS、InfoNCE 改进、DCL、ProtoNCE、Debias CL、CLHNS、DirectCLR
section: papers
section_label: 论文解读
summary: 整理召回方法文档中“负采样”部分的论文与笔记内容，仅做排版整理。
tags: [recsys,retrieval,negative-sampling]
---

## 谷歌 MNS ACM2020

Mixed Negative Sampling for Learning Two-tower Neural Networks in Recommendations

### 解决的问题

1. batch 内负采样存在选择偏差：没有点击的样本不会成为负样本

2. 调整采样分布时缺少灵活性：采样分布取决于训练数据，不能灵活调整，可能和真实分布存在

较大差异

### Mixed Negative Sampling

点击数据生成 logits 矩阵              ，    是从 item 库中随机抽样的样本，和 query 生成 logits 矩

阵         ，横向拼接形成                       的矩阵。

减少了选择偏差，每个样本都有机会成为负样本，并且可以通过调整   更加灵活地调整数据集。

### 评估结果

infoNCE 的改进

ProtoNCE[63], DCL[71], DirectNCE[72], SCL[8], FNCL[35]

DirectNCE: 只取前 d 个维度计算损失

SCL: 面向有监督学习

### FNCL：去除掉伪负样本

## DCL 2022 ICLR

Decoupled Contrastive Learning.pdf

### 解决的问题

1. InfoNCE 对 batch_size 敏感

### 2. 需要大量负样本

### 推导

在损失函数的梯度中可以分解出一个正负样本耦合(NPC)的因子

其中 NPC 因子

图 a，随着 batch_size 增大，变异系数减小，NPC 波动减小，NPC 增大；图 b，随着 batch_size

增大，NPC 有更大的概率为 1。

基于此，本文在损失函数中去掉正负样本耦合的部分：

增加了权重系数，使当正样本之间隔得越远时，具有越大的权重

其中

实验结果

在 batch_size 越小的时候，效果比带有 NPC 的好越多。

## ProtoNCE 2021 ICLR

用原型 prototype 替代负样本，集中程度代替温度系数。使用 EM 算法估计 prototype 的分布参数。

## DCL 2020 NeurIPS

Debias Contrastive Learning.pdf

### 代码

解决的问题：采样的样本中有伪负样本，会带来 performance 降低方法：用先验的样本类概率和正样本&样本的采样概率来替代负样本采样概率，设计纠偏损失函数存在的问题：

1. 需要做类先验概率的预估（超参数的选择对效果影响大）

2. 假设数据的类是均匀分布

### 推导过程

●   原始损失函数

●   理想无偏损失函数

假设存在潜在类标签分配函数 h，可以将样本分类，假设分类符合均匀分布正例类 c 的概率𝜌(𝑛) = 𝑛+ ，其他类的概率为𝜏− = 1 − 𝑛+

采样到数据𝑛′来自正例同一类的概率：

采样到数据𝑛′来自正例不同类的概率：

𝑛其中 Q 是权重系数，假设 Q=N。在实际中，不能从不同类样本中负采样，𝑛− 只能从整个数据集𝑛𝑛 中采样，因此𝑛𝑛− 有𝜏+ 的概率来自于正样本同一个类。

●   分析有偏损失函数与无偏损失函数之间的 gap 和影响

有偏损失函数的下界

1. 当无偏损失函数值越小（负样本乘项越小），第二项的值越大，使有偏和无偏损失函数之

间的 gap 越大

2. 优化有偏和无偏的损失函数得到的数据表达差异很大

因此希望实际损失函数能更接近无偏损失函数。

●   推导得到更接近无偏损失函数的损失函数

与正样本不同类中负采样的概率是未知的，根据条件概率可得到采样数据𝑛′的概率

那么从与正样本不同类中采样的概率为

代入无偏的损失函数

在这个损失函数中，我们仍然从整个样本库中负采样，但新增了一项正样本类中采样，继续化简得到

其中𝜏+ 是超参数。

●   伪代码实现纠偏损失函数

实验结果

1. 超参数𝜏+ 对实验结果影响较大，难以选择

2. 负样本数 N 在某个特定范围内，效果最好

3. 正样本数 M 越大效果越好

## CLHNS 2021 ICLR

Contrastive Learning with Hard Negative Samples

### 代码

解决的问题：采样负样本时构造难负样本，并平衡其样本难度和伪负样本方法：假设负样本服从 von Mises–Fisher 分布，对损失函数进行化简，通过对集中参数𝛽的调整增大难负样本的权重。存在的问题：

1. 需要做类先验概率的预估（超参数的选择对效果影响大）

2. 假设数据的类是均匀分布

3. 在下游任务中效果并不是都好

### 推导过程

●   好的难负样本的标准

●   假设负样本从 von Mises–Fisher 分布的数据中采样

𝑛𝑛 是 von Mises–Fisher 分布，𝛽 ≥ 0是集中参数。

𝑛(𝑛) ≠ 𝑛(𝑛− )满足第一个原则，𝛽𝑛(𝑛)𝑛 𝑛(𝑛− )满足第二个原则，正负样本距离越近，𝛽增大被采样的概率权重。

从负样本中采样的概率可以表示为从所有样本&正样本中采样

因此，损失函数可以表示为

●   伪代码实现构造难负样本损失函数

实验结果

## DirectCLR 2022 ICLR FB

Understanding Dimensional Collapse in Contrastive Self-supervised Learning.pdf

### 代码

### 其他

https://cloud.tencent.com/developer/article/2313165

### 对比

https://zhuanlan.zhihu.com/p/642797247

### Self-Attentive Sequential Recommendation

BERT4Rec: Sequential Recommendation with Bidirectional Encoder Representations from

Transformer
