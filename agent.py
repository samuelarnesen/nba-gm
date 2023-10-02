
from participant import Participant
from player import InjuryStatus
from enum import Enum, auto
from agent_model import AgentModel

import sys, copy, itertools, random, pickle, os

class DifficultyMode(Enum):
	DEBUG = "debug"
	EASY = "easy"
	MEDIUM = "medium"
	HARD = "hard"

# todo: delete this

with open("./model_data/scorer.p", "rb") as f:
	DEFAULT_MODEL = pickle.load(f)

class Agent(Participant):

	def __init__(self, name, rules, team_name=None, autodraft=False):
		super().__init__(name, rules, team_name, autodraft)
		self.model = DEFAULT_MODEL
		self.mode = DifficultyMode.DEBUG
		self.cached_evaluations = {}

	def set_mode(self, mode):
		if mode == "debug" or mode == DifficultyMode.DEBUG:
			self.mode = DifficultyMode.DEBUG
		elif mode == "easy" or mode == DifficultyMode.EASY:
			self.mode = DifficultyMode.EASY
		elif mode == "medium" or mode == DifficultyMode.MEDIUM:
			self.mode = DifficultyMode.MEDIUM
		elif mode == "hard":
			self.mode = DifficultyMode.HARD
		else:
			print("Error: {} is not a valid mode: Choose between easy, medium, and hard. Defaulting to debug".format(mode))
			self.mode = DifficultyMode.DEBUG

	def is_a_person(self):
		return False

	def evaluate_player(self, player):
		if player.get_alias() != player.get_name() and player.get_scout_value() and player.get_games_started() == 0:
			sample, game_count = player.get_scout_value()
			return DEFAULT_MODEL.score(name=None, position=player.get_position(), game_count=game_count, sample=sample)
		else:
			return DEFAULT_MODEL.score(name=player.get_name(), position=player.get_position(), game_count=None, sample=None)

	def send_pick_to_commissioner(self, draftable_players):
		values = {}
		for player in draftable_players:
			if player.get_alias() in self.cached_evaluations:
				values[player] = self.cached_evaluations[player.get_alias()]
			else:
				values[player] = self.evaluate_player(player)
				self.cached_evaluations[player.get_alias()] = values[player]

		max_player = None
		max_value = -float("inf")
		for player in values:
			if values[player] > max_value:
				max_value = values[player]
				max_player = player

		print(max_player)
		return max_player.get_name()

	def set_lineup(self, year, games_out=0):
		self.team.bench_everyone()

		scores = {}
		for player in self.team.get_all_players():
			scores[player] = self.evaluate_player(player)

		sorted_list = sorted([(player, scores[player]) for player in scores], key=lambda x: x[1], reverse=True)
		for i, (player, _) in enumerate(sorted_list):
			if i < self.rules.get_team_rules().get_lineup_size():
				self.team.move_player_to_starting_lineup(player)

		return True




	





