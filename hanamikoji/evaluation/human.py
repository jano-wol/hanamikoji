def card_list_to_inner(l):
    ret = [0] * 7
    for c in l:
        ret[c - 1] += 1
    return ret


def inner_to_card_list(inner):
    ret = []
    for i, val in enumerate(inner):
        while val > 0:
            ret.append(i + 1)
            val -= 1
    return ret


def _sub_cards(a, b):
    return [a - b for a, b in zip(a, b)]


class Human:
    def __init__(self):
        pass

    def __str__(self):
        return "Human"

    def parse_move_1_2(self):
        expected_length = 3
        while True:
            hand_str = input(f"Enter the 3 human cards ({expected_length} digits, each 1–7): ").strip()
            if len(hand_str) != expected_length or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly {expected_length} digits.")
                continue
            hand = [int(c) for c in hand_str]
            if all(1 <= card <= 7 for card in hand):
                return hand
            print("Invalid card values. All digits must be between 1 and 7.")

    def parse_move_2_2_a(self):
        expected_length = 2
        while True:
            hand_str = input(f"Enter the 2 human cards ({expected_length} digits, each 1–7): ").strip()
            if len(hand_str) != expected_length or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly {expected_length} digits.")
                continue
            hand = [int(c) for c in hand_str]
            if all(1 <= card <= 7 for card in hand):
                return hand
            print("Invalid card values. All digits must be between 1 and 7.")

    def parse_move_2_2_b(self):
        expected_length = 2
        while True:
            hand_str = input(f"Enter the other 2 human cards ({expected_length} digits, each 1–7): ").strip()
            if len(hand_str) != expected_length or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly {expected_length} digits.")
                continue
            hand = [int(c) for c in hand_str]
            if all(1 <= card <= 7 for card in hand):
                return hand
            print("Invalid card values. All digits must be between 1 and 7.")

    def parse_action_type(self):
        while True:
            hand_str = input(f"Provide action type. Possible values 1–4: ").strip()
            if len(hand_str) != 1 or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly 1 digits.")
                continue
            if 1 <= int(hand_str) <= 4:
                return int(hand_str)
            print("Invalid action type. Please enter a digit between 1 and 4.")

    def parse_1_2_resolve(self):
        while True:
            hand_str = input(f"Provide the card human would like to get. Possible values 1–7: ").strip()
            if len(hand_str) != 1 or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly 1 digits.")
                continue
            if 1 <= int(hand_str) <= 7:
                return int(hand_str)
            print("Invalid action type. Please enter a digit between 1 and 7.")

    def parse_2_2_resolve(self):
        while True:
            hand_str = input(f"Provide the cards index human would like to get. Possible values 1–2: ").strip()
            if len(hand_str) != 1 or not hand_str.isdigit():
                print(f"Invalid input. Please enter exactly 1 digits.")
                continue
            if 1 <= int(hand_str) <= 2:
                return int(hand_str)
            print("Invalid action type. Please enter digit 1 or 2.")

    def act(self, infoset):
        if infoset[0].decision_cards_1_2 is not None:
            print(f'Resolve 1_2. cards={inner_to_card_list(infoset[0].decision_cards_1_2)}')
            g = self.parse_1_2_resolve()
            h = [0] * 7
            h[g - 1] = 1
            assert infoset[0].decision_cards_1_2[g - 1] > 0
            return [4, [h, _sub_cards(infoset[0].decision_cards_1_2, h)]]
        if infoset[0].decision_cards_2_2 is not None:
            print(
                f'Resolve 2_2. cards1={inner_to_card_list(infoset[0].decision_cards_2_2[0])} cards2={inner_to_card_list(infoset[0].decision_cards_2_2[1])}')
            g = self.parse_2_2_resolve()
            if g == 1:
                return [5, [infoset[0].decision_cards_2_2[0], infoset[0].decision_cards_2_2[1]]]
            else:
                return [5, [infoset[0].decision_cards_2_2[1], infoset[0].decision_cards_2_2[0]]]
        t = self.parse_action_type()
        t -= 1
        assert infoset[0].action_cards[infoset[0].acting_player_id][t] == 1
        if t == 0:
            return [0, [0] * 7]
        if t == 1:
            return [1, [0] * 7]
        if t == 2:
            h = self.parse_move_1_2()
            return [2, card_list_to_inner(h)]
        else:
            l1 = card_list_to_inner(self.parse_move_2_2_a())
            l2 = card_list_to_inner(self.parse_move_2_2_b())
            if l1 < l2:
                return [3, [l1, l2]]
            else:
                return [3, [l2, l1]]
