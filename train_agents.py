from agent_model import AgentModel
from league import League
import re, json, pickle, argparse, sys

def save_game(league, save_path):
	with open(save_path, "wb") as f:
		pickle.dump(league, f)

def load_game(load_path):
	with open(load_path, "rb") as f:
		league = pickle.load(f)
	return league


if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--num_seasons", type=int, default=1_000)
	args = parser.parse_args()

	for year in range(args.num_seasons):

		league = League()
		league.load_from_config()
		league.start_league()

		league.run_draft(0)
		league.run_season([27, 54])
		league.run_championship(dramatic=True)
		league.end_season()

	league.save_agents()
