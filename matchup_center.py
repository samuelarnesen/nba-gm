import random, sys
from player import Player

class MatchupCenter:

	@staticmethod
	def play_game(contender_one, contender_two, display=False, play_by_play=False, roto=False, detailed_display=False):
		if play_by_play:
			return MatchupCenter.play_by_play_game(contender_one, contender_two, display)
		else:
			return MatchupCenter.play_regular_game(contender_one, contender_two, display, roto, detailed_display)

	@staticmethod
	def play_regular_game(contender_one, contender_two, display=False, roto=False, detailed_display=False):
		contender_one_game = contender_one.play_game()
		contender_two_game = contender_two.play_game()

		contender_one_score = contender_one_game.score(other=contender_two_game, roto=roto)
		contender_two_score = contender_two_game.score(other=contender_one_game, roto=roto)

		winner = contender_one if contender_one_score >= contender_two_score else contender_two
		if display:
			print("{} ({}) - {} ({})". format(contender_one.get_name(), round(contender_one_score, 2), contender_two, round(contender_two_score, 2)))
			if detailed_display:
				print(contender_one, contender_one_game)
				print(contender_two, contender_two_game)
				print()

		return winner, (contender_one_game, contender_two_game), (contender_one_score, contender_two_score)


	@staticmethod
	def play_by_play_game(contender_one, contender_two, display=False, max_possessions=200):

		def choose_assister(team, shooter):
			other_players = list(filter(lambda x: x != shooter, [player for player in team.get_starters()]))

			prob_not_assisted = 1
			for player in other_players:
				prob_not_assisted *= (1 - player.get_stats().get_assist_percentage())
			
			if random.random() < prob_not_assisted:
				return None
			else:
				return random.choices(other_players, k=1, weights=[player.get_stats().get_assist_percentage() for player in other_players])[0]

		def turnover(shooter):
			return random.random() < shooter.get_stats().get_turnover_percentage()

		def shot(shooter, assisted, defensive_bpm):
			three_pointer = random.random() < shooter.get_stats().get_three_point_attempt_rate()
			success_rate = shooter.get_stats().get_three_point_percentage() if three_pointer else shooter.get_stats().get_two_point_percentage()
			success_rate = success_rate + (0.025 if three_pointer else 0.05) if assisted else success_rate - (0.025 if three_pointer else 0.05)
			return random.random() - defensive_bpm < success_rate, three_pointer

		def choose_shooter(team):
			return random.choices(team.get_starters(), k=1, weights=[player.get_stats().get_usage_rate() for player in team.get_starters()])[0]

		def rebound(offensive_team, defensive_team):
			team_offensive_rebound_pct = 1
			for player in offensive_team.get_starters():
				team_offensive_rebound_pct *= (1 - player.get_stats().get_offensive_rebound_percentage())
			team_offensive_rebound_pct = 1 - team_offensive_rebound_pct

			team_defensive_rebound_pct = 1
			for player in defensive_team.get_starters():
				team_defensive_rebound_pct *= (1 - player.get_stats().get_defensive_rebound_percentage())
			team_defensive_rebound_pct = 1 - team_defensive_rebound_pct

			team_offensive_rebound_pct /= (team_offensive_rebound_pct + team_defensive_rebound_pct)
			offensive_rebound = random.random() < team_offensive_rebound_pct

			if offensive_rebound:
				rebounder = random.choices(offensive_team.get_starters(), k=1, weights=[player.get_stats().get_offensive_rebound_percentage() for player in offensive_team.get_starters()])[0]
				return rebounder, True
			else:
				rebounder = random.choices(defensive_team.get_starters(), k=1, weights=[player.get_stats().get_defensive_rebound_percentage() for player in defensive_team.get_starters()])[0]
				return rebounder, False

		def possession(offensive_team, defensive_team, offensive_team_box_score, defensive_team_box_score):
			shooter = choose_shooter(offensive_team)
			if turnover(shooter):
				return defensive_team
			assister = choose_assister(offensive_team, shooter)
			defense_effect = sum([player.get_stats().get_defensive_bpm() for player in defensive_team.get_starters()]) / len(defensive_team.get_starters())
			success, three_pointer = shot(shooter, isinstance(assister, Player), defense_effect)
			if not success:
				rebounder, offensive_rebound = rebound(offensive_team, defensive_team)
				offensive_team_box_score.add_rebound(rebounder) if offensive_rebound else defensive_team_box_score.add_rebound(rebounder)
				return offensive_team if offensive_rebound else defensive_team
			else:
				offensive_team_box_score.add_points(shooter, 3 if three_pointer else 2)
				offensive_team_box_score.add_assist(assister)
				return defensive_team

		team_one = contender_one.get_team()
		team_two = contender_two.get_team()
		team_one_box_score = BoxScore(team_one)
		team_two_box_score = BoxScore(team_two)
		offensive_team = team_one if random.random() < 0.5 else team_two
		for possession_count in range(max_possessions):
			if offensive_team == team_one:
				offensive_team = possession(team_one, team_two, team_one_box_score, team_two_box_score)
			else:
				offensive_team = possession(team_two, team_one, team_two_box_score, team_one_box_score)

		winner = contender_one if team_one_box_score.score() > team_two_box_score.score() else contender_two
		if display:
			print("{} ({}) - {} ({})". format(contender_one.get_name(), round(team_one_box_score.score(), 1), contender_two, round(team_two_box_score.score(), 1)))

		return winner, (team_one_box_score, team_two_box_score)

class BoxScore:

	def __init__(self, team):
		self.stats = {}
		for player in team.get_starters():
			self.stats[player.get_name()] = {"Points": 0, "Rebounds": 0, "Assists": 0}
		self.team_points = 0

	def add_points(self, player, points_to_add):
		self.stats[player.get_name()]["Points"] += points_to_add
		self.team_points += points_to_add

	def add_rebound(self, player):
		self.stats[player.get_name()]["Rebounds"] += 1

	def add_assist(self, player):
		if isinstance(player, Player):
			self.stats[player.get_name()]["Assists"] += 1

	def get_points(self, player):
		return self.stats[player.get_name()]["Points"]

	def get_rebounds(self, player):
		return self.stats[player.get_name()]["Rebounds"]

	def get_assists(self, player):
		return self.stats[player.get_name()]["Assists"]

	def score(self):
		return self.team_points

	def __str__(self):
		return "\n".join(["{}: {} / {} / {}".format(name, self.stats[name]["Points"], self.stats[name]["Rebounds"], self.stats[name]["Assists"]) for name in self.stats])

	def __contains__(self, key):
		return key in self.stats

	def __getitem__(self, name):
		return self.stats[name]



