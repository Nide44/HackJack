class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        self.visible = False # We assume that "in the deck" = invisible
        self.play_value = self.calculate_play_value(self.value)

    def __str__(self):
        return self.suit + self.value
    
    @staticmethod
    def calculate_play_value(value):
        if value == "A":
            return 11
        elif value in ["J", "Q", "K"]:
            return 10
        else:
            try:
                return int(value)
            except:
                raise Exception("Card doesn't have a valid pip value")