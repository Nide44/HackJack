import settings
import random, math

from card import Card

class Deck:
    suits = ["H", "C", "D", "S"]
    values = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

    def __init__(self):
        self.cards = []
        self.fill_deck()
        self.refresh_flag = False

    def fill_deck(self):
        for _ in range(settings.NB_DECKS):
            for suit in Deck.suits:
                for value in Deck.values:
                    self.cards.append(Card(suit, value))

    def shuffle_deck(self):
        random.shuffle(self.cards)

    def cut_deck(self, percentage):
        cut_index = math.floor(percentage * (len(self.cards) - 1))
        self.cards = self.cards[cut_index:] + self.cards[:cut_index]
    
    def place_blank_card(self, position):
        self.cards.insert(-position, Card("B", "0"))

    def deal_card(self, visible):
        dealt_card =  self.cards.pop()
        dealt_card.visible = visible
        if dealt_card.suit == "B":
            self.refresh_flag = True
            dealt_card =  self.cards.pop()
            dealt_card.visible = visible
        return dealt_card