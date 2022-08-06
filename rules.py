import json, random, sys

class Rules:

	def __init__(self, config):
		self.play_by_play = config["Play-by-play"]
		self.dramatic = config["Dramatic"]
		self.team_rules = TeamRules(config["Lineup Size"], config["Roster Size"], config["Positional Constraints"], config["Allow Injuries"])
		self.draft_rules = DraftRules(config["Draft Rules"])
		self.scoring_rules = ScoringRules(config["Scoring Rules"]) if not config["Play-by-play"] else None

	def play_by_play_mode(self):
		return self.play_by_play

	def dramatic_mode(self):
		return self.dramatic

	def get_team_rules(self):
		return self.team_rules

	def get_draft_rules(self):
		return self.draft_rules

	def get_scoring_rules(self):
		return self.scoring_rules

class TeamRules:

	def __init__(self, starting_lineup_size, roster_size, positionally_constrainted, allow_injuries):
		self.starting_lineup_size = starting_lineup_size
		self.roster_size = roster_size
		self.positionally_constrainted = positionally_constrainted
		self.allow_injuries = allow_injuries

	def get_lineup_size(self):
		return self.starting_lineup_size

	def get_roster_size(self):
		return self.roster_size

	def positionally_constrained(self):
		return self.positionally_constrained

	def allow_injuries_mode(self):
		return self.allow_injuries

class DraftRules:

	def __init__(self, draft_rules):
		self.year_one_rounds = draft_rules[0]["Rounds"]
		self.year_one_snake =  draft_rules[0]["Snake"]
		self.year_one_scouting = draft_rules[0]["Scouting"]
		self.year_one_scouting_games = draft_rules[0]["Scouting Games"]
		self.normal_rounds = draft_rules[1]["Rounds"]
		self.normal_snake =  draft_rules[1]["Snake"]
		self.normal_scouting = draft_rules[1]["Scouting"]
		self.normal_scouting_games = draft_rules[1]["Scouting Games"]

	def get_properties_this_year(self, year, one_index=True):
		if (year == 1 and one_index) or (year == 0 and not one_index):
			return self.year_one_rounds, self.year_one_snake, self.year_one_scouting, self.year_one_scouting_games
		return self.normal_rounds, self.normal_snake, self.normal_scouting, self.normal_scouting_games

	def use_scouting(self, year):
		_, _, use_scouting, _ = self.get_properties_this_year(year)
		return use_scouting

	def get_number_of_games_of_scouting(self, year):
		_, _, _, num_games = self.get_properties_this_year(year)
		return num_games



class ScoringRules:

	def __init__(self, scoring_rules):

		self.randomize = scoring_rules["Randomization"]["Enable"]
		self.distribution = scoring_rules["Randomization"]["Distribution"] if self.randomize else None
		self.standard_deviation = scoring_rules["Randomization"]["Standard Deviation"] if self.distribution == "normal" else None
		self.bounds = scoring_rules["Randomization"]["Bounds"] if self.distribution == "uniform" else None
		self.flip_parity = scoring_rules["Randomization"]["Flip Parity"] if self.randomize else None

		self.points = self.random_transform(scoring_rules["Points"])
		self.field_goals = self.random_transform(scoring_rules["Field Goals"])
		self.field_goal_attempts = self.random_transform(scoring_rules["Field Goal Attempts"])
		self.free_throws = self.random_transform(scoring_rules["Free Throws"])
		self.free_throw_attempts = self.random_transform(scoring_rules["Free Throw Attempts"])
		self.offensive_rebounds = self.random_transform(scoring_rules["Offensive Rebounds"])
		self.defensive_rebounds = self.random_transform(scoring_rules["Defensive Rebounds"])
		self.steals = self.random_transform(scoring_rules["Steals"])
		self.assists = self.random_transform(scoring_rules["Assists"])
		self.blocks = self.random_transform(scoring_rules["Blocks"])
		self.turnovers = self.random_transform(scoring_rules["Turnovers"])
		self.personal_fouls = self.random_transform(scoring_rules["Personal Fouls"])

	def random_transform(self, original_number):
		if not self.randomize:
			return original_number

		if self.distribution == "normal":
			transformed = random.gauss(original_number, self.standard_deviation)
		else:
			transformed = (random.random() * (2 * self.bounds)) + original_number
		
		if not self.flip_parity:
			return transformed
		if (transformed < 0 and original_number > 0) or (transformed > 0 and original_number < 0):
			return 0

		return original_number

	def points_coeff(self):
		return self.points

	def field_goals_coeff(self):
		return self.field_goals

	def field_goal_attempts_coeff(self):
		return self.field_goal_attempts

	def free_throws_coeff(self):
		return self.free_throws

	def free_throw_attempts_coeff(self):
		return self.free_throw_attempts

	def offensive_rebounds_coeff(self):
		return self.offensive_rebounds

	def defensive_rebounds_coeff(self):
		return self.defensive_rebounds

	def steals_coeff(self):
		return self.steals

	def assists_coeff(self):
		return self.assists
	
	def blocks_coeff(self):
		return self.blocks

	def turnovers_coeff(self):
		return self.turnovers

	def personal_fouls_coeff(self):
		return self.personal_fouls

	def display_weights(self):
		print()
		print("Points:", round(self.points, 2))
		print("Field Goals:", round(self.field_goals, 2))
		print("Field Goal Attempts:", round(self.field_goal_attempts, 2))
		print("Free Throws:", round(self.free_throws, 2))
		print("Free Throw Attempts:", round(self.free_throw_attempts, 2))
		print("Offensive Rebounds:", round(self.offensive_rebounds, 2))
		print("Defensive Rebounds:", round(self.defensive_rebounds, 2))
		print("Steals", round(self.steals, 2))
		print("Assists", round(self.assists, 2))
		print("Blocks", round(self.blocks, 2))
		print("Turnovers", round(self.turnovers, 2))
		print("Personal Fouls", round(self.personal_fouls, 2))
		print()
