---
title: 召回方法整理：双塔召回
subtitle: DSSM、YouTubeDNN、谷歌双塔、Facebook 双塔、MOBIUS、DMR、Deep Retrieval
section: papers
section_label: 论文解读
summary: 整理召回方法文档中“双塔召回”部分的论文与笔记内容，并按论文笔记结构重新整理排版。
tags: [recsys,retrieval,dual-tower]
---

## 微软 DSSM 2013

> Learning Deep Structured Semantic Models for Web Search using Clickthrough Data

用 query 和 document 的展现点击数据来计算语义匹配。

### 模型结构

- query 和 document 使用相同的参数。
- 使用 word hashing，基于 n-gram 减小 bag-of-words 的维数，例如 `#good# -> #go, goo, ood, od#`。

### 训练样本

- 正样本：query 有点击的 document。
- 负样本：采样的未点击 document（非曝光未点击）。

### 相似度评估

- query embedding 和 document embedding 的余弦距离。

## YouTubeDNN 2016

> Deep Neural Networks for YouTube Recommendations

多分类任务，使用用户侧特征（观看历史、搜索历史、人口特征），预估下一个想看的视频；没有使用视频侧特征。

### 优化目标

- 交叉熵损失函数。

### 模型结构

- 模型输出为 user embedding，softmax 层参数为 video embedding。

### 特征处理

- search query：query tokenize into unigram and bigram and embed token。
- 样本 age：训练集中样本时间最大值减去当前样本时间；预测时用 `0` 或者微小的复数。这个特征用来解决视频流行度分布变化快、但模型只能表示训练周期内平均概率的问题；它不依赖视频上传时间，因此预测时用户向量对所有 item 都是同一个值。

### 训练样本

- 正样本：所有 YouTube 观看而非推荐产生的观看记录，用户看完的视频。
- 负样本：每个正样本采样几千个负样本，并增加重要性权重。每个用户选取相同样本数，保证用户等权重。

### 实现代码

- <https://github.com/ogerhsou/Youtube-Recommendation-Tensorflow/blob/master/youtube_recommendation.py>

## 谷歌双塔 2019

> Sampling-bias-corrected neural modeling for large corpus item recommendations

流数据训练，使用 in-batch 负采样并做样本纠偏。batch 内负采样的优势是不需要额外增加采样步骤，也能适应样本分布变化。

### 模型结构

- 两个塔相互独立，输出是 inner product。

### 优化目标

- weighted log-likelihood 损失函数，reward 是正样本权重（例如观看时长等）。

### 训练样本

- 正样本：点击的视频。
- 负样本：每天产生的流数据中获取 batch，使用 in-batch item 作为负样本。
- in-batch item 呈幂次分布，会导致训练样本存在较大的 bias：热门 item 更常出现在 batch 中，因此在 logit 中加 `logQ correction`，其中 `p_j` 是 item `j` 在随机 batch 中的采样概率。
- 这个参数比较关键：如果不设置，推荐的词会非常小众；设置过大，推荐词又几乎全是热门词。原文笔记里给出的参考设置是 `log10(p)`，其中 `p` 是样本出现的概率。

### 补充说明（Eric Wang Peng）

这部分是原笔记里的额外补充，主要指出代码实现中样本纠偏计算有问题。

- 根据定义：`p = B * n / N`
- `n` 是某个词出现的次数。
- `N` 是所有词出现的次数（所有 market 之和）。
- `B` 是训练的 `batch_size`。

由于引入了 market mask，相当于将一个 batch 拆成了多个小 batch 在使用；因此对于某个 market `m` 来说，其 `batch_size = B * N_m / N`，即正比于这个 market 中词的数量。

代入后得到：

- `p = B * N_m * n / N^2`
- 现在实现里使用的是 `p = n / N_m`
- 修正项应为 `B * N_m * N_m / N^2`

由于取对数：

- `log(p) = log(B) + log(N_m * n) - 2log(N) = log(N_m) + log(n) - 2log(N)`
- 现在实现是：`p = n / N_m`，因此 `log(p) = log(n) - log(N_m)`
- 修正项变成：`log(N_m) + log(n) - 2log(N) - log(n) + log(N_m) = 2log(N_m) - 2log(N)`

原笔记里的解释是：

- 当 `n` 越大时，说明词越热门，越容易出现在 negative 样本中。
- 当 `N_m` 越大时，说明这个 market 比重大，那么这个词出现在别的样本中成为负样本的可能性越大。

对比当时实现：

```sql
,ln(cast(count(1) over (partition by keyword, market) as double) /
    cast(count(1) over (partition by market) as double)) as weight
```

原笔记认为正确写法应为：

```sql
,ln((count(1) over (partition by keyword, market)) *
    (count(1) over (partition by market))) /
   (count(1) * count(1)) as weight
```

这一错误带来的效果是：对于小 market 的词，`p` 被高估，因此 `log(p)` 过高，`s - log(p)` 过低；当 `w` 是负样本时，梯度不足，学习会更慢。

### 样本纠偏

- 预估样本在随机 batch 中的采样概率 `p`，再将采样概率 `p` 转化成连续两次采样到样本之间的平均步数。

### 参考链接

- <https://zhuanlan.zhihu.com/p/574752588>

### 技巧

- embedding normalize
- 超参数 temperature

## Facebook 双塔 2020

> Embedding-based Retrieval in Facebook Search

样本构造上，同时使用点击和展现作为正样本，随机负采样和有展无点作为负样本，并做了 hard negative mining 和 hard positive mining。在线侧采用 ANN 检索，并对不同向量量化方法做了比较以提升检索效率。

### 模型结构

- query encoder 和 document encoder 是独立网络，用 cos 函数计算两个向量的距离。

### 损失函数

- triplet loss。

### 样本构造

#### 正样本

- 用户 click 数据。
- 用户 impression 数据。
- 两种正样本效果差不多。
- hard positive 样本构造：失败的 search session 数据作为正样本。

#### 负样本

- 随机负采样。
- hard 样本构造。

动机：people search 中总是把同名的人都排在前面，目标的人并不会比其他同名人更高，可能是由于负样本太简单，导致模型没有学好社交特征。

解决方案：使用与正样本相近的样本作为 hard negative。

1. online hard negative
   在 batch 内，将与正样本 doc 相似度最高的其他 query 的 doc 作为负样本，对 recall 提升很大。
   问题是：可能一个 batch 内所有样本都还不够 hard。
2. offline hard negative
   只用 hard negative 的效果还不如随机采样，因为模型更注重其他特征而忽略了文本特征。

原笔记里的结论是：候选集中绝大多数其实是简单负样本，第一种方法相当于 easy:hard = 100:1 的负样本；第二种方法更像是 hard model 到 easy model 的迁移学习。

### 向量增强

- 向量加权：随机采样模型在召回量大时更容易召回目标；hard negative 模型在召回量小、候选集更小时更容易召回目标，因此可以对多个模型得到的 embedding 做加权。
- 级联模型：先召回大量候选，再用第二个模型结果进一步过滤。

### 特征工程

- 文本特征用 character n-gram，加入 word n-gram 会带来提升。
- 位置特征：在 query 侧和 document 侧都加入各自的位置。
- 社交向量特征：独立模型。

## 百度 MOBIUS 2019

> MOBIUS: Towards the Next Generation of Query-Ad Matching in Baidu’s Sponsored Search

在匹配层不仅考虑相关性，还考虑其他指标，比如 cpm、roi 等，来提升广告的 cpm。要解决的问题是低相关性高出现频次的 query-ad pair，以及大规模候选集的计算量。

### 模型结构

- `Pr(click)` 用来线上做 ctr 预估。
- `Pr(bad)` 用来过滤 bad case。

### 线上检索

- MIPS 将业务相关的系数作用到计算用户向量和广告向量内积的阶段。

## 阿里 DMR 2020

> Deep Match to Rank Model for Personalized Click-Through Rate Prediction

### 参考代码

- <https://github.com/lvze92/DMR>

## 字节 2021

> Deep Retrieval: Learning A Retrievable Structure for Large-Scale Recommendations
