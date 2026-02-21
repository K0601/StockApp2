import torch
import numpy as np
from models.actor_critic import ActorCritic
from rl.ppo import PPO


def train_model(env, input_dim, episodes=50, device="cpu", progress_callback=None):

    episode_rewards = []

    model = ActorCritic(input_dim).to(device)
    agent = PPO(model)

    for ep in range(episodes):

        state = torch.tensor(env.reset(), dtype=torch.float32).to(device)
        done = False
        total_reward = 0

        states = []
        actions = []
        rewards = []
        log_probs = []
        values = []
        dones = []

        while not done:
            

            action, log_prob, value = model.get_action(state)

            next_state, reward, done = env.step(action.item())

            states.append(state)
            actions.append(action)
            rewards.append(reward)
            log_probs.append(log_prob)
            values.append(value.squeeze())
            dones.append(done)

            total_reward += reward

            state = torch.tensor(next_state, dtype=torch.float32).to(device)

        # ===== 最終状態のValue =====
        with torch.no_grad():
            _, last_value = model.forward(state)

        values.append(last_value.squeeze())

        # ===== Tensor化（ここで1回だけ）
        values = torch.stack(values).to(device)

        # ===== GAE計算 =====
        advantages = agent.compute_gae(rewards, values, dones)

        # compute_gae が Tensor を返す前提ならこれだけでOK
        advantages = advantages.to(device)

        # ★ stack不要
        returns = advantages + values[:-1].detach()

        states = torch.stack(states)
        actions = torch.stack(actions)
        log_probs = torch.stack(log_probs)

        # ===== PPO更新 =====
        agent.update(
            states,
            actions,
            log_probs,
            returns.detach(),
            advantages.detach()
        )

        episode_rewards.append(total_reward)

        # リアルタイム更新
        if progress_callback:
            progress_callback(ep + 1, episodes, total_reward)

        print(f"Episode {ep+1}/{episodes} | Reward: {total_reward:.4f}")

    return model, episode_rewards

