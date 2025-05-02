import os
import random
import time


def parse_move(response):
    return None, None


class Human:
    def __init__(self, human_in, poll_interval):
        self.human_in = human_in
        self.poll_interval = poll_interval
        self.last_tick = -1
        self.interrupt = None

    def act(self, infoset):
        while True:
            if os.path.exists(self.human_in):
                with open(self.human_in, 'r') as f:
                    response = f.read().strip()
                if response == "swap":
                    self.interrupt = "swap"
                    return random.choice(infoset[1].moves)
                elif response == "reset":
                    self.interrupt = "reset"
                    return random.choice(infoset[1].moves)
                else:
                    move, tick = parse_move(response)
                    if move is not None and tick is not None:
                        if tick != self.last_tick:
                            self.last_tick = tick
                            assert move in infoset[1].moves
                            return move
            time.sleep(self.poll_interval)

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
