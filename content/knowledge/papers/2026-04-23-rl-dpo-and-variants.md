---
title: DPO 及变体
date: 2026-04-23 17:12:02
subtitle: DPO、IPO、Conservative DPO、SimPO
section: papers
section_label: 论文解读
group: reinforcement-learning
summary: 从 DPO 的目标函数出发，整理 IPO、Conservative DPO 和 SimPO 这几条常见变体路线。
tags: [reinforcement-learning,dpo,alignment,preference-learning]
---

从 PPO 往对齐训练继续走，会发现工程复杂度很快上来。原文的切入点是：PPO 训练里通常需要 actor、critic、reward model 和 reference model 多个模块，维护成本高，而且显式优势函数容易把 reward 的波动直接传到梯度更新里。DPO 就是在这个背景下，把“偏好优化”改写成一个更直接的目标。

## DPO

### 从 PPO 到 DPO

原文对 DPO 的动机总结得很直接：

- critic 和 reward model 都会增加训练与维护成本；
- reward 波动过大时，优势函数也会随之剧烈波动，训练不稳定；
- 如果能把优势函数吸收到目标函数里，就有机会只保留策略模型和参考模型。

因此，DPO 通过变分法重写目标，把原本显式出现的优势函数换成了一个等价的偏好优化形式。

### 损失函数

对一个偏好样本 $(x, y_w, y_l)$，其中 $y_w$ 是 preferred response，$y_l$ 是 rejected response，DPO 的目标写成：

$$
\mathcal{L}_{\text{DPO}}(\pi_{\theta}; \pi_{\text{ref}})
=-
\mathbb{E}_{(x,y_w,y_l)\sim\mathcal{D}}
\left[
\log \sigma \left(
\beta \log \frac{\pi_{\theta}(y_w \mid x)}{\pi_{\text{ref}}(y_w \mid x)}
-
\beta \log \frac{\pi_{\theta}(y_l \mid x)}{\pi_{\text{ref}}(y_l \mid x)}
\right)
\right]
$$

原文强调，旧策略的约束就体现在这个式子里的 reference model 上。reference 会减小 chosen / rejected 对数比值的差距，从而限制参数更新幅度。

### 实现要点

原文给了完整的 DPO 伪代码，流程可以整理成下面几步：

1. 计算策略模型对 `chosen` 和 `rejected` 的对数概率；
2. 计算参考模型对同样样本的对数概率；
3. 用两者的差构造相对 log ratio；
4. 对 `\beta \cdot logits` 取 `logsigmoid`，得到 DPO loss；
5. 额外监控 `chosen_rewards`、`rejected_rewards`、`reward_accuracy` 和 `reward_margin`。

原文特别提醒了一点：这里的 `labels` 不是分类标签，而是语言模型逐 token 的监督目标；计算时还要显式忽略 `-100` 的位置。

## IPO

### 要解决什么问题

IPO（Identity Preference Optimization）主要针对一个问题：当偏好数据非常确定时，DPO 容易对偏好数据过拟合。

原文的解释是，如果采样数据的偏好非常明确，等价于 $q=1$，此时 DPO 会不断拉大正负样本之间的分差，KL 正则的作用会被弱化，模型就会倾向于让：

- $\pi(y_w)$ 趋近于 $100\%$；
- $\pi(y_l)$ 趋近于 $0$。

### IPO 的做法

IPO 不再沿用 DPO 的偏好概率映射，而是采用恒等映射 $\Psi(q)=q$，让模型的分差 $h_\pi$ 直接去拟合人类偏好：

$$
h_\pi \approx q
$$

对应地，目标函数变成一个均方误差：

$$
L(h) = (h_\pi - q)^2
$$

原文进一步写出，在真实偏好概率为 $q$、模型分差为 $h$ 时，期望损失可以表示为：

$$
\mathcal{L}(h)
=
q \cdot (h - \Psi(1))^2 + (1-q)\cdot(-h-\Psi(1))^2
$$

最终得到 IPO 的训练目标：

$$
\mathcal{L}_{\rm IPO}(\theta)=
\mathbb{E}_{(y_w, y_l, x) \sim \mathcal{D}}
\left(
h_\pi - \frac{\tau^{-1}}{2}
\right)^2
$$

## Conservative DPO

### 要解决什么问题

Conservative DPO 针对的是标签噪声。DPO 默认偏好标签全都正确，但如果偏好数据里本来就有错误标注，直接按 DPO 去拉大分差，会让模型训练不稳定。

### 损失函数

原文把 Conservative DPO 的修正写成：

$$
\mathcal{L}_{\rm CDPO}(\theta)
=
-(1-\varepsilon)\log \sigma(\beta \cdot logits)
-\varepsilon \log \sigma(-\beta \cdot logits)
$$

这里的 $\varepsilon$ 表示标签出错的概率，原文给的常见范围是 `0.1-0.3`。它的效果是：不会再无限制地拉大正负样本的分差。

## SimPO

### 要解决什么问题

原文把 SimPO 的动机总结成两点：

1. DPO 更偏向更长的文本，因为 logits 是对 token 概率求和，文本越长，累积值往往越大；
2. DPO 仍然会在偏好数据上过拟合。

此外，SimPO 还是一个 `reference-free` 的方案，可以直接减少显存占用。

### 奖励定义与目标函数

SimPO 显式定义了基于平均 token log-prob 的奖励：

$$
r_\theta(y)=\frac{\beta}{L}\sum_{i=1}^{L}\log\pi_\theta(w_i|x,w_{<i})
$$

再在损失里引入一个常量 $\gamma$：

$$
\mathcal{L}_{\rm SimPO}
=
-\log \sigma \left(r_{\theta}(y_w)-r_{\theta}(y_l)-\gamma\right)
$$

原文对这个设计的解释是：当正负样本之间的差距已经大于 $\gamma$ 后，损失会逐渐趋近于零，模型不会再无止境地把两者继续拉开。

## 总结

这几条路线可以看成围绕 DPO 的三种典型修正：

- `IPO` 主要解决“偏好过于确定时的过拟合”；
- `Conservative DPO` 主要解决“偏好标签有噪声”；
- `SimPO` 主要解决“长度偏置、过拟合，以及 reference model 带来的额外开销”。

如果只抓主线，DPO 之后的这些变体，本质上都在围绕两个问题打转：

- 怎么让偏好优化更稳；
- 怎么让训练成本更低。
