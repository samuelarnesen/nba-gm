from data import PlayerData, GameData, CumulativeGameData
from enum import Enum, auto
import sys, math, random, re

class Player:

	def __init__(self, name, data, years_left=0, value=None, number_of_scouting_games=-1, alias=None, roto=False):
		self.name = name
		self.years_left = years_left
		self.data = data
		self.total_points = 0
		self.games_started = 0
		self.games_started_this_year = 0
		self.points_this_year = 0
		self.box_score_stats = [0, 0, 0]
		self.box_score_stats_this_year = [0, 0, 0]
		self.cumulative_game = CumulativeGameData()
		self.cumulative_game_this_year = CumulativeGameData()
		self.injury_status = InjuryStatus.HEALTHY

		self.use_scouting = number_of_scouting_games >= 0
		self.scouting_report = None
		self.scout_value = None
		self.alias = name if alias == None else alias
		self.roto = roto


	def set_name(self, name):
		self.name = name

	def set_alias(self, alias):
		self.alias = alias

	def set_years_left(self, years_left):
		self.years_left = years_left

	def set_value(self, value):
		self.value = value

	def set_data(self, data):
		if not isinstance(data, PlayerData):
			print("Error: Data added is of type {}, not of type PlayerData. Action denied".format(type(data)))
			return
		self.data = data

	def get_position(self):
		return self.data.get_position()

	def get_alias(self):
		return self.alias

	def age(self):
		self.years_left -= 1
		self.points_this_year = 0
		self.box_score_stats_this_year = [0, 0, 0]
		self.games_started_this_year = 0

	def sample_game(self, real_game=True):
		if isinstance(self.data, type(None)):
			print("Error: No games to sample from. Action denied")
			return
		game = self.data.sample_game()
		while math.isnan(game.score()):
			game = self.data.sample_game()

		if self.injury_status == InjuryStatus.LIMITED:
			game = GameData.limit_game(game)
		elif self.injury_status == InjuryStatus.OUT:
			game = GameData.out_game(game)

		if real_game:
			self.cumulative_game.add(game)
			self.cumulative_game_this_year.add(game)

			if not self.roto:
				score = game.score(roto=self.roto)
				self.total_points += score
				self.points_this_year += score

			self.games_started += 1
			self.games_started_this_year += 1
			self.use_scouting = False

		return game

	def generate_scouting_report(self, number_of_games):
		self.use_scouting = True
		number_of_games_to_use = random.randrange(1, number_of_games)
		games = [self.sample_game(real_game=False) for i in range(number_of_games_to_use)]

		if self.roto:
			total_game = CumulativeGameData()
			for game in games:
				total_game.add(game)
			self.scouting_report = "Value: {}, Games: {}".format(str(total_game), number_of_games_to_use)
			self.scout_value = (str(total_game), number_of_games_to_use)
		else:
			avg_score = round(sum([game.score() for game in games]) / number_of_games_to_use, 0)
			self.scouting_report = "Value: {}, Games: {}".format(str(avg_score), number_of_games_to_use)
			self.scout_value = (avg_score, number_of_games_to_use)

	def get_scouting_report(self):
		return self.scouting_report

	def get_scout_value(self):
		return self.scout_value

	def get_name(self):
		return self.name

	def get_years_left(self):
		return self.years_left

	def is_expired(self):
		return self.years_left <= 0

	def get_points_this_year(self):
		return self.points_this_year

	def get_average_points_this_year(self):
		return self.points_this_year / self.games_started_this_year

	def reset_points_this_year(self):
		self.points_this_year = 0
		self.games_started_this_year = 0
		self.cumulative_game_this_year = CumulativeGameData()

	def get_value(self):
		if self.games_started == 0:
			return "?"
		if self.roto:
			return self.cumulative_game
		return round(self.total_points / self.games_started)

	def get_position_name(self):
		positions = ["PG", "SG", "SF", "PF", "C"]
		return positions[self.get_position() - 1]

	def recalculate_injury_status(self):
		rand = random.random()
		if rand < 0.03:
			self.injury_status = InjuryStatus.OUT
		elif rand < 0.06:
			self.injury_status = InjuryStatus.LIMITED
		else:
			self.injury_status = InjuryStatus.HEALTHY

	def restore_to_health(self):
		self.injury_status = InjuryStatus.HEALTHY

	def get_injury_status(self):
		return self.injury_status

	def get_stats(self):
		return self.data

	def get_total_points(self):
		return self.total_points

	def get_games_started(self):
		return self.games_started

	def update_from_box_score(self, box_score, real_game=True):
		if not real_game:
			return

		self.games_started += 1
		self.games_started_this_year += 1

		self.box_score_stats_this_year[0] += box_score["Points"]
		self.box_score_stats[0] += box_score["Points"]
		self.box_score_stats_this_year[1] += box_score["Rebounds"]
		self.box_score_stats[1] += box_score["Rebounds"]
		self.box_score_stats_this_year[2] += box_score["Assists"]
		self.box_score_stats[2] += box_score["Assists"]

	def __str__(self):

		if self.games_started == 0 and not self.use_scouting:
			return "{} {}\t({})".format(self.get_position_name(), self.name, self.years_left)
		elif self.games_started == 0:
			return "{} {}\t({}) [Scouting: {}]".format(self.get_position_name(), self.alias, self.years_left, self.get_scouting_report())
		elif self.box_score_stats != [0, 0, 0]:
			return "{} {}\t({}, {}/{}/{})".format(self.get_position_name(), self.name, self.years_left, \
					int(self.box_score_stats[0] / self.games_started), int(self.box_score_stats[1] / self.games_started), int(self.box_score_stats[2] / self.games_started))
		else:
			return "{} {}\t({}, {})".format(self.get_position_name(), self.name, self.years_left, self.get_value())	

	def __eq__(self, other):
		if not isinstance(other, Player):
			return False
		else:
			return other.get_name() == self.name

	def __hash__(self):
		return hash(self.get_name())

class PlayerGroup:

	def __init__(self, internal_list=None, roto=False):
		self.players = []
		if internal_list != None:
			for player in internal_list:
				if isinstance(player, Player):
					self.players.append(player)
				elif isinstance(player, tuple):
					if len(player) == 3:
						self.players.append(Player(player[0], player[1], player[2], roto=roto))
					else:
						print("Error: PlayerGroup could not be created. Tuple element of wrong length")
						self.players = []
				else:
					print("Error: PlayerGroup could not be created. Element of wrong type")
					self.players = []

	def __contains__(self, player):
		if isinstance(player, Player):
			return player in self.players
		elif isinstance(player, str):
			return self.get_player_by_name(player) != None
		return False

	def __len__(self):
		return len(self.players)

	def __iter__(self):
		self.current_index = -1
		return self

	def __next__(self):
		if self.current_index >= len(self.players) - 1:
			self.current_index = 0
			raise StopIteration
		self.current_index += 1
		return self.players[self.current_index]

	def __str__(self):
		player_rep_list = []
		for i, player in enumerate(self.players):

			player_rep_list.append(player.__str__())

			if player.get_injury_status() == InjuryStatus.OUT:
				player_rep_list[-1] += " **OUT**"
			elif player.get_injury_status() == InjuryStatus.LIMITED:
				player_rep_list[-1] += " **LIMITED**"

		return "\n".join(player_rep_list)

	def __getitem__(self, idx):
		if idx >= len(self.players):
			return None
		return self.players[idx]

	def get_player_by_name(self, name):
		for player in self.players:
			if str(player.get_alias()).lower() == name.lower():
				return player

		candidates = []
		for player in self.players:
			split_player_name = re.split("[-\s+]", player.get_name())
			initials = "".join([word[0] for word in filter(lambda x: len(x) > 0, split_player_name)])
			if initials == name or re.search("(?:^{})|(?:{}$)".format(name.lower(), name.lower()), player.get_name().lower()) != None:
				candidates.append(player)

		if len(candidates) == 1:
			return candidates[0]
		elif len(candidates) > 1:
			print("Warn: {} does not refer to a single player".format(name))
		return None

	def append(self, player):
		self.players.append(player)

	def remove(self, player):
		if isinstance(player, Player):
			player_to_remove = self.get_player_by_name(player.get_name())
		elif isinstance(player, str):
			player_to_remove = self.get_player_by_name(player)

		if not isinstance(player_to_remove, type(None)):
			self.players.remove(player_to_remove)
		else:
			print("Warn: player could not be removed")
		return player_to_remove

class InjuryStatus(Enum):
	HEALTHY = auto()
	LIMITED = auto()
	OUT = auto()

