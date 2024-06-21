from game import Game

game = Game("random")

while True and not(len(game.players) == 0):
    # Create & prepare deck
    game.grab_new_deck()
    game.prepare_deck()

    while not game.deck.refresh_flag:
        # Prepare game
        game.place_bets()

        # Initialize game
        game.perform_deal()

        # Handle naturals
        natural_house = game.check_natural_house()
        all_players_natural = game.check_natural_players()
        game.handle_naturals()

        if natural_house or all_players_natural:
            game.reset_game()
            continue

        # Play the main game
        all_players_bust = game.perform_play()
        
        if all_players_bust:
            game.reset_game()
            continue

        # Turn out winnings
        game.turn_out_winnings()

        # Prepare for the next game
        game.reset_game()
