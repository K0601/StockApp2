import torch

class Buffer:
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.dones = []
        self.log_probs = []
        self.values = []

    def add(self, *args):
        self.states.append(args[0])
        self.actions.append(args[1])
        self.rewards.append(args[2])
        self.dones.append(args[3])
        self.log_probs.append(args[4])
        self.values.append(args[5])
