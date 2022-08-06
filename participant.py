from team import Team
from player import Player
from draft_picks import DraftPickStore
import re, sys, random

class Participant:

	def __init__(self, name, rules, team_name=None, autodraft=False):
		self.name = name
		self.team = Team(rules=rules.get_team_rules(), name=team_name)
		self.championships_won = 0
		self.wins_this_season = 0
		self.losses_this_season = 0
		self.wins_last_season = 0
		self.losses_last_season = 0
		self.draft_picks = DraftPickStore(name, rules.get_draft_rules())
		self.points_this_year = 0
		self.autodraft = autodraft
		self.rules = rules
		self.max_roster_size = self.rules.get_team_rules().get_roster_size()
		self.lineup_size = self.rules.get_team_rules().get_lineup_size()
		self.year = 1
		self.total_results = []
		self.points_results = []

	def __str__(self):
		return self.name

	def __len__(self):
		return len(self.team)

	def __contains__(self, player):
		return player in self.team

	def restore_to_health(self):
		self.team.restore_to_health()

	def update_health_status(self):
		self.team.update_health_status()

	def find_star(self):
		return self.team.find_star()

	def play_game(self):
		game = self.team.play_game()
		game.set_scoring_rules(self.rules.get_scoring_rules())
		return game

	def start_championship(self):
		self.team.start_championship()	

	def add_game(self, win, points):
		self.points_this_year += points
		if win:
			self.wins_this_season += 1
		else:
			self.losses_this_season += 1

	def update_from_box_score(self, box_score):
		self.team.update_from_box_score(box_score)

	def end_season(self, ranking):
		self.team.age()
		self.points_results.append(self.points_this_year)
		self.wins_last_season = self.wins_this_season + (self.points_this_year / 1000) + (random.random() / 100000) # for tiebreaking
		self.losses_last_season = self.losses_this_season
		self.wins_this_season = 0
		self.losses_this_season = 0
		self.points_this_year = 0
		self.year += 1
		self.total_results.append(ranking)

	def send_pick_to_commissioner(self, draftable_players):
		if not self.autodraft:
			return input().strip(" ")
		else:
			return draftable_players[-1].get_name()

	def get_drafter_name(self, year, current_round, one_index=True):
		return self.draft_picks.get_pick_owner(year, current_round, one_index)

	def draft_player(self, player):
		return self.team.draft_player(player)

	def add_player(self, player):
		return self.team.add_player(player)

	def remove_player(self, player):
		return self.team.cut_player(player)

	def check_roster_eligibility(self):
		return self.team.is_eligible()

	def execute_move(self, move):

		if re.match("start (.*)", move) != None:
			return self.team.move_player_to_starting_lineup(re.match("start (.*)", move).groups(1)[0])
		elif re.match("bench (.*)", move) != None:
			return self.team.remove_player_from_starting_lineup(re.match("bench (.*)", move).groups(1)[0])
		elif re.match("cut (.*)", move) != None:
			player = self.team.cut_player(re.match("cut (.*)", move).groups(1)[0])
			return player
		elif re.match("flip the team", move) != None:
			return self.team.flip_the_team()
		elif move in ["display team", "dt", ""]:
			print()
			print(self.team)
			print()
			return self.team != None
		else:
			print("Error: command not recognized", file=sys.stderr)
			return False

	def add_championship(self):
		self.championships_won += 1

	def get_name(self):
		return self.name

	def get_team(self):
		return self.team

	def get_total_results(self, year_by_year=True):
		if year_by_year:
			return self.total_results
		worst_rank = max(self.total_results)
		cumulative = [0 for i in range(worst_rank)]
		for rank in self.total_results:
			cumulative[rank - 1] += 1

		return cumulative

	def get_championships(self):
		return self.championships_won

	def get_wins_this_season(self):
		return self.wins_this_season

	def get_losses_this_season(self):
		return self.losses_this_season

	def get_wins_last_season(self):
		return self.wins_last_season

	def get_losses_last_season(self):
		return self.losses_last_season

	def get_record(self):
		return (self.wins_this_season, losses_this_season)

	def get_games_played(self):
		return self.wins_this_season + self.losses_this_season

	def get_ppg_this_season(self):
		return round(self.points_this_year / self.get_games_played(), 1)

	def get_championships(self):
		return self.championships_won

	def get_pick_by_year_and_round(self, year, pick_round):
		return self.draft_picks.get_pick_owner(year, pick_round)

	def transfer_pick(self, pick, recipient, suppress_check=False):
		self.draft_picks.transfer_pick(pick, recipient, suppress_check=suppress_check)

	def get_all_player_stats(self):
		return self.team.get_all_player_stats()

	def is_a_person(self):
		return True

	def can_accept_trade(self, sending_length, receiving_length):
		return len(self.team) + receiving_length - sending_length <= self.max_roster_size

	@staticmethod
	def get_participant_by_name(name, participant_list):
		for participant in participant_list:
			if participant.get_name() == name:
				return participant
		return None

		