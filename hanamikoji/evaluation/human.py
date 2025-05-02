import os
import time

class Human:
    def __init__(self, human_in, poll_interval):
        self.human_in = human_in
        self.poll_interval = poll_interval
        self.last_tick = -1
        self.interrupt = None


    def act(self, infoset):
        move = 0
        assert move in infoset[1].moves
        return move


    def check_interrupt(self):
        if os.path.exists(self.human_in):
            with open(self.human_in, 'r') as f:
                response = f.read().strip()
            if response == "swap":
                self.interrupt = "swap"
                return
            if response == "reset":
                self.interrupt = "reset"
                return
        time.sleep(self.poll_interval)
        return