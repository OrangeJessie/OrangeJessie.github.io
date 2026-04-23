---
title: 推荐系统的多样性提升实践
subtitle: 指标、召回优化、排序策略与频控
section: experience
section_label: 经验分享
group: methods
summary: 从指标、召回优化、排序策略和频控四个角度整理推荐系统多样性提升方法。
tags: [recsys,diversity,ranking]
---

当一个推荐系统的效率已经很高的时候，往往就需要开始考虑多样性。

`CTR` 和 `CVR` 的建模只针对这一次的展现，是一个短期行为；而越精确的模型，往往会带来越多同质化内容。实时重定向内容的转化链路效率通常高于其他内容，用户很容易陷入信息茧房。长期来看，用户体验会下降，导致用户流失，转化效率下降。

因此，一个好的推荐系统，不仅要考虑短期内的转化效率提升，还要考虑长期的用户体验。归根结底，多样性优化最终还是要落到系统整体转化量的增长上，例如 `GMV`、`order` 或广告收入。

## 多样性指标

多样性通常有两种含义，一个是外延，一个是内容异质。

- 所谓外延，就是覆盖范围，例如一次推荐覆盖了用户多少兴趣方向，或者包含多少商品类别。
- 内容异质则是指推荐内容之间的差异性，例如大部分推荐内容是否都来自相同实体。

从这两个含义出发，可以设置一些具体指标。

### 外延指标

- 类目宽度：展现的类目数 / 总类目数
- 实体宽度

### 内容异质指标

- 连续 `m` 天同一类目展现占比超过 `n%` 的用户占比
- 连续 `n` 个内容里有 `m` 个是相同实体的用户占比
- 任意实体展现超过 `n` 次的用户占比

这些指标是否有效，需要建立长期实验来观察。如果在长期实验中，多样性指标的提升能带来 `DAU`、`CTR` 和 `CVR` 的提升，那么这些指标才是有效的。

## 多样性优化方向

优化系统多样性时，同样要从它的两种含义去思考。

- 外延主要通过召回阶段丰富候选集，从源头上增加内容方向的广度，确保推荐系统能覆盖更多类别和用户兴趣点。
- 内容异质主要通过排序阶段的策略调整，优化多样性呈现，减少相似内容的重复。

简单来说，一方面要增加覆盖用户更多兴趣、更广类目的召回；另一方面，要从排序策略上减少重复内容。

## 召回优化

对召回的优化主要有三个层面。

### 单个兴趣点召回不同内容

单纯的重定向召回缺乏相关商品的推荐，而双塔模型召回恰好擅长捕捉潜在关系。

双塔模型召回的经典文章是谷歌 2019 年发表的 [Sampling-bias-corrected neural modeling for large corpus item recommendations](https://research.google/pubs/sampling-bias-corrected-neural-modeling-for-large-corpus-item-recommendations/)。这篇工作采用了 `in-batch` 负采样和样本纠偏参数，是一个很好的 baseline 模型。

### 覆盖更多兴趣点

多向量双塔召回非常适合做多兴趣点召回。用户的单向量表示总是受到主要兴趣的影响，导致主要兴趣召回得更多，而一些不那么重要的兴趣召回得更少。

[Multi-Interest Network with Dynamic Routing for Recommendation at Tmall](https://researchportal.hkust.edu.hk/en/publications/multi-interest-network-with-dynamic-routing-for-recommendation-at-2) 在 2019 年提出了 `MIND`。它使用胶囊网络和动态路由算法，让商品向量向近似的兴趣向量靠近，再进行聚类，从而得到不同方向的兴趣向量，但整体结构比较复杂，计算开销也更大。

在 2020 年，阿里的 [Controllable Multi-Interest Framework for Recommendation](https://arxiv.org/abs/2005.09347) 提出了 `ComiRec`。它在 `MIND` 的基础上，用 `self-attention` 代替动态路由来隐式提取用户的不同兴趣向量，并在 serving 阶段增加控制多样性指标的集成模块，用来平衡召回多样性和精确度。

上面两种多向量召回都是隐式地学习用户的多个兴趣。如果某个用户的兴趣很广泛，但其中一个兴趣占了绝对主导，这种方式依然不一定能得到足够多样化的结果，多个向量召回出来的内容仍可能属于相同兴趣方向。

微软在 2020 年 SIGIR 发表的 [Octopus: Comprehensive and Elastic User Representation for the Generation of Recommendation Candidates](https://www.microsoft.com/en-us/research/?p=683799) 则显式控制各个兴趣向量之间的正交性，确保不同向量召回的商品尽可能不相关，并降低单个向量兴趣不纯净带来的影响。

### 拓展兴趣点

热门、最快上升、年龄性别、类别最热等一系列规则召回，精确度不高，但可以作为补充探索的方式。

实际实践中，这类方法通常效果不好。一方面，这些内容与用户历史兴趣无关，排序模型很难把它们排在前面，所以展现量很少；另一方面，即使展现出来，用户往往也不感兴趣，又会给排序模型更多负反馈。

## 排序策略优化

### Determinantal Point Process（DPP）

可以用商品集合的相似度矩阵的行列式来表达商品集合的多样性。把矩阵看作向量集合时，行列式表示这些向量张成的有向体积；向量间夹角越大，也就是商品越不相关时，有向体积越大。因此，矩阵行列式越大，商品集合的多样性越好。

目标可以写成：

$$
Y^* = \arg\max_{Y \subseteq Z} \det(L_Y)
$$

其中，$Y$ 是当前候选集，$Z$ 是商品集合。

Hulu 在 2018 年 NeurIPS 发表的 [Fast Greedy MAP Inference for Determinantal Point Process to Improve Recommendation Diversity](https://papers.nips.cc/paper/7805-fast-greedy-map-inference-for-determinantal-point-process-to-improve-recommendation-diversity) 提出了一种求解过程，使用贪心算法，每次从候选集中选一个使当前商品集多样性增加最多的商品加入结果集合。

在这之后，可以经过一系列化简，得到最大化后验概率的算法。化简过程这里不展开。

### 频控策略

频控策略更多是启发式规则，需要根据具体业务数据进行分析。

一个直接的做法是分析从召回到转化的漏斗数据，计算每一步的通过率：

$$
\text{通过率} = \frac{\text{下一阶段商品数}}{\text{上一阶段商品数}}
$$

例如，召回之后类目 `A` 有 `100` 个商品，而在粗排之后只有 `30` 个，那么通过率就是 `0.3`。

通过分析每一阶段的通过率，可以定位到底是哪一阶段导致系统多样性明显下降，再针对性地采取措施。

## 总结

在优化系统多样性之前，首先要搞清楚：哪些多样性指标真的能给系统带来长期收益。

如果这个问题没有想明白，那么那些不能带来业务指标提升的多样性优化，最终很容易停留在局部修补的层面，难以长期被重视。
