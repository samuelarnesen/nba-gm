from league import League
import re, json, pickle, argparse

def save_game(league, save_path):
	with open(save_path, "wb") as f:
		pickle.dump(league, f)

def load_game(load_path):
	with open(load_path, "rb") as f:
		league = pickle.load(f)
	return league


if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--save_filepath", type=str, default="./saved_games/saved_game.p")
	parser.add_argument("--load_from_saved_game", action="store_true", default=False)
	parser.add_argument("--checkpoint_filepath", default="./saved_games/saved_game.p", type=str)
	args = parser.parse_args()

	if args.load_from_saved_game:
		league = load_game(args.checkpoint_filepath)
		current_year = league.get_current_year()
	else:
		league = League()
		league.load_from_config()
		league.start_league()
		current_year = 0

	for year in range(current_year, 10):
		print("Year {}".format(year + 1))
		league.run_draft(year)
		league.run_season([27, 54])
		league.run_championship()
		league.end_season()
		save_game(league, args.save_filepath)

	league.display_final_results()








