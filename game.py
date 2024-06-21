import random, math

from deck import Deck
from player import Player
from hand import Hand
from settings import NB_PLAYERS, DEF_STASH

class Game:
    def __init__(self, mode, logger):
        self.logger = logger
        self.players = [Player(f"Player{i + 1}", DEF_STASH) for i in range(NB_PLAYERS)]
        self.house = Player("house")
        self.mode = mode
        self.current_bets = {player.name: 0 for player in self.players}
        self.current_insurances = {player.name: 0 for player in self.players}

        self.place_bets_mapping = {
            "random": self.place_bets_random
        }
        self.decide_hit_stand_mapping = {
            "random": self.decide_hit_stand_random
        }
        self.decide_split_mapping = {
            "random": self.decide_split_random
        }
        self.decide_double_down_mapping = {
            "random": self.decide_double_down_random
        }
        self.place_insurance_mapping = {
            "random": self.place_insurance_random
        }
        self.decide_insurance_mapping = {
            "random": self.decide_insurance_random
        }

    def grab_new_deck(self):
        self.deck = Deck()
        self.logger.info("New deck grabbed")

    def prepare_deck(self):
        self.deck.shuffle_deck()
        self.deck.cut_deck(random.random())
        self.deck.place_blank_card(random.randrange(60, 76))
        self.logger.info("Deck shuffled, cut and blank card added")

    def place_bets(self):
        self.place_bets_mapping[self.mode]()

    def place_bets_random(self):
        for player in self.players:
            bet = round(random.uniform(2.0, min(500.0, player.stash)) * 2) / 2
            self.current_bets[player.name] = bet
            player.stash -= bet
            self.logger.info(f"{player.name} bets {bet} ({player.stash} left)")

    def perform_deal(self):
        # First card for all players
        for player in self.players:
            player.hands.append(Hand([self.deck.deal_card(True)]))

        # First card for the house
        self.house.hands.append(Hand([self.deck.deal_card(True)]))

        # Second card for all players
        for player in self.players:
            player.hands[0].cards.append(self.deck.deal_card(True))
            self.logger.info(f"Initial hand {player.name}: {', '.join([str(card) for card in player.hands[0].cards])}")

        # Second card for the house
        self.house.hands[0].cards.append(self.deck.deal_card(False))
        self.logger.info(f"Initial hand house: {', '.join([str(card) if card.visible else 'X' for card in self.house.hands[0].cards])}")

    def place_insurance_random(self, player):
        return round(random.uniform(0.0, min(self.current_bets[player.name]/2, player.stash)) * 2.0) / 2

    def check_natural_house(self):
        if self.house.hands[0].cards[0].play_value in [10, 11]:
            self.logger.info("The house checks for a natural")
            if self.house.hands[0].cards[0].play_value == 11:
                # Opportunity for players to get insurance
                self.logger.info("The players can take insurance")
                for player in self.players:
                    insurance = self.decide_insurance()
                    if insurance:
                        player.hands[0].insured = True
                        insurance_amount = self.place_insurance_mapping[self.mode](player)
                        player.stash -= insurance_amount
                        self.current_insurances[player.name] = insurance_amount
                        self.logger.info(f"{player.name} takes {insurance_amount} insurance ({player.stash} left)")

            if self.house.hands[0].calculate_total_value() == 21:
                self.logger.info("The house has a natural")
                self.logger.info(f"Natural house hand: {', '.join([str(card) for card in self.house.hands[0].cards])}")
                self.house.hands[0].status = "N"
                return True
            
            self.logger.info("The house does not have a natural")
            
        return False

    def check_natural_players(self):
        all_players_natural = True
        for player in self.players:
            if player.hands[0].calculate_total_value() == 21:
                self.logger.info(f"{player.name} has a natural")
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
                self.logger.info(f"{player.name} wins {self.current_bets[player.name] * 2.5} because of a natural win (total: {player.stash})")
            elif player.hands[0].status == "NT":
                player.stash += self.current_bets[player.name]
                self.logger.info(f"{player.name} earns back {self.current_bets[player.name]} because of a natural tie (total: {player.stash})")
            elif player.hands[0].insured and self.house.hands[0].status == "N":
                player.stash += self.current_insurances[player.name] * 2.0
                self.logger.info(f"{player.name} earns back {self.current_insurances[player.name] * 2.0} because of insurance (total: {player.stash})")
    
    def decide_hit_stand(self):
        return self.decide_hit_stand_mapping[self.mode]()
    
    def decide_hit_stand_random(self):
        return "H" if random.random() > 0.5 else "S"
    
    def decide_split_random(self):
        return True if random.random() > 0.5 else False
    
    def decide_split(self):
        return self.decide_split_mapping[self.mode]()
    
    def decide_double_down_random(self):
        return True if random.random() > 0.5 else False
    
    def decide_double_down(self):
        return self.decide_double_down_mapping[self.mode]()
    
    def decide_insurance_random(self):
        return True if random.random() > 0.5 else False
    
    def decide_insurance(self):
        return self.decide_insurance_mapping[self.mode]()

    def perform_play(self):
        # Player phase
        all_players_bust = True
        for player in self.players:
            # Option to double down
            doubled_down = False
            if player.hands[0].calculate_total_value() in [9, 10, 11] and player.stash > self.current_bets[player.name]:
                doubled_down = self.decide_double_down()
                if doubled_down:
                    player.stash -= self.current_bets[player.name]
                    self.current_bets[player.name] *= 2
                    player.hands[0].cards.append(self.deck.deal_card(True))
                    if player.hands[0].calculate_total_value() > 21:
                        player.hands[0].try_to_switch_soft_hand()
                    self.logger.info(f"{player.name} doubles down, complete hand: {', '.join([str(card) for card in player.hands[0].cards])}")
                    continue

            # Option to split pairs
            if player.hands[0].cards[0].value == player.hands[0].cards[1].value:
                split = self.decide_split()
                if split and not doubled_down and player.stash > self.current_bets[player.name]:
                    player.hands.append(Hand([player.hands[0].cards[1]]))
                    del player.hands[0].cards[1]
                    player.stash -= self.current_bets[player.name]
                    self.logger.info(f"{player.name} splits pair: {' / '.join([', '.join([str(card) for card in hand.cards]) for hand in player.hands])}")

                    # Special ace case
                    if player.hands[0].cards[0].value == "A":
                        for hand in player.hands:
                            hand.cards.append(self.deck.deal_card(True))
                            if hand.calculate_total_value() > 21:
                                hand.try_to_switch_soft_hand()
                        self.logger.info(f"Special ace case: {' / '.join([', '.join([str(card) for card in hand.cards]) for hand in player.hands])}")
                        continue
                else:
                    if player.hands[0].cards[0].value == "A":
                        player.hands[0].try_to_switch_soft_hand()

            # Regular play
            for hand in player.hands:
                if hand.status == "P":
                    hand_bust = False
                    hit_stand = self.decide_hit_stand()
                    self.logger.info(f"{player.name} decides to {'stand' if hit_stand == 'S' else 'hit'} for hand {', '.join([str(card) for card in hand.cards])}")
                    while hit_stand != "S":
                        hand.cards.append(self.deck.deal_card(True))
                        if hand.calculate_total_value() > 21:
                            if not hand.try_to_switch_soft_hand() and hand.calculate_total_value() > 21:
                                hand.status = "L"
                                self.logger.info(f"{player.name} goes bust with hand {', '.join([str(card) for card in hand.cards])} (total: {player.stash})")
                                hand_bust = True
                                break
                        hit_stand = self.decide_hit_stand()
                        self.logger.info(f"{player.name} decides to {'stand' if hit_stand == 'S' else 'hit'} for hand {', '.join([str(card) for card in hand.cards])}")
                    if not hand_bust:
                        all_players_bust = False

        if all_players_bust:
            self.logger.info("All players went bust, the house wins")
            return True

        # House phase
        self.house.hands[0].cards[1].visible = True
        self.logger.info(f"Second card of house revealed to form the following hand: {', '.join([str(card) for card in self.house.hands[0].cards])}")
        while self.house.hands[0].calculate_total_value() < 17:
            self.house.hands[0].cards.append(self.deck.deal_card(True))
            self.logger.info(f"The house gets a new card for the following hand: {', '.join([str(card) for card in self.house.hands[0].cards])}")
            if self.house.hands[0].calculate_total_value() > 21:
                if not self.house.hands[0].try_to_switch_soft_hand():
                    self.house.hands[0].status = "L"
                    self.logger.info(f"The house goes bust")
                    return False
        return False
    
    def turn_out_winnings(self):
        if self.house.hands[0].status == "L":
            for player in self.players:
                for hand in player.hands:
                    if hand.status == "P":
                        hand.status = "RW"
                        player.stash += self.current_bets[player.name] * 2.0
                        self.logger.info(f"{player.name} wins {self.current_bets[player.name] * 2.0} for the hand {', '.join([str(card) for card in hand.cards])} because the house went bust (total: {player.stash})")

        else:
            for player in self.players:
                for hand in player.hands:
                    if hand.status == "P":
                        if self.house.hands[0].calculate_total_value() < hand.calculate_total_value():
                            hand.status = "RW"
                            player.stash += self.current_bets[player.name] * 2.0
                            self.logger.info(f"{player.name} wins {self.current_bets[player.name] * 2.0} for the win with hand {', '.join([str(card) for card in hand.cards])} (total: {player.stash})")
                        elif self.house.hands[0].calculate_total_value() == hand.calculate_total_value():
                            hand.status = "RT"
                            player.stash += self.current_bets[player.name] * 1.0
                            self.logger.info(f"{player.name} earns back {self.current_bets[player.name] * 1.0} for the tie with hand {', '.join([str(card) for card in hand.cards])} (total: {player.stash})")
                        else:
                            hand.status = "L"
                            self.logger.info(f"{player.name} loses with the hand {', '.join([str(card) for card in hand.cards])} (total: {player.stash})")

    def exclude_bankrupt_players(self):
        player_index_to_exclude = []
        for index, player in enumerate(self.players):
            if player.stash < 2:
                player_index_to_exclude.append(index)

        player_index_to_exclude = sorted(player_index_to_exclude, reverse=True)

        for index in player_index_to_exclude:
            self.logger.info(f"{self.players[index].name} is bankrupt and excluded from the game")
            del self.players[index]

    def reset_game(self):
        self.exclude_bankrupt_players()
        self.current_bets = {player.name: 0 for player in self.players}
        self.current_insurances = {player.name: 0 for player in self.players}
        for player in self.players:
            player.hands = []
        self.house.hands = []
