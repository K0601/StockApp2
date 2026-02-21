#Proximal Policy Optimization Algorithms 利益が出る方向に脳を少しずつ調整する装置
import torch
import torch.optim as optim


class PPO:

    def __init__(self, model, lr=3e-4,
                 gamma=0.99,
                 lam=0.95,
                 clip=0.2,
                 entropy_coef=0.01):

        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=lr)

        self.gamma = gamma
        self.lam = lam
        self.clip = clip
        self.entropy_coef = entropy_coef

    # ==========================================
    # GAE
    # ==========================================
    def compute_gae(self, rewards, values, dones):

        device = values.device

        advantages = []
        gae = 0

        for t in reversed(range(len(rewards))):

            delta = (
                rewards[t]
                + self.gamma * values[t+1] * (1 - dones[t])
                - values[t]
            )

            gae = delta + self.gamma * self.lam * (1 - dones[t]) * gae
            advantages.insert(0, gae)

        advantages = torch.stack(advantages).to(device)

        return advantages

    # ==========================================
    # PPO Update
    # ==========================================
    def update(self, states, actions, log_probs_old,
           returns, advantages):

        log_probs_old = log_probs_old.detach()
        returns = returns.detach()
        advantages = advantages.detach()

        # 安定化
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # ★ Categorical用
        actions = actions.long().squeeze()

        for _ in range(10):

            # ===== ここ変更 =====
            logits, values = self.model(states)
            dist = torch.distributions.Categorical(logits=logits)

            log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()

            ratio = torch.exp(log_probs - log_probs_old)

            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip, 1 + self.clip) * advantages

            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = (returns - values.squeeze()).pow(2).mean()

            loss = (
                actor_loss
                + 0.5 * critic_loss
                - self.entropy_coef * entropy
            )

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 0.5)
            self.optimizer.step()

