import random


class RandomAgent:

    def __init__(self):
        self.name = 'Random'

    def __str__(self):
        return "RandomAgent"

    def act(self, infoset):
        return random.choice(infoset[1].moves)
