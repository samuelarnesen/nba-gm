import pandas as pd
from functools import total_ordering
from rules import Rules, ScoringRules
import random, math, sys, copy

class Database:

	def __init__(self, filepath, rules, positional_filepath=None):
		self.data = None
		if isinstance(filepath, str):
			self.data = pd.read_csv(filepath, encoding="ISO-8859-1")
		elif isinstance(filepath, list):
			self.data = pd.read_csv(filepath[0], encoding="ISO-8859-1")
			for extra_filepath in range(1, len(filepath)):
				self.data = self.data.append(pd.read_csv(filepath[extra_filepath], encoding="ISO-8859-1"))

		self.positions = None
		if isinstance(positional_filepath, str):
			self.positions = pd.read_csv(positional_filepath, encoding="ISO-8859-1")
		elif isinstance(positional_filepath, list):
			self.positions = pd.read_csv(positional_filepath[0], encoding="ISO-8859-1")
			for extra_filepath in range(1, len(positional_filepath)):
				self.positions = self.positions.append(pd.read_csv(positional_filepath[extra_filepath], encoding="ISO-8859-1"))

		self.rules = rules

	def get_player_names(self):
		return self.data["NAME"].drop_duplicates().values

	def get_player_data(self, player_name):
		if not self.rules.play_by_play_mode():
			return PlayerData(self.data[self.data["NAME"] == player_name], self.positions[self.positions["Name"] == player_name], self.rules.get_scoring_rules())
		else:
			return PlayByPlayPlayerData(self.data[self.data["NAME"] == player_name], self.positions[self.positions["Name"] == player_name])

class PlayerData:

	def __init__(self, data, position, scoring_rules):
		self.data = data
		self.num_games = len(self.data["NAME"].values)
		self.position = int(position["Proper"].values[0])
		self.scoring_rules = scoring_rules

	def __len__(self):
		return self.num_games

	def sample_game(self):
		game = GameData(self.scoring_rules, self.data.iloc[random.randrange(self.num_games)])
		if not game.is_valid():
			game = GameData(self.scoring_rules, self.data.iloc[random.randrange(self.num_games)])
		return game

	def get_position(self):
		return self.position

class PlayByPlayPlayerData:

	def __init__(self, data, position):
		self.data = data
		self.num_seasons = len(data)
		self.position = int(position["Proper"].values[0])

	def get_position(self):
		return self.position

	def get_usage_rate(self):
		return self.data["USG%"].values[random.randrange(self.num_seasons)]

	def get_three_point_attempt_rate(self):
		return self.data["3PAr"].values[random.randrange(self.num_seasons)]

	def get_three_point_percentage(self):
		return self.data["3P%"].values[random.randrange(self.num_seasons)]

	def get_two_point_percentage(self):
		return self.data["2P%"].values[random.randrange(self.num_seasons)]

	def get_offensive_rebound_percentage(self):
		return self.data["ORB%"].values[random.randrange(self.num_seasons)] / 100

	def get_defensive_rebound_percentage(self):
		return self.data["DRB%"].values[random.randrange(self.num_seasons)] / 100

	def get_assist_percentage(self):
		return self.data["AST%"].values[random.randrange(self.num_seasons)] / 100

	def get_defensive_bpm(self):
		return self.data["DBPM"].values[random.randrange(self.num_seasons)] / 100

	def get_turnover_percentage(self):
		return self.data["TOV%"].values[random.randrange(self.num_seasons)] / 100


@total_ordering
class GameData:

	def __init__(self, scoring_rules=None, data=None):
		if not isinstance(data, type(None)):
			data = copy.deepcopy(data)

		self.scoring_rules = scoring_rules

		self.points = float(data["PTS"]) if not isinstance(data, type(None)) else 0
		#self.rebounds = float(data["TRB"]) if not isinstance(data, type(None)) else 0
		self.assists = float(data["AST"]) if not isinstance(data, type(None)) else 0
		self.steals = float(data["STL"]) if not isinstance(data, type(None)) else 0
		self.blocks = float(data["BLK"]) if not isinstance(data, type(None)) else 0
		self.turnovers = float(data["TOV"]) if not isinstance(data, type(None)) else 0
		self.field_goal_attempts = float(data["FGA"]) if not isinstance(data, type(None)) else 0
		self.free_throw_attempts = float(data["FTA"]) if not isinstance(data, type(None)) else 0
		self.field_goals = float(data["FG"]) if not isinstance(data, type(None)) else 0
		self.free_throws = float(data["FT"]) if not isinstance(data, type(None)) else 0
		self.offensive_rebounds = float(data["ORB"]) if not isinstance(data, type(None)) else 0
		self.defensive_rebounds = float(data["DRB"]) if not isinstance(data, type(None)) else 0
		self.personal_fouls = float(data["PF"]) if not isinstance(data, type(None)) else 0

	def __eq__(self, other):
		return self.score() == other.score()

	def __lt__(self, other):
		return self.score() == other.score()

	def __str__(self):
		return "Points: {}\nRebounds: {}\nAssists:{}\nBlocks:{}\nSteals:{}Turnovers:{}FGA:{}".format(self.points, self.rebounds, self.assists,\
			self.blocks, self.steals, self.turnovers, self.field_goals_attempts)

	def set_scoring_rules(self, scoring_rules):
		self.scoring_rules = scoring_rules

	def get_points(self):
		return self.points

	def get_assists(self):
		return self.assists

	def get_steals(self):
		return self.steals

	def get_blocks(self):
		return self.blocks

	def get_turnovers(self):
		return self.turnovers

	def get_field_goals(self):
		return self.field_goals

	def get_field_goal_attempts(self):
		return self.field_goal_attempts

	def get_free_throw_attempts(self):
		return self.free_throw_attempts

	def get_offensive_rebounds(self):
		return self.offensive_rebounds

	def get_defensive_rebounds(self):
		return self.defensive_rebounds

	def get_free_throws(self):
		return self.free_throws

	def get_personal_fouls(self):
		return self.personal_fouls

	def score(self):
		if not isinstance(self.scoring_rules, ScoringRules):
			print("Error: Cannot score game because scoring rules have not been set", file=sys.stderr)
			return 0

		return (self.get_points() * self.scoring_rules.points_coeff()) + \
				(self.get_field_goals() * self.scoring_rules.field_goals_coeff()) + \
				(self.get_field_goal_attempts() * self.scoring_rules.field_goal_attempts_coeff()) + \
				(self.get_free_throws() * self.scoring_rules.free_throws_coeff()) + \
				(self.get_free_throw_attempts() * self.scoring_rules.free_throw_attempts_coeff()) + \
				(self.get_offensive_rebounds() * self.scoring_rules.offensive_rebounds_coeff()) + \
				(self.get_defensive_rebounds() * self.scoring_rules.defensive_rebounds_coeff()) + \
				(self.get_steals() * self.scoring_rules.steals_coeff()) + \
				(self.get_assists() * self.scoring_rules.assists_coeff()) + \
				(self.get_blocks() * self.scoring_rules.blocks_coeff()) + \
				(self.get_turnovers() * self.scoring_rules.turnovers_coeff()) + \
				(self.get_personal_fouls() * self.scoring_rules.personal_fouls_coeff())


	def add(self, other_game):
		self.points += other_game.get_points()
		self.field_goals += other_game.get_field_goals()
		self.field_goal_attempts += other_game.get_field_goal_attempts()
		self.free_throws += other_game.get_free_throws()
		self.free_throw_attempts += other_game.get_free_throw_attempts()
		#self.rebounds += other_game.get_rebounds()
		self.offensive_rebounds += other_game.get_offensive_rebounds()
		self.defensive_rebounds += other_game.get_defensive_rebounds()
		self.steals += other_game.get_steals()
		self.assists += other_game.get_assists()
		self.blocks += other_game.get_blocks()
		self.turnovers += other_game.get_turnovers()
		self.personal_fouls += other_game.get_personal_fouls()

	def is_valid(self):
		return not math.isnan(self.score()) and self.score() >= 0 and self.score() < 1000

	@staticmethod
	def limit_game(game):

		game.points = game.get_points() * 0.8
		#game.rebounds = game.get_rebounds() * 0.8
		game.assists = game.get_assists() * 0.8
		game.steals = game.get_steals() * 0.8
		game.blocks = game.get_blocks() * 0.8
		game.field_goals_attempts = game.get_field_goal_attempts() * 0.8
		game.turnovers = game.get_turnovers() * 0.8
		game.free_throw_attempts = game.get_free_throw_attempts() * 0.8
		game.offensive_rebounds = game.get_offensive_rebounds() * 0.8
		game.defensive_rebounds = game.get_defensive_rebounds() * 0.8
		game.field_goals = game.get_field_goals() * 0.8
		game.free_throws = game.get_free_throws() * 0.8
		game.personal_fouls = game.get_personal_fouls() * 0.8

		return game

	@staticmethod
	def out_game(game):
		game.points = 0
		game.rebounds = 0
		game.assists = 0
		game.steals = 0
		game.blocks = 0
		game.field_goals_attempts = 0
		game.turnovers = 0
		game.free_throw_attempts = 0
		game.offensive_rebounds = 0
		game.defensive_rebounds = 0
		game.field_goals = 0
		game.free_throws = 0
		game.personal_fouls = 0

		return game

