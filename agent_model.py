# NOTE: This is copied over from a jupyter notebook which is why it's super messy

import os, pickle, json, random, time, math

import matplotlib.pyplot as plt
from tqdm import tqdm
import torch
from scipy.stats import norm, truncnorm
from sklearn.linear_model import LinearRegression
import numpy as np

from data import Database, CumulativeGameData, GameData
from rules import Rules

NUM_FEATURES = 10

class AgentModel:

	def __init__(self, predicted_scores, data, overall_dataset, stds, player_names, players_to_idxs):
		self.predicted_scores = predicted_scores
		self.data = data
		self.overall_dataset = overall_dataset
		self.stds = stds
		self.player_names = player_names
		self.players_to_idxs = players_to_idxs

	def generate_sample(self, player, num_games):
		player_data = self.data.get_player_data(player)
		
		cumulative = CumulativeGameData()
		for i in range(num_games):
			cumulative.add(player_data.sample_game())
		return cumulative


	def cumulative_game_data_to_tensor(self, game):
		return torch.tensor([
			game.get_points() / game.get_num_games(),
			game.get_field_goals() / game.get_field_goal_attempts() if game.get_field_goal_attempts() > 0 else 0,
			game.get_free_throws() / game.get_free_throw_attempts() if game.get_free_throw_attempts() > 0 else 0 ,
			game.get_offensive_rebounds() / game.get_num_games(),
			game.get_defensive_rebounds() / game.get_num_games(),
			game.get_steals() / game.get_num_games(),
			game.get_assists() / game.get_num_games(),
			game.get_blocks() / game.get_num_games(),
			game.get_turnovers() / game.get_num_games(),
			game.get_personal_fouls() / game.get_num_games()
		], dtype=torch.float)

	def cumulative_game_data_to_stdev_tensor(self, game):
		stdev_map = game.get_stdevs()
		return torch.tensor([
			stdev_map["points"],
			-1,
			-1,
			stdev_map["offensive_rebounds"],
			stdev_map["defensive_rebounds"],
			stdev_map["steals"],
			stdev_map["assists"],
			stdev_map["blocks"],
			stdev_map["turnovers"],
			stdev_map["personal_fouls"],
		], dtype=torch.float)

	def get_odds(self, name, game_count, position=None, sample=None, should_print=False):
	
		def get_penalty(mean, std, sample_item):
			dist = norm(loc=mean.item(), scale=(std.item() / math.sqrt(game_count)))
			penalty = dist.logpdf(sample_item)
			return penalty

		position = position if position else self.data.get_player_data(name).get_position()
		sample = sample if sample else self.generate_sample(name, game_count)
		sample_tensor = self.cumulative_game_data_to_tensor(sample)
		
		log_odds = {}
		relative_odds = {}
		total_odds = 0
		for player in filter(lambda x: self.data.get_player_data(x).get_position() == position, self.player_names):
			player_data = self.overall_dataset[self.players_to_idxs[player]]
			std_to_use = self.stds[player]
			
			pt_penalty = get_penalty(player_data[0], std_to_use[0], sample_tensor[0]) # pts
			trb_penalty = get_penalty(player_data[3] + player_data[4], (std_to_use[3]**2 + std_to_use[4]**2)**0.5, sample_tensor[3] + sample_tensor[4])
			stl_penalty = get_penalty(player_data[5], std_to_use[5], sample_tensor[5]) # steals
			ast_penalty = get_penalty(player_data[6], std_to_use[6], sample_tensor[6]) # asts
			blk_penalty = get_penalty(player_data[7], std_to_use[7], sample_tensor[7]) # blocks
			to_penalty = get_penalty(player_data[8], std_to_use[8], sample_tensor[8]) # turnovers
			pf_penalty = get_penalty(player_data[9], std_to_use[9], sample_tensor[9]) # turnovers

			log_prob = pt_penalty + ast_penalty + trb_penalty + stl_penalty + blk_penalty
			
			log_odds[player] = math.exp(log_prob)
			total_odds += log_odds[player]

		for player in log_odds:
			relative_odds[player] = log_odds[player] / total_odds if total_odds > 0 else 1 / len(self.player_names)
		
		if should_print:
			print(sample)
			sorted_list = sorted([(player, 100 * relative_odds[player]) for player in relative_odds], key=lambda x: x[1], reverse=True)
			for i, (player, score) in enumerate(sorted_list):
				print(i + 1, player, round(score, 2))
		return relative_odds
	
	def score(self, name=None, position=None, game_count=None, sample=None):
		if name:
			return self.predicted_scores[name]
		relative_odds = self.get_odds(name=None, game_count=game_count, position=position, sample=sample)
		score = 0
		for player in relative_odds:
			score += (relative_odds[player] * self.predicted_scores[player])
		return score

if __name__ == '__main__':
	with open("./config.json") as f:
		json_obj = json.load(f)
	rules = Rules(json_obj)
	data = Database(json_obj["Data Path"], rules, json_obj["Positional Data Path"])


	def cumulative_game_data_to_tensor(game):
		return torch.tensor([
			game.get_points() / game.get_num_games(),
			game.get_field_goals() / game.get_field_goal_attempts() if game.get_field_goal_attempts() > 0 else 0,
			game.get_free_throws() / game.get_free_throw_attempts() if game.get_free_throw_attempts() > 0 else 0 ,
			game.get_offensive_rebounds() / game.get_num_games(),
			game.get_defensive_rebounds() / game.get_num_games(),
			game.get_steals() / game.get_num_games(),
			game.get_assists() / game.get_num_games(),
			game.get_blocks() / game.get_num_games(),
			game.get_turnovers() / game.get_num_games(),
			game.get_personal_fouls() / game.get_num_games()
		], dtype=torch.float)

	def cumulative_game_data_to_stdev_tensor(game):
		stdev_map = game.get_stdevs()
		return torch.tensor([
			stdev_map["points"],
			-1,
			-1,
			stdev_map["offensive_rebounds"],
			stdev_map["defensive_rebounds"],
			stdev_map["steals"],
			stdev_map["assists"],
			stdev_map["blocks"],
			stdev_map["turnovers"],
			stdev_map["personal_fouls"],
		], dtype=torch.float)

	def generate_data(rules, data):
		players_to_idxs = {}
		idxs_to_players = {}
		players_to_stds = {}
		overall_dataset = []
		for i, player in enumerate(data.get_player_names()):
			average_game = data.get_player_data(player).get_cumulative_game()
			game_tensor = cumulative_game_data_to_tensor(average_game)
			std = cumulative_game_data_to_stdev_tensor(average_game)
			players_to_idxs[player] = i
			idxs_to_players[i] = player
			players_to_stds[player] = std
			overall_dataset.append(game_tensor)
		overall_dataset = torch.stack(overall_dataset)

		mean = torch.mean(overall_dataset, dim=0)
		normalized_dataset = (overall_dataset - mean) / std
		return overall_dataset, normalized_dataset, idxs_to_players, players_to_idxs, mean, players_to_stds

	overall_dataset, normalized_dataset, idxs_to_players, players_to_idxs, means, stds = generate_data(rules, data)

	player_names = data.get_player_names()

	def generate_sample(player, num_games):
		player_data = data.get_player_data(player)
		
		cumulative = CumulativeGameData()
		for i in range(num_games):
			cumulative.add(player_data.sample_game())
		return cumulative

	def generate_batch(batch_size=64):
		samples = []
		num_games = []
		targets = []
		for i in range(batch_size):
			player = random.choice(player_names)
			game_count = random.randrange(1, 8)
			num_games.append(game_count)
			samples.append(generate_sample(player, game_count))
			targets.append(overall_dataset[players_to_idxs[player], :])
		return samples, num_games, targets

	def get_odds(name, game_count, position=None, sample=None, should_print=False):
		
		def get_penalty(mean, std, sample_item):
			dist = norm(loc=mean.item(), scale=(std.item() / math.sqrt(game_count)))
			penalty = dist.logpdf(sample_item)
			return penalty

		position = position if position else data.get_player_data(name).get_position()
		sample = sample if sample else generate_sample(name, game_count)
		sample_tensor = cumulative_game_data_to_tensor(sample)
		
		log_odds = {}
		relative_odds = {}
		total_odds = 0
		for player in filter(lambda x: data.get_player_data(x).get_position() == position, player_names):
			player_data = overall_dataset[players_to_idxs[player]]
			std_to_use = stds[player]
			
			pt_penalty = get_penalty(player_data[0], std_to_use[0], sample_tensor[0]) # pts
			trb_penalty = get_penalty(player_data[3] + player_data[4], (std_to_use[3]**2 + std_to_use[4]**2)**0.5, sample_tensor[3] + sample_tensor[4])
			stl_penalty = get_penalty(player_data[5], std_to_use[5], sample_tensor[5]) # steals
			ast_penalty = get_penalty(player_data[6], std_to_use[6], sample_tensor[6]) # asts
			blk_penalty = get_penalty(player_data[7], std_to_use[7], sample_tensor[7]) # blocks
			to_penalty = get_penalty(player_data[8], std_to_use[8], sample_tensor[8]) # turnovers
			pf_penalty = get_penalty(player_data[9], std_to_use[9], sample_tensor[9]) # turnovers

			log_prob = pt_penalty + ast_penalty + trb_penalty + stl_penalty + blk_penalty
			
			log_odds[player] = math.exp(log_prob)
			total_odds += log_odds[player]

		for player in log_odds:
			relative_odds[player] = log_odds[player] / total_odds if total_odds > 0 else 1 / len(player_names)
		
		if should_print:
			print(sample)
			sorted_list = sorted([(player, 100 * relative_odds[player]) for player in relative_odds], key=lambda x: x[1], reverse=True)
			for i, (player, score) in enumerate(sorted_list):
				print(i + 1, player, round(score, 2))
		return relative_odds

	def generate_random_team(temperature, win_rates, num_games):
		full_team_names = random.choices(player_names, k=10)
		team_with_noise = [(name, win_rates[name] + ((0.5 * temperature) * (random.random() - 0.5))) for name in full_team_names]
		sorted_team_with_noise = sorted(team_with_noise, key=lambda x: x[1], reverse=True)
		names = [name for (name, _) in sorted_team_with_noise][0:6]
		team = [data.get_player_data(name) for name in names]
		game = GameData()
		game.scoring_rules = rules.scoring_rules
		for player_data in team:
			game.add(player_data.sample_game())
		return names, game

	def generate_data(num_games=10_000, smoothing=50):
		player_to_wins = {}
		player_to_matches = {}
		player_to_win_rate = {}
		for player in player_names:
			player_to_wins[player] = 0
			player_to_matches[player] = 0
			player_to_win_rate[player] = 0.5
		
		temperature = 1
		for i in tqdm(range(num_games)):
			names_one, game_one = generate_random_team(temperature, player_to_win_rate, num_games)
			names_two, game_two = generate_random_team(temperature, player_to_win_rate, num_games)

			score_one = game_one.score(other=game_two, roto=True)
			score_two = game_two.score(other=game_one, roto=True)
			value_one = 1 if score_one > score_two else (0 if score_one < score_two else 0.5)
			value_two = 1 - value_one

			for name in names_one:
				player_to_wins[name] += value_one
				player_to_matches[name] += 1
				player_to_win_rate[name] = (player_to_wins[name] + (smoothing / 2)) / (player_to_matches[name] + smoothing)
			for name in names_two:
				player_to_wins[name] += value_two
				player_to_matches[name] += 1
				player_to_win_rate[name] = (player_to_wins[name] + (smoothing / 2)) / (player_to_matches[name] + smoothing)
			
			temperature -= (temperature / num_games)
		
		for player in player_names:
			player_to_win_rate[name] = player_to_wins[name] / player_to_matches[name] if player_to_matches[name] > 0 else 0

		return player_to_win_rate, player_to_wins, player_to_matches

	"""		
	rate, wins, matches = generate_data()

	with open("./model_data/temp-agent-data.p", "wb") as f:
		pickle.dump({"rate": rate, "wins": wins, "matches": matches}, f)
	"""


	with open("./model_data/temp-agent-data.p", "rb") as f:
		data_dict = pickle.load(f)
	rate = data_dict["rate"]
	wins = data_dict["wins"]
	matches = data_dict["matches"]


	xs = []
	ys = []
	for name in player_names:
		xs.append(overall_dataset[players_to_idxs[name], :])
		ys.append(rate[name])
	xs = torch.stack(xs).detach().numpy()
	ys = np.array(ys)

	reg = LinearRegression().fit(xs, ys)

	predicted_scores = {}
	for name in player_names:
		predicted_scores[name] = reg.predict(overall_dataset[players_to_idxs[name], :].unsqueeze(0).detach().numpy())[0]

	model = AgentModel(predicted_scores, data, overall_dataset, stds, player_names, players_to_idxs)

	with open("./model_data/scorer.p", "wb") as f:
		pickle.dump(model, f)