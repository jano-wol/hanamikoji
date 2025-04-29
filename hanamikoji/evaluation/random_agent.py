import random

class RandomAgent:

    def __init__(self):
        self.name = 'Random'

    def act(self, infoset):
        return random.choice(infoset[1].moves)
