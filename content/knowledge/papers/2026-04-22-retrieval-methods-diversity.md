---
title: 召回方法整理：双塔召回多样性
subtitle: MIND、ComiRec、SINE、Octopus、REMI、PinnerSage、DAT、爱奇艺多兴趣优化
section: papers
section_label: 论文解读
summary: 整理召回方法文档中“双塔召回多样性”部分的论文与笔记内容，并按论文笔记结构重新整理排版。
tags: [recsys,retrieval,multi-interest]
---

## 阿里 MIND 2019 CIKM

> Multi-Interest Network with Dynamic Routing for Recommendation at Tmall

### 解决的问题

用多个向量表示用户的多种兴趣，采用动态路由算法将历史商品聚合成多个集合，每个集合对应用户特定兴趣的向量表示。

### 缺点

- 结构复杂，计算开销大。

### 胶囊网络与动态路由算法

- 胶囊网络与神经元类似，区别是胶囊网络输入的是多个向量。
- `c` 通过动态路由算法计算，对线性变换后的输入向量 `u` 加权。
- 动态路由算法在每一步迭代中，会向与输出向量 `a` 更接近的输入向量 `u` 靠近；更接近的 `a` 和 `u` 内积更大，因此在下一步中 softmax 权重更大，本质上接近聚类。
- Squashing 保证向量方向不变，模大于 0 小于 1；`s` 的模越大越接近 1，越小越接近 0，作用上类似 sigmoid。

### 模型结构

- 模型目的是将特征映射到用户表达；当 `V` 为一维向量时，类似 YouTubeDNN。
- Embedding 和 Pooling 层：others features 是用户基础特征（age、gender、id 等拼接），item `N` 是用户历史行为的 item 特征，label 是目标商品特征（brand_id、shop_id 等，对冷启有效，通过 average pooling 构建 item 向量）。
- Multi-Interest Extractor 层：通过动态路由算法计算用户兴趣向量。
  1. 采用 shared 线性变换矩阵（上文中的 `W`，不同 item 的 `W` 相同）。
  2. 高斯分布随机初始化 routing logits（`b`），这样可以获得不同兴趣向量，否则每个兴趣向量最后都会收敛到最感兴趣的那个方向。
  3. 对不同用户采用动态的兴趣数量。
- Label-Aware Attention 层：interest capsule 的权重取决于与目标 item 的兼容性。

### 超参数与结果

- Initialization of routing logits `b`：`N(0, 1)` 在 `epoch = 1` 时效果最好；随着 epoch 增加，与 `N(0, 0.1)`、`N(0, 5)` 逐渐接近。
- power number `p` in label-aware attention：`p = 0` 效果最差，相当于每个 interest capsule 都有相同权重；`p` 越大效果越好。
- online 效果：动态 embedding 个数比 `k = 7` 微涨，涨幅不大。

### 参考链接

- <https://github.com/shenweichen/DeepMatch/blob/master/deepmatch/models/mind.py>
- <https://zhuanlan.zhihu.com/p/145283113>

## 阿里 ComiRec 2020 KDD

> Controllable Multi-Interest Framework for Recommendation

用 self-attention 层来隐式提取多个用户兴趣向量，并在 serving 时增加召回结果集成模块，平衡多样性和精确度。

### 优点

1. 隐式地学习用户多个兴趣向量，能够适应数据分布变化。
2. 在 serving 时增加集成模块，平衡多样性和精确度。

### 缺点

1. 用户兴趣数量固定，设置兴趣数量对结果影响较大；对兴趣单一的用户，效果可能不如单兴趣模型。
2. 召回结果重复度较高、特征较少、即时性差。

### 模型结构

#### Multi-interest Module

1. Dynamic Routing
   和 MIND 相同。
2. Self-Attention Layer
   其中 `H` 是 user behavior embedding，每一个历史行为都可能影响每一个 embedding。

#### Model Training

目标 item embedding 会选出一个 user behavior embedding，用选出的 embedding 来计算 loss。

#### Aggregation Module

用于在 serving 时，得到多个 interest embedding 后，获得整体的 top-N item。

- 基本做法是从候选集中选出每个兴趣向量最相近的 `K` 个 item。
- 但原笔记认为这并不是最好的做法，因为用户更倾向被推荐新的、或者更 diverse 的结果。
- 因此在召回阶段增加了控制 diverse 的项，其中 `g(i, j)` 是 diverse 函数。

### 测试结果和指标

- 使用 `Diversity@N` 来衡量召回的多样性。

## 阿里 SINE 2021 WSDM

> Sparse-Interest Network for Sequential Recommendation

根据历史行为数据，对每个用户从原型池中激活不同原型作为用户兴趣。通过计算两个方面的权重：

1. 用户历史行为在原型中占比；
2. 用户历史行为属于每个激活原型的比例；

来获得各个原型的兴趣向量。随后通过 self-attention 计算用户预测兴趣，并对各个原型兴趣向量加权，得到最终用户向量。

### 优点

1. 不需要聚合多个向量的召回结果，不存在训练时已知目标 item、用目标 item 在多个向量中 softmax 选一个，而 serving 时未知目标 item 所带来的偏差。

### 缺点

1. 网络结构复杂度提升到 3 倍左右的情况下，效果没有很大提升。
2. 多样性方面没有评估；最后得到的是一个加权后的兴趣向量，而非多个向量，多样性能否得到保障存疑。

### 网络结构与算法

#### Sparse-interest Module

总兴趣原型有 `L` 个，激活 `K` 个。

1. Concept Activation
   - 通过 self-attention 计算商品向量权重，并得到表示用户兴趣的加权向量。
   - 得到该用户激活的 topK 个兴趣原型。
2. 计算第 `t` 个用户行为属于第 `k` 个兴趣原型的概率。
3. 计算在兴趣 `k` 下 item `t` 的重要程度。
4. 对每个激活的原型生成兴趣向量：
   `sum(属于第 k 个原型的概率 * 在兴趣 k 中的重要程度 * 原始 embedding)`。

#### Interest Aggregation Module

兴趣向量选择有两种思路：

1. 将目标 item 与多个兴趣向量计算 attention，选其中一个作为该条记录的兴趣向量，例如 ComiRec。
   缺点是 inference 时没有目标 item，与训练阶段不一致，因此需要额外 aggregation module 来聚合召回结果。
2. 用用户历史行为预测下一个感兴趣的意图，再通过 self-attention 得到预测兴趣向量，计算聚合权重，判断哪个原型与预测兴趣更接近。

最终的用户兴趣向量表示为多个兴趣向量的加权和。

## 微软 Octopus 2020 SIGIR

> Octopus: Comprehensive and Elastic User Representation for the Generation of Recommendation Candidates

### 解决的问题

1. 不同用户兴趣方向数量不同。
2. 兴趣不纯净，例如衣服方向的行为也会影响手机方向。

### 优点

- 灵活性：可以部署大量通道，但只有用户行为相关的通道会被激活，从而减少不相关表示和无效计算。
- 纯净性：一类 user behavior 只会激活一个通道，通道内只有一类兴趣，避免将多种兴趣混合在同一个兴趣向量里。

### 缺点

1. 聚合多个向量结果时，需要额外训练一个模型决定每个向量的 quota，增大线上 serving 开销。
2. 不同用户兴趣数量不同，会导致线上检索时计算资源难以评估。

### 网络结构和算法

1. 初始化 grouping head `Hg`：使用 item 表示空间的正交基底，保证通道间正交性。
2. 计算用户历史行为与各个通道的相关性，ATT 使用向量相乘。
3. 对每个用户行为计算其属于哪个通道。
4. 将属于同一通道的用户行为向量做 aggregation。
5. 选取与 label 最近的一个 interest 向量作为该 interest 向量的 label。
6. 计算 interest 向量与 label 之间的距离，并构造对应 loss。

### Serving：多兴趣召回候选集集成

1. 从各个兴趣向量召回 TopK，根据与兴趣向量的距离整体排序，并选取前 `N` 个。
2. 从各个兴趣向量召回固定 quota `k`；但平均分配显然不合理，因此另外设计网络去学习每个兴趣向量的 quota（与兴趣向量训练不耦合）。
   1. 计算兴趣向量的使用率。
   2. 计算每个正样本使用哪个兴趣向量。
   3. 以 `y` 为 label、`r` 为 pred，用交叉熵损失训练网络。
   4. 为每个兴趣向量分配 quota：`r` 越大，兴趣向量使用率越高，应该分配的 quota 越多。

原笔记的结论是：

- `alpha` 越大，越倾向让兴趣最相近的向量召回更多；
- `alpha` 越小，越倾向平均分配；
- 第二种 quota 分配方式效果明显更好。

实验缩写说明：

- `Orth`：channel 正交的正则项。
- `Group`：同通道激活的视为一个组。
- `OCT(C)`：全局 score 排序取 topK。
- `OCT(A)`：模型决定 quota。

## 微软 REMI 2023 RecSys

> Rethinking Multi-Interest Learning for Candidate Matching in Recommender Systems

### 解决的问题

1. sampled softmax 会带来更严重的简单样本问题。
2. 动态路由或 attention 容易造成路由崩溃，一个兴趣只由一个特别重要的 item 决定。

### IHN（interest-aware negative mining）

#### Idea sampling distribution

1. 更容易采到会让选中兴趣向量误分类的 item。
2. 负样本难度可调；负样本应该采多难，取决于数据量和模型复杂程度。

#### 采样分布

- 样本选择的概率分布正比于选中的兴趣向量与 item 向量的内积。
- 通过调节负样本难度系数来控制采样：系数大时，即使内积较小也有较大概率被采中，负样本更简单；系数小时，只有内积较大时才更容易被采中，负样本更难。
- 实际上是从 batch 中选择样本；而 batch 又是从样本库中均匀抽样出来的，因此这里使用蒙特卡洛重要性采样，从均匀分布中进行采样。

### RR（routing regularization）

本文认为路由崩溃是因为 attention 权重矩阵 `A` 过于稀疏，因此在权重矩阵上增加方差正则来消除影响。

### 评估结果

- 比较了不同采样方式。
- 做了消融实验。

## PinnerSage 2020 KDD

> PinnerSage: Multi-Modal User Embedding Framework for Recommendations at Pinterest

对用户历史兴趣进行聚类，计算类的表示向量，并根据类重要性选出重要的类，用于召回候选。

### 优点

1. 避免出现不相关 badcase 候选。
2. 可解释性强。

### 缺点

1. 当历史行为很多时，计算复杂度大幅增加，为 `O(n^2)`。
2. 当历史行为有多种类型时难以应用，例如既有 item 又有 query。
3. 依赖兴趣空间的学习算法。

### 组成部分

1. 将用户近 90 天的行为数据聚类。
2. 为每个类计算一个 medoid 方法的向量表示。
3. 对每个用户的每个类计算重要性分数。

### 1. 用户行为聚类

对用户行为聚类有两个限制：

- 类由相似的 pins（兴趣）组成。
- 类的数量需要根据用户兴趣数量自动决定。

为了满足上述两个限制，采用 Ward 层次聚类算法，根据最小化类方差来做层次聚类。

参考链接：

- <https://blog.csdn.net/turkeym4/article/details/103150759>

初始化时，每个历史行为 pin 都是一个类；每次选择两个合并后方差最小的类进行合并，计算复杂度为 `O(n^2)`。在计算合并后类与其他类之间的方差时，使用 Lance-Williams 算法优化效率。

### 2. Medoid based Cluster Representation

如果直接用模型学习类中心向量，类中一旦存在异常值，得到的中心向量在向量空间里可能落在类之外，导致召回完全不相关的候选。因此这里采用 medoid 方法生成类表示：选择类中使其他 pins 到该 pin 距离方差最小的那个 pin 作为类表示。

原笔记里的补充是：这种方式还有一个优势，只需要存储 pin 的 index，embedding 可以通过 k-v 存储查询。

### 3. Cluster Importance

每个用户的兴趣类很多，无法每个都去做 ANN 检索，因此需要用重要性权重筛选类；这里使用时间衰减的重要性权重。

## 美团 DAT 2021 DLP-KDD

> A Dual Augmented Two-tower Model for Online Large-scale Recommendation

### 解决的问题

1. 双塔之间没有交叉信息。
2. category 不平衡，数据量少的 category 效果较差。

### 模型结构

#### DAT

使用 query 和 item_id 生成辅助向量 `au` 和 `av`，并与其他特征拼接。

#### mimic loss

- 正样本中，`au` 和 `pv` 计算 mean square error。
- 计算 mimic loss 时，需要对双塔网络 `stop_gradient`，只更新 `au` 和 `av`。

#### Category Alignment Loss

解决类别较少的 category 效果差的问题。具体做法是：以数据量最多的 category 的 `pv` 作为 major，计算它与其他 category 协方差之差的二范数。

#### Loss

- 交叉熵损失。

#### 参数选择

- `au` 和 `av` 都是 32 维向量。
- 原笔记里记录了若干权重系数，其中部分取 `0.5`，另一个取 `1`。

## 爱奇艺多兴趣召回优化

参考链接：

- <https://www.6aiq.com/article/1621123836297>

使用 attention 隐式提取多个兴趣向量，多 embedding 召回。

### 解决的问题

1. 通过在损失函数中增加兴趣 embedding 正则项，解决召回结果重复度较高的问题。
2. 增加激活兴趣记录表，在 serving / evaluation 时回溯该表，去掉用户激活较少的兴趣，实现兴趣动态化。
3. 增加多模态特征，提升召回效果。
