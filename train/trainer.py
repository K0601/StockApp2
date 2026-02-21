import torch
from rl.buffer import Buffer
from rl.ppo import PPO

def train(env, model, episodes=10):
    agent = PPO(model)

    for ep in range(episodes):
        state = torch.tensor(env.reset(), dtype=torch.float32)
        buffer = Buffer()
        done = False

        while not done:
            logits, value = model(state)
            action = torch.tanh(logits)

            next_state, reward, done, _ = env.step(action.detach().numpy())

            buffer.add(state, action, reward, done, logits, value)
            state = torch.tensor(next_state, dtype=torch.float32)

        agent.update(buffer)
        print(f"Episode {ep} done")
