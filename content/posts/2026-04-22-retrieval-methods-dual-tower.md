---
title: 召回方法整理：双塔召回
subtitle: DSSM、YouTubeDNN、谷歌双塔、Facebook 双塔、MOBIUS、DMR、Deep Retrieval
section: papers
section_label: 论文解读
summary: 整理召回方法文档中“双塔召回”部分的论文与笔记内容，仅做排版整理。
tags: [recsys,retrieval,dual-tower]
---

## 微软 DSSM 2013

Learning Deep Structured Semantic Models for Web Search using Clickthrough Data

用 query 和 document 的展现点击数据来计算语义匹配。

### 模型结构

query 和 document 使用的是相同的参数

word hashing

基于 n-gram，目的是为了减小 bag-of-word 的维数，eg. #good# → #go, goo, ood, od#

### 训练样本

正样本是 query 有点击的 document，负样本是采样的未点击 document(非曝光未点击)。

### 相似度评估

query embedding 和 document embedding 的余弦距离

## YoutubeDNN 2016

Deep Neural Networks for YouTube Recommendations

多分类任务，使用用户侧特征（观看历史、搜索历史、人口特征），预估下一个想看的视频。没

有使用视频侧特征。

### 优化目标

交叉熵损失函数

### 模型结构

模型输出为 user embedding，softmax 层参数为 video embedding。

### 特征处理

search query：query tokenize into unigram and bigram and embed token

样本 age：训练集中样本时间最大值-当前样本时间，预测时用 0 或者微小的复数（解决视频流行度分布变化大，但模型只能表示训练周期内的平均概率），不依赖视频上传时间，预测时用户向量对所有 item 都是同一个值。

### 训练样本

正样本：所有 yotube 观看而非推荐产生的观看记录，用户看完的视频负样本：一个正样本采样几千个负样本，增加重要性权重。每个用户选取相同样本数，保证用户等权重。

### 实现代码

https://github.com/ogerhsou/Youtube-Recommendation-

Tensorflow/blob/master/youtube_recommendation.py

### 测试结果

## 谷歌双塔 2019

Sampling-bias-corrected neural modeling for large corpus item recommendations

流数据训练，in-batch 负采样，并减小偏差，batch 内负采样优势是不用增加采样步骤，适应样本

分布变化。

### 模型结构

两个塔相互独立，输出是 inner product。

### 优化目标

weighted log-likelihood 损失函数，reward 是正样本权重（观看时长等）

### 训练样本

正样本是点击的视频，负样本是每天产生的流数据中获取 batch， in-batch item。

in-batch item 是幂次分布，会导致训练样本存在较大的 bias，热门 item 更常出现在 batch 中，因

此在 logit 中加 logQ correction，其中 p_j 是 item j 在随机 batch 中采样概率

这个参数比较关键，如果不设置的话推荐的词都非常小众，设置大了的话推荐的词几乎全是热

门，参考设置 log10(p)，其中 p 是样本出现的概率。

---

added by Eric Wang Peng

在代码中，这部分的实现有些问题

根据定义：

p = B*n/N

这里

●   n 是某个词出现的次数，

●   N 是所有词出现的次数（所有 market 之和）

●   B 是训练的 batch_size

这里比较 trick 的是：

我们由于引入的 market mask，所以相当于将一个 batch 拆成了多个小的 batch 在使用，所了对于

一个 market m 来说，其 batch_size = B * N_m / N，即正比于这个 market 中词的数量的。

代入上面得到：

p= B * N_m * n / N^2

现在是 p = n/N_m

修正项=B*N_m*N_m/N^2

由于取 log，所以 log(p) = log(B) + log(N_m * n) - 2log(N) = log(N_m) + log(n) - 2 log(N)

现在是： p = n / N_m ⇒ log(p) = log(n) - log(N_m)

修正项是: log(N_m) + log(n) - 2 log(N) - log(n) + log(N_m) = 2log(N_m) - 2 log(N)

这里可以这么理解：

●   当 n 越大的时候，说明词越热门，越容易出现在 negative 的样本中；

●   当 N_m 越大的时候，说明这个 market 比重大，那么这个词出现在别的样本中成为负样本

的可能性越大。

对比我们的实现：

,ln(cast(count(1) over (partition by keyword, market) as

double)/cast(count(1) over (partition by market) as double)) as weight

是错误的，应该是：

,ln((count(1) over (partition by keyword, market)) *(count(1) over

(partition by market))) / (count(1) * count(1))) as weight

这里省去了 cast.

这个错误带来的效果是：

对于 market 来说，对于小 market 的词，p 被高估，因此 log(p)过高，s - log(p)过低，当 w 是负样

本时，梯度不足，学习的比较慢。

---

### 样本纠偏

预估样本在随机 batch 中的采样概率 p，将采样概率 p 预估转化成连续两次采样到样本之间的平均

步数。

### 纠偏的一些参考方法

https://zhuanlan.zhihu.com/p/574752588

### 技巧

embedding normalize

超参数 temperature

### 测试结果

## Facebook 双塔 2020

Embedding-based Retrieval in Facebook Search

样本构造，对比点击、展现作为正样本，随机负采样、有展无点作为负样本，并做了 hard

negative mining and hard positive mining。

在线 ann 检索，对比了不同向量量化方法，更高效检索。

### 模型结构

query encoder 和 document encoder 是独立的网络，用 cos 函数计算两个向量的距离。

### 验证指标

### 损失函数

triplet loss

### 样本构造

### ●   正样本

-   用户 click 数据

-   用户 impression 数据

两种正样本效果差不多。

hard positive 样本构造：失败的 search session 数据作为正样本。

### ●   负样本

-   随机负采样

-   hard 样本构造

动机：people search 中总是把同名的人都排在前面，目标的人并不会比其他同名人高，可能是由

于负样本太简单导致模型没有学好社交特征。

解决方案：使用与正样本相近的样本作为 hard nagative。

1. online hard negative

在 batch 内，将与正样本 doc 相似度最高的其他 query 的 doc 作为负样本，对 recall 提

升很大。

问题：可能一个 batch 内所有样本都不够 hard

2. offline hard negative

只用 hard negative 效果还不如随机采样，因为模型更注重其他特征而忽略了文本特征。

实际上候选集中绝大多数是简单负样本，第一种方法是 easy: hard=100:1 的负样本，第

二种方法是 hard model 到 easy model 的迁移学习。

### 向量增强

向量加权：随机采样模型在召回量大时能召回目标，hard negative 模型在召回量小候选集小时能

召回目标，因此用多个模型得到的 embedding 加权

级联模型：先召回大量的候选集，再用第二个模型的结果去过滤。

### 特征工程

文本特征用 character n-gram，加入 word n-gram 会带来提升。

位置特征，在 query 侧和 document 侧都加入分别的位置。

社交向量特征，独立模型。

## 百度 MOBIUS 2019

MOBIUS: Towards the Next Generation of Query-Ad Matching in Baidu’s Sponsored

Search

在匹配层不仅考虑相关性，还考虑其他指标，比如 cpm、roi 等，来提升广告的 cpm。要解决的

问题是低相关性高出现频次的 query-ad pair 和大规模候选集的计算量。

### 优化目标

### 模型结构

Pr(click)用来线上 ctr 预估，Pr(bad)用来过滤 bad case。

### 线上检索

MIPS 将业务相关的系数作用到计算用户向量和广告向量内积的阶段。

### 实验效果

## 阿里 DMR 2020

Deep Match to Rank Model for Personalized Click-Through Rate Prediction

### 参考代码

https://github.com/lvze92/DMR

## 字节 2021

Deep Retrieval- Learning A Retrievable Structure for Large-Scale Recommendations
