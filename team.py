from player import Player, PlayerGroup
from data import GameData, RotoGameData
import sys, random

class Team:

	def __init__(self, rules, name=None):
		self.name = name
		self.all_players = PlayerGroup()
		self.starting_players = PlayerGroup()
		self.bench_players = PlayerGroup()
		self.max_roster_size = rules.get_roster_size()
		self.lineup_size = rules.get_lineup_size()
		self.positional_constraints = rules.is_positionally_constrained()
		self.aliases_to_names = {}
		self.roto_stats = RotoGameData()

	def __str__(self):
		return "\n{}\nStarters:\n{}\n\nBench:\n{}".format(self.name, self.starting_players, self.bench_players)

	def __contains__(self, player):
		return player in self.all_players

	def __len__(self):
		return len(self.all_players)

	def __eq__(self, other):
		if not isinstance(other, Team):
			return False
		return self.name == other.get_name()

	def restore_to_health(self):
		for player in self.all_players:
			player.restore_to_health()

	def update_health_status(self):
		for player in self.all_players:
			player.recalculate_injury_status()

	def find_star(self):
		star = self.get_all_player_stats()[0][1]
		return star, star.get_points_this_year()

	def get_all_player_stats(self):
		player_stats =  list(reversed(sorted([(player.get_points_this_year(), random.random(), player) for player in self.all_players])))
		return [(points, player) for (points, _, player) in player_stats]

	def start_championship(self):
		for player in self.all_players:
			player.reset_points_this_year()

	def draft_player(self, player):
		self.add_player(player, check_size=False)

	def add_player(self, player, check_size=True):

		if len(self.all_players) >= self.max_roster_size and check_size:
			print("Warn: Roster length exceeds maximum roster size {}. Addition denied".format(self.max_roster_size))
			return

		self.all_players.append(player)
		self.aliases_to_names[str(player.get_alias())] = player
		if len(self.starting_players) < self.lineup_size:
			self.starting_players.append(player)
		else:
			self.bench_players.append(player)

	def play_game(self, opponent=None):
		game = GameData()
		for player in self.starting_players:
			game.add(player.sample_game())
		return game

	def age(self):
		players_to_remove = []
		for player in self.all_players:
			player.age()
			if player.is_expired():
				players_to_remove.append(player)
				
		for player in players_to_remove:
			self.cut_player(player.get_name())

	def cut_player(self, player):

		if player in self.aliases_to_names:
			player = self.aliases_to_names[player]

		if player not in self.all_players:
			print("Warn: Player {} not on team".format(player))
			return False

		player_to_cut = self.all_players.remove(player)
		self.starting_players.remove(player) if player in self.starting_players else self.bench_players.remove(player)
		return player_to_cut

	def move_player_to_starting_lineup(self, player):

		if player in self.aliases_to_names:
			player = self.aliases_to_names[player]

		if player not in self.bench_players:
			print("Warn: Player {} not on bench".format(player))
			return False

		if self.is_starting_lineup_full():
			print("Warn: Starting roster size exceeded")
			return False

		player_to_move = self.bench_players.remove(player)
		self.starting_players.append(player_to_move)

		return True

	def is_starting_lineup_full(self):
		return len(self.starting_players) >= self.lineup_size

	def remove_player_from_starting_lineup(self, player):

		if player in self.aliases_to_names:
			player = self.aliases_to_names[player]

		if player not in self.starting_players:
			print("Warn: Player {} not in starting roster".format(player))
			return False

		player_to_move = self.starting_players.remove(player)
		self.bench_players.append(player_to_move)
		return True

	def bench_everyone(self):
		for player in self.starting_players:
			self.bench_players.append(player)
		self.starting_players = PlayerGroup()

	def is_eligible(self):
		if len(self.all_players) > self.max_roster_size or len(self.starting_players) > self.lineup_size:
			return False

		if not self.positional_constraints:
			return True

		current_position = 1
		failed_once = False
		sorted_positions = sorted([player.get_position() for player in self.starting_players])
		for i in range(0, len(sorted_positions)):
			if sorted_positions[i] not in [current_position - 1, current_position, current_position + 1]:
				if failed_once:
					return False
				failed_once = True
			else:
				current_position += 1

		return True

	def flip_the_team(self):
		success = True
		old_bench = PlayerGroup([player for player in self.bench_players])
		old_starters = PlayerGroup([player for player in self.starting_players])
		for player_to_remove, player_to_start in zip(old_starters, old_bench):
			success = success and self.remove_player_from_starting_lineup(player_to_remove.get_name())
			success = success and self.move_player_to_starting_lineup(player_to_start.get_name())
		return success

	def update_from_box_score(self, box_score):
		for player in self.starting_players:
			if player.get_name() in box_score:
				player.update_from_box_score(box_score[player.get_name()])

	def get_starters(self):
		return self.starting_players

	def get_bench_players(self):
		return self.bench_players

	def get_all_players(self):
		return self.all_players

	def set_name(self, name):
		self.name = name

	def get_name(self):
		return self.name






