class Human:
    def __init__(self, human_in, poll_interval):
        self.human_in = human_in
        self.poll_interval = poll_interval


    def act(self, infoset):
        move = 0
        assert move in infoset[1].moves
        return move
