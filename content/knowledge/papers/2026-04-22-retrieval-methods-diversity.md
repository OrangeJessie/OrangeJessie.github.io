---
title: 召回方法整理：双塔召回多样性
subtitle: MIND、ComiRec、SINE、Octopus、REMI、PinnerSage、DAT、爱奇艺多兴趣优化
section: papers
section_label: 论文解读
summary: 整理召回方法文档中“双塔召回多样性”部分的论文与笔记内容，仅做排版整理。
tags: [recsys,retrieval,multi-interest]
---

## 阿里 MIND 2019 CIKM

Multi-Interest Network with Dynamic Routing for Recommendation at Tmall

### 解决的问题

用多个向量表示用户的多种兴趣，采用动态路由算法将历史商品聚合成多个集合，每个集合对应

用户特定兴趣的向量表示。

### 缺点：

1. 结构复杂，计算开销大

### 胶囊网络与动态路由算法

胶囊网络与神经元类似，区别是胶囊网络输入的是多个向量。

c 通过动态路由算法计算，对线性变换后的输入向量 u 加权，动态路由算法在每一步迭代中，会向

与输出向量 a 更接近的输入向量 u 靠近（更接近的 a 和 u 内积更大，在下一步中 softmax 权重更

大），近似聚类。

Squashing 保证向量方向不变，模大于 0 小于 1。s 的模越大越接近 1，越小越接近 0，与

sigmoid 函数相似。

### 模型结构

模型目的是要将特征映射到用户表达，                               ，当 V 为一维向量时，类似

YoutubeDNN。

Embedding 和 Pooling 层，others features 是用户基础特征(age, gender, id 等连接起来)，

item N 是用户历史行为的 item 特征，Label 是目标商品的特征(brand_id, shop_id 等对冷启有

效，通过 average pooling 构建 item 向量)。

Multi-Interest Extractor 层，动态路由算法计算用户兴趣向量。

1. 采用 shared 线性变换矩阵(上文中 W，不同 item 的 W 相同)。

2. 高斯分布随机初始化 routing logits(b)，这样来获得不同的兴趣向量，否则每个兴趣向量

最后都是最感兴趣的向量。

3. 对不同用户采用动态的兴趣数量，

Label-Aware Attention 层，interest capsule 的权重取决于与目标 item 的兼容性。

测试指标和结果

### Hyperparameter Choosen

Initialization of routing logits b: N(0, 1) 在 epoch=1 时效果最好，随着 epoch 增加，与 N(0,

0.1) N(0, 5)逐渐相同

power number p in label-aware attention: p=0 效果最差，相当于每个 interest capsule 都有

相同的权重，p 越大效果越好。

### online 效果

动态 embedding 个数比 k=7 微涨，涨幅不大。

参考代码：

https://github.com/shenweichen/DeepMatch/blob/master/deepmatch/models/mind.py

https://zhuanlan.zhihu.com/p/145283113

## 阿里 ComiRec 2020 KDD

Controllable Multi-Interest Framework for Recommendation.pdf

用 self-attention 层来隐式提取多个用户兴趣向量，并在 serving 时增加召回结果集成模块，平衡

多样性和精确度。

### 优点：

1. 隐式地学习用户多个兴趣向量，能够适应数据分布变化

2. 在 serving 时增加集成模块，平衡多样性和精确度

### 缺点：

1. 用户兴趣数量固定，设置兴趣数量对结果有较大影响，且对兴趣单一的用户，学习效果没

有单兴趣好

2. 召回结果重复度较高、特征较少、即时性差

### 模型结构

### Multi-interest Module

1. Dynamic Routing

和 MIND 相同

2. Self-Attention Layer

，其中 H 是 user behavior

embedding，每一个历史行为都可能影响每一个 embedding。

### Model training

目标 item embedding 选出一个 user behavior embedding，用选出的 embedding 来算 loss

，

### Aggregation Module

用于在 serving 的时候，得到多个 interest embedding 后，获得整体的 top-N item。

基本做法是从候选集中选出每个兴趣向量最相近的 K 个 item，                               ，但是这

样并不是最好的，用户更倾向被推荐新的或是 diverse 的结果。

因此增加召回时控制 diverse 的项，其中 g(i, j)是 diverse 函数，比如可以取

### 测试结果和指标

使用 Diversity@N 来衡量召回的多样性

## 阿里 SINE 2021 WSDM

Sparse-Interest Network for Sequential Recommendation

根据历史行为数据，对每个用户从原型池中激活不同原型作为用户兴趣，通过计算两个方面权

重：1. 用户历史行为在原型中占比，2. 用户历史行为属于每个激活的原型的比例，来获得对应各

个原型的兴趣向量。通过 self-attention 计算用户预测兴趣，并对各个原型兴趣向量加权获得最终

的用户向量。

### 优点：

1. 不需要聚合多个向量的召回结果，不存在训练时已知目标 item，用目标 item 与多个向量

softmax 选择其中一个，而 serving 时未知的偏差

### 缺点：

1. 网络结构复杂度*3 的情况下，效果没有很大的提升

2. 多样性方面没有评估，最后得到的是一个加权后的兴趣向量，而非多个向量，多样性能否

得到保障存疑

网络结构与算法

### Sparse-interest module

总的兴趣原型 L 个，激活 K 个

1. Concept Activation

self-attention 计算商品向量权重，并得到表示用户兴趣的加权向量

得到该用户激活的 topK 个兴趣原型

2. 计算第 t 个用户行为属于第 k 个兴趣原型的概率

3. 针对兴趣 k，item t 的重要程度

4. 对每个激活的原型生成兴趣向量

sum(属于第 k 个原型的概率*在兴趣 k 中的重要程度*原始 embedding)

### Interest aggregation module

兴趣向量的选择

方案一：将目标 item 用来与多个兴趣计算 attention，取其中一个作为该条记录的兴趣向量，比

如 ComiRec 里。

缺点是 inference 的时候没有目标 item 的，与训练时不一致，需要额外的 aggregation

模块来聚合召回结果。

方案二：用户历史行为预测下一个感兴趣的意图

，其中 P 矩阵是   ，属于第 k 个原型的 item 权重*原型向量，通过

self-attention 层得到预测的兴趣向量

计算聚合的权重，计算哪个原型和预测的兴趣向量更接近

最终的用户兴趣向量表示为多个兴趣向量的加权和

### 离线评估

## 微软 Octopus 2020 SIGIR

Octopus: Comprehensive and Elastic User Representation for the Generation of

Recommendation Candidates

解决的问题：

1. 不同用户兴趣方向数量不同

2. 兴趣不纯净，比如衣服方向的行为也会影响到手机方向

### 优点：

灵活性：可以部署大量通道，但是只有用户行为相关的通道会被激活

-   减少不相关的表示，减少无效计算。

纯净性：一类 user behavior 只会激活一个通道，通道内只有一类兴趣

-   避免将多种兴趣的 user behavior 混合，每个兴趣向量都有更明确的方向。

### 缺点：

1. 聚合多个向量结果时，额外训练了一个模型决定每个向量的 quota，增大线上 serving 开

销

2. 不同用户兴趣数量不同，会导致线上检索的时候计算资源难以评估

### 网络结构和算法

1. 初始化 grouping head Hg：item 表示空间的正交基底，保证通道间的正交性

2. 计算用户历史行为和各个通道的相关性，ATT 使用向量相乘

3. 对每个用户行为计算属于哪个通道

4. 将属于同一通道的用户行为向量 aggregation

5. 选取与 label 最近的一个 interest 向量作为该 interest 向量的 label

6. 计算 interest 向量与 label 之间的距离

，loss 为

### serving 多兴趣召回候选集集成

1. 从各个兴趣召回 TopK，根据与兴趣向量的距离整体排序，并选取前 N 个；

2. 从各个兴趣召回固定 quota k，但是平均分配显然是不合理的，因此设计一个网络去获得每个

兴趣向量的 quota（与兴趣向量的训练不耦合）

1. 计算兴趣向量的使用率

2. 计算对每个正样本使用哪个兴趣向量

3. 以 y 为 label，r 为 pred，交叉熵损失函数训练网络。

4. 为每个兴趣向量分配 quota，当 r 越大，该兴趣向量使用率越高，应该分配的 quota 越多。

alpha 越大，越倾向于兴趣最相近的向量召回越多，alpha 越小，越倾向于平均分配。

实验结果

第二种 quota 分配方式效果好很多。

Orth: channel 正交的正则项

Group: 同通道激活的视为一个组

OCT(C): 全局 score 排序取 topK

OCT(A): 模型决定 quota

## 微软 REMI 2023 RecSys

Rethinking Multi-Interest Learning for Candidate Matching in Recommender Systems

### 解决的问题

1. sampled softmax 会带来更严重的简单样本问题

2. 采用动态路由或者 attention 会造成路由崩溃的问题，一个兴趣只由一个特别重要的 item 决定

### IHN (interest-aware negative mining)

### Idea sampling distribution

1. 容易被选中的兴趣向量误分类的 item

2. 负样本的难度是可调节的（负样本多少最好，取决于数据量和模型复杂程度）

### 采样分布

样本选择的概率分布，正比于选中的兴趣向量与 item 向量的内积。

其中，     是选中的兴趣向量，            是负样本 item 向量， 是调节负样本难度的系数，当 大的时候，即使兴趣向量和 item 向量内积比较小，也能有比较大的概率选中负样本，负样本简单，当小的时候，只有内积比较大才能选中负样本，负样本难。实际上是从 batch 中选择样本，batch 中的样本是从样本库中均匀分布选择出来的，用蒙特卡洛重要性采样方法从均匀分布中进行采样：

### RR (routing regularization)

本文认为路由崩溃是因为 attention 权重矩阵 A 过于稀疏导致，因此在权重矩阵上增加了方差正则来消除影响

### 评估结果

不同采样方式

消融实验

## PinnerSage 2020 KDD

PinnerSage: Multi-Modal User Embedding Framework for Recommendations at Pinterest.pdf

对用户历史兴趣进行聚类，计算类的表示向量，并根据类重要性，选出重要的类用于召回候选。

### 优点：

1. 避免出现不相关 badcase 候选

2. 可解释性强

### 缺点：

2

1. 当历史行为很多时，计算复杂度大大增加，O(𝑛 )

2. 当历史行为有多种类型时，难以应用，比如既有 item 又有 query。

3. 依赖兴趣空间的学习算法

### 组成部分

1. 将用户近 90 天的行为数据聚类

2. 为每个类计算一个 medoid 方法的向量表示

3. 对每个用户的每个类计算一个重要性分数

### 1. 用户行为聚类

对用户行为聚类有两个限制：

-   类是由相似的 pins(兴趣)组成的

-   类的数量根据用户兴趣数量自动决定

为了满足上述两个限制，采用 Ward 层次聚类算法，根据最小化类方差层次聚类，参考

https://blog.csdn.net/turkeym4/article/details/103150759

初始时每个历史行为 pins 都是一个类，每次两个合并后方差最小的类合并为一个类，计算复杂度2为 O(𝑛 )。在计算合并后的类与其他类之间的方差时，使用 Lance-Williams 算法来优化效率

### 2. Medoid based Cluster Representation

采用模型获得类的中心向量缺点在于，如果类有异常值，得到的中心向量在向量空间可能与类在不同的区域，会导致召回完全不相关的候选。因此采用 medoid 方法生成类的表示，选择类中使其他 pins 距离该 pin 的方差最小的 pin 作为类的表示

这种方式还有一个优势是，只需要存储 pin 的 index，embedding 可以用 k-v 存储来查询。（没懂）

### 3. Cluster Importance

每个用户的兴趣类很多，无法每个去 ANN 检索，因此需要用重要性权重来筛选类，使用时间衰减的重要性权重

### 离线评估

## 美团 DAT 2021 DLP-KDD

A Dual Augmented Two-tower Model for Online Large-scale Recommendation

### 解决的问题

1. 双塔之间没有交叉信息的问题

2. category 不平衡，数据量少的 category 效果差的问题

### 模型结构

### DAT

使用 query 和 item_id 生成辅助向量 au 和 av，并与其他特征拼接。

### mimic loss

正样本中，au 和 pv 计算 mean square error

在计算 mimic loss 的时候，需要对双塔网络 stop_gradient，只更新 au 和 av。

### Category Alignment Loss

解决类别较少的 category 效果差的问题。数据量最多的 category 的 pv 作为 major，计算与其他 category 之间的协方差之差的第二范数。

### Loss

交叉熵损失

### 参数选择

au 和 av 都是 32 维向量

和    为 0.5，   为1

### 效果

爱奇艺多兴趣召回优化

https://www.6aiq.com/article/1621123836297

使用 attention 隐式提取多个兴趣向量，多 embedding 召回。

### 解决的问题

1. 通过在损失函数中加上兴趣 embedding 正则项的方式解决召回结果重复度较高的问题。

正则项

2. 增加激活兴趣记录表，在 serving/evaluation 的时候回溯该表，去掉用户激活较少的兴

趣，实现兴趣动态化。

3. 增加多模态特征，提升召回效果。
