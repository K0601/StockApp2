import torch
import torch.nn as nn
import torch.nn.functional as F


class ActorCritic(nn.Module):
    def __init__(self, input_dim, action_dim=3, hidden_dim=128):
        super().__init__()

        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )

        # Actor (離散アクション用)
        self.policy = nn.Linear(hidden_dim, action_dim)

        # Critic
        self.value = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = self.shared(x)

        logits = self.policy(x)
        value = self.value(x)

        return logits, value

    #学習用のaction決定
    def get_action(self, state):
        logits, value = self.forward(state)

        dist = torch.distributions.Categorical(logits=logits)
        action = dist.sample()
        log_prob = dist.log_prob(action)

        return action, log_prob, value

    #テスト用のaction決定
    def act(self, state):
        if not isinstance(state, torch.Tensor):
            state = torch.FloatTensor(state)

        state = state.unsqueeze(0)

        with torch.no_grad():
            logits, _ = self.forward(state)
        #一番確率の高い行動=greedyを使うためargmax
        action = torch.argmax(logits, dim=1)

        return action.item()
