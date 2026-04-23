---
title: 策略梯度、TRPO、PPO
subtitle: 从 vanilla policy gradient 到 trust region 与 clipped objective
section: papers
section_label: 论文解读
group: reinforcement-learning
summary: 把策略梯度的基本推导、TRPO 的 trust region 思路和 PPO 的两种简化形式串起来。
tags: [reinforcement-learning,policy-gradient,trpo,ppo]
---

强化学习的核心目标，是找到一个最优策略，使智能体在与环境交互的过程中获得的累积奖励期望最大。把策略参数化，再用梯度上升去优化目标函数，就是策略梯度方法的起点；TRPO 和 PPO 则是在这个基础上，继续解决“怎么更新得更稳”的问题。

## 策略梯度

### 目标函数

将策略参数化之后，强化学习的目标可以写成对策略参数 $\theta$ 的优化问题。原文从状态价值函数出发，把目标写成“初始状态价值的期望”。

在推导里，一个关键中间量是折扣访问频率：

$$
\mu(x)=\sum_{k=0}^{\infty}\gamma^k \Pr(s \to x, k, \pi_\theta)
$$

它表示从当前状态出发，后续访问到状态 $x$ 的折扣累计权重。

### 梯度推导

状态价值函数的梯度可以整理成：

$$
\nabla_\theta V^{\pi_\theta}(s)=\sum_{x\in S}\mu(x)\phi(x)
$$

其中，$\phi(x)$ 表示策略发生微小变化时，状态 $x$ 下期望动作价值的变化率。原文强调，这个式子可以理解成：优化策略参数时，本质上是在给每个状态的直接梯度赋予一个重要性权重，再做加权求和。

接着用恒等式

$$
\nabla x = x \nabla \ln x
$$

把动作概率的梯度改写成更适合采样的形式：

$$
\phi(s)=\sum_a \nabla_\theta \pi_\theta(a|s)Q^{\pi_\theta}(s,a)
=\sum_a \pi_\theta(a|s)\nabla_\theta \ln \pi_\theta(a|s)Q^{\pi_\theta}(s,a)
$$

这样就不再需要遍历所有动作，而是可以直接按当前策略去采样动作，再用采样到的奖励来估计更新方向。

### 最终更新公式

原文把策略梯度最终化简成：

$$
\nabla_\theta J(\theta)=\mathbb{E}_{s\sim \mu,\; a\sim \pi}\left[Q^\pi(s,a)\nabla_\theta \ln \pi(a|s,\theta)\right]
$$

在代码实现里，通常再用实际观测到的回报 $G_t$ 去替代 $Q^\pi(s,a)$，得到参数更新公式：

$$
\theta \leftarrow \theta + \alpha G_t \nabla_\theta \ln \pi(A_t|S_t,\theta)
$$

## TRPO

### 为什么要从策略梯度走到 TRPO

原文指出，策略梯度至少有两个直接问题：

- 步长难以确定。更新过大，可能把智能体带进完全未知的状态空间，使数据质量明显下降。
- 无法保证单调提升。策略梯度本质上是局部一阶近似，一旦参数更新后状态访问分布发生明显变化，就不能保证新策略一定更好。

TRPO（Trust Region Policy Optimization）就是在这个背景下提出的：它希望通过对“策略变化幅度”施加约束，让每一步更新都更稳。

### 性能差异恒等式

TRPO 推导里最核心的一步，是用性能差异恒等式来比较新旧策略：

$$
\eta(\tilde{\pi})=\eta(\pi)+\mathbb{E}_{s_0,a_0,\dots \sim \tilde{\pi}}\left[\sum_{t=0}^{\infty}\gamma^t A_\pi(s_t,a_t)\right]
$$

其中，

$$
A_\pi(s,a)=Q_\pi(s,a)-V_\pi(s)
$$

表示优势函数，也就是“当前动作比该状态下平均动作好多少”。

原文进一步引入折扣状态访问分布：

$$
\rho_{\tilde{\pi}}(s)=(1-\gamma)\sum_{t=0}^{\infty}\gamma^t P(S_t=s \mid \tilde{\pi})
$$

把性能差异恒等式整理成更适合优化的形式：

$$
\eta(\tilde{\pi})=\eta(\pi)+\sum_s \rho_{\tilde{\pi}}(s)\sum_a \tilde{\pi}(a|s)A_\pi(s,a)
$$

### Trust Region 目标

由于直接优化新策略时，状态访问分布也会跟着变化，TRPO 用旧策略的状态分布来近似，得到 surrogate objective：

$$
L_\pi(\tilde{\pi})=\eta(\pi)+\sum_s \rho_\pi(s)\sum_a \tilde{\pi}(a|s)A_\pi(s,a)
$$

然后再利用 KL 散度给出下界：

$$
\eta(\tilde{\pi}) \ge L_\pi(\tilde{\pi}) - C D_{KL}^{\max}(\pi,\tilde{\pi})
$$

只要右边增大，就能保证新策略的期望收益提升。于是 TRPO 最终把问题写成一个带约束优化：

$$
\underset{\theta}{\text{maximize}} \quad L_{\theta_{old}}(\theta)
\qquad
\text{subject to} \quad \bar{D}_{KL}^{\rho_{\theta_{old}}}(\theta_{old}, \theta)\le \delta
$$

### 近似求解

原文最后把目标函数做一阶展开、约束做二阶展开，把问题近似成一个二次约束优化。根据 KKT 条件，可以得到更新方向：

$$
\theta_{k+1}=\theta_k+\sqrt{\frac{2\delta}{g^T H^{-1}g}}H^{-1}g
$$

其中 $g$ 是目标函数的一阶梯度，$H$ 是 KL 散度的二阶项近似。也正因为这里要处理 Hessian 相关量，TRPO 的计算会更重。

## PPO

### 从 TRPO 到 PPO

原文对 PPO 的切入点非常直接：TRPO 虽然稳，但计算复杂。

- 它需要处理带不等式约束的拉格朗日问题。
- 参数更新和 Hessian 有关。
- 实际实现里常常还要配合共轭梯度和线性搜索。

PPO（Proximal Policy Optimization）保留了“不要让新旧策略差太远”的思想，但用更简单的方式来近似求解。原文把 PPO 分成两类：`PPO-惩罚` 和 `PPO-截断`。

### PPO-惩罚

PPO-惩罚的思路是：不再把 KL 散度写成硬约束，而是作为惩罚项直接放进目标函数里，再用启发式方式去动态调整惩罚系数。原文强调，关键不在于精确求解拉格朗日乘子，而在于根据 KL 的大小自适应调整强弱：

- 当 KL 较小时，约束可以弱一些，让模型收敛更快；
- 当 KL 较大时，约束就要更强，避免策略更新过猛。

### PPO-截断

PPO-截断是更常见的写法。它直接裁剪重要性采样比值：

$$
\arg\max_{\theta}\;
\mathbb{E}_{s\sim \nu^{\pi_{\theta_k}},\; a\sim \pi_{\theta_k}(\cdot|s)}
\left[
\min\left(
\frac{\pi_{\theta}(a|s)}{\pi_{\theta_k}(a|s)}A^{\pi_{\theta_k}}(s,a),
\operatorname{clip}\left(
\frac{\pi_{\theta}(a|s)}{\pi_{\theta_k}(a|s)},
1-\epsilon,\,
1+\epsilon
\right)A^{\pi_{\theta_k}}(s,a)
\right)
\right]
$$

原文对这个目标的解释也很直观：

- 当 $A>0$ 时，如果概率比值已经超过 $1+\epsilon$，就不再继续放大；
- 当 $A<0$ 时，如果概率比值已经低于 $1-\epsilon$，就不再继续减小。

这样做的目的，就是让新策略不要偏离旧策略过远。

### 实现要点

原文给了 PPO-截断的代码实现。整理成流程，主要有四步：

1. 用当前策略对状态采样动作，并记录旧策略下该动作的概率；
2. 用 reward 和 value 计算 advantage 与 target value；
3. 反复若干个 epoch，用新旧动作概率之比构造 clipped objective，更新 policy network；
4. 同时更新 value network。

文中还特别提到，`value model` 和 `policy model` 往往共享底层网络，只在输出层分开：

- value model 输出标量价值；
- policy model 输出动作概率分布。

## 总结

这三部分可以看成一条连续的演化链：

- 策略梯度给出了最基本的优化方向；
- TRPO 引入 trust region，用 KL 约束换取更稳定的性能提升；
- PPO 则在保留“更新不要太激进”这一思想的同时，把训练过程改得更简单、更实用。

如果只抓主线，原文其实讲得很清楚：从策略梯度到 TRPO，再到 PPO，核心一直都不是“换了一个完全不同的目标”，而是“如何在保证收益提升的前提下，让策略更新更稳定、更可实现”。
