import collections

class MovesGener(object):
    """
    This is for generating the possible combinations
    """
    def __init__(self, cards_list, choose_1_2, choose_2_2):
        self.stash_1 = None
        self.trash_2 = None
        self.choose_1_2 = None
        self.choose_2_2 = None
        self.resolve_1_2 = None
        self.resolve_2_2 = None

        if choose_2_2:
            self.resolve_2_2 = [[[], []], [[], []]]
            self.resolve_2_2[0][0] = choose_2_2[0]
            self.resolve_2_2[0][1] = choose_2_2[1]
            self.resolve_2_2[1][0] = choose_2_2[1]
            self.resolve_2_2[1][1] = choose_2_2[0]
            return

        if choose_1_2:
            self.resolve_1_2 = []
            for i, val in enumerate(choose_1_2):
                if val != 0:
                    a = [0] * 7
                    b = choose_1_2[:]
                    a[i] = 1
                    b[i] -= 1
                    self.resolve_1_2.append([a, b])
            return



        self.cards_list = cards_list
        self.cards_dict = collections.defaultdict(int)

        for i in self.cards_list:
            self.cards_dict[i] += 1

    # generate all possible moves from given cards
    def gen_moves(self):
        moves = []
        moves.extend(self.gen_type_1_single())
        moves.extend(self.gen_type_2_pair())
        moves.extend(self.gen_type_3_triple())
        moves.extend(self.gen_type_4_bomb())
        moves.extend(self.gen_type_5_king_bomb())
        moves.extend(self.gen_type_6_3_1())
        moves.extend(self.gen_type_7_3_2())
        moves.extend(self.gen_type_8_serial_single())
        moves.extend(self.gen_type_9_serial_pair())
        moves.extend(self.gen_type_10_serial_triple())
        moves.extend(self.gen_type_11_serial_3_1())
        moves.extend(self.gen_type_12_serial_3_2())
        moves.extend(self.gen_type_13_4_2())
        moves.extend(self.gen_type_14_4_22())
        return moves
