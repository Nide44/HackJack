class Hand:
    def __init__(self, cards):
        self.cards = cards
        self.insured = False
        self.status = "P" 
        # P: Playing, N: Natural
        # NW: Natural Win, NT: Natural Tie, 
        # RW: Regular Win, RT: Regular Tie, 
        # L: Regular Loss

    def try_to_switch_soft_hand(self):
        for card in self.cards:
            if card.value == "A" and card.play_value == 11:
                card.play_value = 1
                return True     
        return False
    
    def calculate_total_value(self):
        return sum([card.play_value for card in self.cards])