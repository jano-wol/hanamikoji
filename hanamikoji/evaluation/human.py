class Human:
    def __init__(self):
        pass


    def act(self, infoset):
        move = 0
        assert move in infoset[1].moves
        return move
