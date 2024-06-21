import logging, sys, os

from settings import LOGGING_LEVEL
from game import Game

logging.basicConfig(level=LOGGING_LEVEL)
error_logger = logging.getLogger("error")
info_logger = logging.getLogger("info")

error_handler = logging.FileHandler("error.log", mode="w")
info_handler = logging.FileHandler("info.log", mode="w")

error_formatter = logging.Formatter("\t%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s")
info_formatter = logging.Formatter("\t%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s")

error_handler.setFormatter(error_formatter)
info_handler.setFormatter(info_formatter)

error_logger.addHandler(error_handler)
info_logger.addHandler(info_handler)

try:
    game = Game("random", info_logger)
    game_index = 1
    while True:
        # Create & prepare deck
        game.grab_new_deck()
        game.prepare_deck()

        while not game.deck.refresh_flag:
            info_logger.info(f"-- START GAME {game_index} --")
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
                info_logger.info(f"-- END GAME {game_index} --\n")
                game_index += 1
                if len(game.players) == 0:
                    break
                continue

            # Play the main game
            all_players_bust = game.perform_play()
            
            if all_players_bust:
                game.reset_game()
                info_logger.info(f"-- END GAME {game_index} --\n")
                game_index += 1
                if len(game.players) == 0:
                    break
                continue

            # Turn out winnings
            game.turn_out_winnings()

            # Prepare for the next game
            game.reset_game()
            info_logger.info(f"-- END GAME {game_index} --\n")
            game_index += 1
            if len(game.players) == 0:
                break

        if len(game.players) == 0:
            break


except Exception as e:
    _, _, exception_traceback = sys.exc_info()
    file_name = os.path.split(exception_traceback.tb_frame.f_code.co_filename)[1]
    error_logger.critical(f"{e}, {file_name}, {exception_traceback.tb_lineno}")
