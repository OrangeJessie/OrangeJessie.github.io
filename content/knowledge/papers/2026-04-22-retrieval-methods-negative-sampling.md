---
title: 召回方法整理：负采样
subtitle: MNS、DCL、ProtoNCE、Debias CL、CLHNS、DirectCLR
section: papers
section_label: 论文解读
summary: 基于原论文与现有笔记，按统一模板整理负采样与对比学习相关论文，并在文首做论文对比。
tags: [recsys,retrieval,negative-sampling]
---

## 论文对比

| 论文 | 主要解决问题 | 待改进方向 |
| --- | --- | --- |
| MNS 2020 | in-batch negative 有选择偏差且采样分布不灵活 | 需要额外索引库采样与混合策略设计 |
| DCL 2022 | InfoNCE 对 batch size 敏感，强依赖大量负样本 | 主要改 loss，对结构建模帮助有限 |
| ProtoNCE 2021 | 直接用 instance negatives 可能不够稳定 | 依赖 prototype / clustering 质量 |
| Debias CL 2020 | 随机负样本里混入 false negatives | 需要先验估计，超参数敏感 |
| CLHNS 2021 | 想要 hard negatives，但又不能显著引入伪负样本 | 依赖分布假设，下游收益不总是稳定 |
| DirectCLR 2022 | contrastive learning 也会发生 dimensional collapse | 主要解决表示塌缩，对任务构造本身改动有限 |

## 谷歌 MNS 2020

> Mixed Negative Sampling for Learning Two-tower Neural Networks in Recommendations

### 解决问题

- in-batch negative sampling 存在选择偏差，不是所有 item 都有机会成为负样本。
- 采样分布被训练数据分布绑定，缺少灵活调节空间。

### 模型结构

- 论文仍然是在 two-tower recommendation 框架下工作。
- 核心创新点不在 backbone，而在 negative sampling 策略。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/mns-architecture.png" alt="MNS 负采样结构图">
  <figcaption>MNS 结构图：将 batch 内样本与索引库额外采样样本共同拼入 logits，形成 mixed negative sampling。</figcaption>
</figure>

### 样本构造

- 一部分负样本来自 batch 内样本。
- 另一部分负样本来自 item 库中的随机采样样本。
- 原笔记将两部分 logits 横向拼接后统一参与训练。

### 关键信息

- MNS 的重点是“混合”负样本来源，而不是只依赖 in-batch negatives。
- 这样每个 item 都更有机会出现在负样本里，同时也能更灵活地控制采样分布。
- 原笔记还顺手列了几种 InfoNCE 改进路线：ProtoNCE、DCL、DirectNCE、SCL、FNCL。

### 实验结论

- 基于原笔记可确认的结论是：MNS 主要被用来缓解选择偏差并提升采样分布可控性。

## DCL 2022

> Decoupled Contrastive Learning

### 解决问题

- InfoNCE 对 batch size 非常敏感。
- 训练往往依赖大量负样本。

### 模型结构

- DCL 不是重新设计 encoder，而是改 contrastive objective。
- 核心思想是把正负样本耦合项从损失里拆掉。

### 关键信息

- 论文关注 NPC（正负样本耦合）因子。
- 原笔记记录：随着 batch size 增大，NPC 波动减小，且更容易接近 1。
- 基于这一观察，DCL 去掉正负样本耦合项，并调整正样本权重。

<figure class="article-figure">
  <img src="/assets/post-media/retrieval-methods/dcl-batch-size.png" alt="DCL batch size 与 NPC 关系图">
  <figcaption>DCL 论文中的关键观察：batch size 越大，NPC 因子的波动越小，也更接近 1。</figcaption>
</figure>

### 实验结论

- 原笔记明确记录：batch size 越小时，DCL 相比带 NPC 的目标收益更明显。

## ProtoNCE 2021

> ProtoNCE

### 解决问题

- 只依赖 instance-level negatives，可能不够稳定，也不一定能利用潜在聚类结构。

### 模型结构

- 用 prototype 替代一部分 instance-level negative 角色。
- 使用 EM 算法估计 prototype 的分布参数。

### 样本构造

- 原型成为训练中的关键对象，不再只是简单从样本库里取负样本。

### 关键信息

- 原笔记只保留了核心思想：用 prototype 代替负样本，用集中程度代替温度系数。

## Debias CL 2020

> Debiased Contrastive Learning

### 解决问题

- 随机采到的负样本里会混入 same-label negatives，也就是 false negatives。
- 这会降低 contrastive learning 的效果。

### 模型结构

- 核心是 debiased contrastive objective，而不是新的 encoder 结构。
- 通过类先验和采样概率修正损失函数。

### 样本构造

- 负样本仍从整体样本库中采样。
- 但训练目标会对这些负样本里潜在的 false negatives 做概率修正。

### 关键信息

- 原笔记明确记录了两点限制：
  1. 需要估计类先验概率，超参数敏感；
  2. 假设类分布近似均匀。
- 论文理论上分析了有偏损失与无偏损失之间的 gap，并推导更接近无偏损失的目标。

### 实验结论

- 官方摘要明确给出：该 debiased objective 在 vision、language、reinforcement learning 等 benchmark 上 consistently 优于当时 SOTA。
- 原笔记还保留了经验性结论：`τ+` 很敏感，负样本数和正样本数都存在效果区间。

## CLHNS 2021

> Contrastive Learning with Hard Negative Samples

### 解决问题

- 对比学习希望利用更难的负样本，但又不能依赖监督相似度标签。
- 同时需要在“更难”与“更可能是假负样本”之间做平衡。

### 模型结构

- 论文核心是无监督 hard negative sampling family，而不是新 backbone。
- 通过一个可控 hardness 的采样机制来选择 harder negatives。

### 样本构造

- 在无监督设定下构造 hard negatives。
- 原笔记进一步把这个方法理解为对 von Mises-Fisher 分布参数进行控制，从而改变更难负样本的采样权重。

### 关键信息

- 官方摘要明确指出：用户可以控制 hardness。
- 一个极限情形会让同类样本更紧密、异类样本更分离。
- 原笔记也记录了这类方法的限制：依赖类先验估计假设，且下游任务收益不一定统一。

### 实验结论

- TUM 官方摘要明确指出：该方法在多种模态的 downstream tasks 上提升了表现，同时几乎不增加实现复杂度和额外计算开销。

## DirectCLR 2022

> Understanding Dimensional Collapse in Contrastive Self-supervised Learning

### 解决问题

- 对比学习虽然避免了 complete collapse，但仍然会发生 dimensional collapse。
- 也就是说，表示会塌到一个低维子空间，而不能充分利用整个表示空间。

### 模型结构

- 基于对 collapse dynamics 的理论分析，论文提出 DirectCLR。
- DirectCLR 直接优化 representation space，而不是依赖可训练 projector。

### 关键信息

- 论文的重要结论是：contrastive learning 也会发生 dimensional collapse，这一点并不只存在于 non-contrastive 方法里。
- DirectCLR 的设计目标是绕开 projector 带来的表示空间问题。

### 实验结论

- OpenReview / 论文摘要明确给出：在 ImageNet 上，DirectCLR 优于带 trainable linear projector 的 SimCLR。
