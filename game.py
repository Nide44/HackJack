import random, math

from deck import Deck
from player import Player
from hand import Hand
from settings import NB_PLAYERS, DEF_STASH

class Game:
    def __init__(self, mode):
        self.players = [Player(f"player{i + 1}", DEF_STASH) for i in range(NB_PLAYERS)]
        self.house = Player("house")
        self.mode = mode
        self.current_bets = {player.name: 0 for player in self.players}

        self.place_bets_mapping = {
            "random": self.place_bets_random
        }
        self.decide_hit_stand_mapping = {
            "random": self.decide_hit_stand_random
        }
        self.decide_split_mapping = {
            "random": self.decide_split_random
        }

    def grab_new_deck(self):
        self.deck = Deck()

    def prepare_deck(self):
        self.deck.shuffle_deck()
        self.deck.cut_deck(random.random())
        self.deck.place_blank_card(random.randrange(60, 76))

    def place_bets(self):
        self.place_bets_mapping[self.mode]()

    def place_bets_random(self):
        for player in self.players:
            bet = round(random.uniform(2.0, min(500.0, player.stash) * 2)) / 2
            self.current_bets[player.name] = bet
            player.stash -= bet

    def perform_deal(self):
        # First card for all players
        for player in self.players:
            player.hands.append(Hand([self.deck.deal_card(True)]))

        # First card for the house
        self.house.hands.append(Hand([self.deck.deal_card(True)]))

        # Second card for all players
        for player in self.players:
            player.hands[0].cards.append(self.deck.deal_card(True))

        # Second card for the house
        self.house.hands[0].cards.append(self.deck.deal_card(False))

    def check_natural_house(self):
        if self.house.hands[0].cards[0].play_value in [10, 11]:
            if self.house.hands[0].calculate_total_value() == 21:
                self.house.hands[0].status = "N"
                return True
            
        return False

    def check_natural_players(self):
        all_players_natural = True
        for player in self.players:
            if player.hands[0].calculate_total_value() == 21:
                if self.house.hands[0].status == "N":
                    player.hands[0].status = "NT"
                else:
                    player.hands[0].status = "NW"
            else:
                all_players_natural = False
        return all_players_natural
    
    def handle_naturals(self):
        for player in self.players:
            if player.hands[0].status == "NW":
                player.stash += self.current_bets[player.name] * 2.5
            elif player.hands[0].status == "NT":
                player.stash += self.current_bets[player.name]
    
    def decide_hit_stand(self):
        return self.decide_hit_stand_mapping[self.mode]()
    
    def decide_hit_stand_random(self):
        return "H" if random.random() > 0.5 else "S"
    
    def decide_split_random(self):
        return True if random.random() > 0.5 else False
    
    def decide_split(self):
        return self.decide_split_mapping[self.mode]()

    def perform_play(self):
        # Player phase
        all_players_bust = True
        for player in self.players:
            # Option to split pairs
            if player.hands[0].cards[0].value == player.hands[0].cards[1].value:
                split = self.decide_split()
                if split:
                    player.hands.append(Hand([player.hands[0].cards[1]]))
                    del player.hands[0].cards[1]
                    player.stash -= self.current_bets[player.name]

                    # Special ace case
                    if player.hands[0].cards[0].value == "A":
                        for hand in player.hands:
                            hand.cards.append(self.deck.deal_card(True))
                            if hand.calculate_total_value() > 21:
                                if not hand.try_to_switch_soft_hand():
                                    hand.status = "L"
                                    break
                            elif hand.calculate_total_value() == 21:
                                hand.status = "RW"
                        continue
                else:
                    if player.hands[0].cards[0].value == "A":
                        player.hands[0].try_to_switch_soft_hand()

            # Regular play
            for hand in player.hands:
                if hand.status == "P":
                    hit_stand = self.decide_hit_stand()
                    while hit_stand != "S":
                        hand.cards.append(self.deck.deal_card(True))
                        if hand.calculate_total_value() > 21:
                            if not hand.try_to_switch_soft_hand():
                                hand.status = "L"
                                break
                        hit_stand = self.decide_hit_stand()
                    all_players_bust = False

        if all_players_bust:
            return True

        # House phase
        self.house.hands[0].cards[1].visible = True
        while self.house.hands[0].calculate_total_value() < 17:
            self.house.hands[0].cards.append(self.deck.deal_card(True))
            if self.house.hands[0].calculate_total_value() > 21:
                if not self.house.hands[0].try_to_switch_soft_hand():
                    self.house.hands[0].status = "L"
                    return False
        return False
    
    def turn_out_winnings(self):
        if self.house.hands[0].status == "L":
            for player in self.players:
                for hand in player.hands:
                    if hand.status == "P":
                        hand.status = "RW"
                        player.stash += self.current_bets[player.name] * 2.0

        else:
            for player in self.players:
                for hand in player.hands:
                    if hand.status == "P":
                        if self.house.hands[0].calculate_total_value() < hand.calculate_total_value():
                            hand.status = "RW"
                            player.stash += self.current_bets[player.name] * 2.0
                        elif self.house.hands[0].calculate_total_value() == hand.calculate_total_value():
                            hand.status = "RT"
                            player.stash += self.current_bets[player.name] * 1.0
                        else:
                            hand.status = "L"

    def exclude_bankrupt_players(self):
        player_index_to_exclude = []
        for index, player in enumerate(self.players):
            if player.stash < 2:
                player_index_to_exclude.append(index)

        player_index_to_exclude = sorted(player_index_to_exclude, reverse=True)

        for index in player_index_to_exclude:
            del self.players[index]

    def reset_game(self):
        self.exclude_bankrupt_players()
        self.current_bets = {player.name: 0 for player in self.players}
        for player in self.players:
            player.hands = []
        self.house.hands = []
