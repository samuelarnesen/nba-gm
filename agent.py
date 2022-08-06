from participant import Participant
from player import InjuryStatus
from enum import Enum, auto
import sys, copy, itertools, random

class DifficultyMode(Enum):
	DEBUG = "debug"
	EASY = "easy"
	MEDIUM = "medium"
	HARD = "hard"

class Agent(Participant):

	def set_mode(self, mode, tank=False, threshold=5):
		self.player_scores = {}
		self.replacement_level = 0
		self.replacement_percentile = 0.25
		self.replacement_observations = {}
		self.tank = tank
		self.threshold = threshold
		if mode == "debug" or mode == DifficultyMode.DEBUG:
			self.mode = DifficultyMode.DEBUG
			self.game_samples = 0
		elif mode == "easy" or mode == DifficultyMode.EASY:
			self.mode = DifficultyMode.EASY
			self.game_samples = 1
		elif mode == "medium" or mode == DifficultyMode.MEDIUM:
			self.mode = DifficultyMode.MEDIUM
			self.game_samples = 10
		elif mode == "hard":
			self.mode = DifficultyMode.HARD
			self.game_samples = 50
		else:
			print("Error: {} is not a valid mode: Choose between easy, medium, and hard. Defaulting to debug".format(mode))
			self.mode = DifficultyMode.DEBUG
			self.game_samples = 0


	def is_a_person(self):
		return False

	def get_projected_points(self, player, number_of_games_to_sample):
		if player.get_name() in self.player_scores:
			return self.player_scores[player.get_name()]
		average_player_points = 0
		for game in range(number_of_games_to_sample):
			average_player_points += (player.sample_game(real_game=False).score() / number_of_games_to_sample)

		return average_player_points

	def send_pick_to_commissioner(self, draftable_players):

		def score_players(number_of_games_to_sample):

			overall_average = 0
			player_dict = {}
			for player in draftable_players:
				average_player_points = self.get_projected_points(player, number_of_games_to_sample)
				player_dict[player.get_name()] = average_player_points
				overall_average += (average_player_points / len(draftable_players))
				for pos in range(player.get_position() - 1, player.get_position() + 2):
					if pos not in self.replacement_observations:
						self.replacement_observations[pos] = {}
					if player.get_name() not in self.replacement_observations[pos]:
						self.replacement_observations[pos][player.get_name()] = average_player_points
				if player.get_name() not in self.player_scores:
					self.player_scores[player.get_name()] = average_player_points

			replacement_score_by_position = {}
			for pos in self.replacement_observations:
				replacement_level_list = list(reversed(sorted([self.replacement_observations[pos][player] for player in self.replacement_observations[pos]])))
				replacement_score_by_position[pos] = replacement_level_list[int(len(replacement_level_list) * self.replacement_percentile)]

			player_list = []
			for player in draftable_players:
				player_dict[player.get_name()] = (player_dict[player.get_name()] - replacement_score_by_position[player.get_position()])
				player_dict[player.get_name()] *= min(11 - self.year, player.get_years_left()) if player_dict[player.get_name()] > 0 else 1
				player_list.append((player_dict[player.get_name()], player.get_name()))

			player_rankings = [name for _, name in reversed(sorted(player_list, key=lambda pair: pair[0]))]
			return player_rankings

		if self.mode == None:
			print("Error: agent mode is not set", file=sys.stderr)
			return False

		player_to_select = score_players(self.game_samples)[0]
		print(player_to_select)
		return player_to_select

	def set_lineup(self, year, games_out=0):

		should_tank = self.tank and games_out >= self.threshold and year != 10

		player_list = []
		player_to_score = {}
		for player in self.team.get_all_players():
			value = player.get_value()
			if value == "?":
				value = self.get_projected_points(player, self.game_samples)
			if player.get_injury_status() == InjuryStatus.LIMITED:
				value *= 0.8
			elif player.get_injury_status() == InjuryStatus.OUT:
				value = 0

			player_list.append((value if not should_tank else -1 * value, player.get_name(), player))
			player_to_score[player.get_name()] = value if not should_tank else -1 * value
		player_rankings = [player for _, _, player in reversed(sorted(player_list, key=lambda pair: pair[0]))]

		self.team.bench_everyone()

		for player in player_rankings[0:self.lineup_size]:
			success = self.team.move_player_to_starting_lineup(player)

		if len(player_rankings) > self.max_roster_size:
			for player in player_rankings[self.max_roster_size:]:
				self.team.cut_player(player)

		eligible = self.check_roster_eligibility()
		if eligible:
			return True

		combo_scores = [(sum([player_to_score[player.get_name()] for player in combo]), combo) for combo in itertools.combinations(player_rankings, self.lineup_size)]
		sorted_combo_scores = [combo for _, combo in reversed(sorted(combo_scores, key=lambda pair: pair[0]))]
		for combo in sorted_combo_scores:
			self.team.bench_everyone()
			for player in combo:
				self.team.move_player_to_starting_lineup(player)
			if self.check_roster_eligibility():
				return True

		return False





