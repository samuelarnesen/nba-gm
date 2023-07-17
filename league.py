from participant import Participant
from data import Database
from player import Player, PlayerGroup
from agent import Agent, DifficultyMode
from rules import Rules
from matchup_center import MatchupCenter
from draft_center import DraftCenter
from transaction_center import TransactionCenter, TransactionResult
from scheduler import Scheduler, Event
import json, random, copy, sys, re, time, operator

class League:

	def __init__(self):
		self.participants = []
		self.data = None
		self.free_agents = PlayerGroup()
		self.draft_center = DraftCenter()
		self.max_roster_size = 12
		self.lineup_size = 6
		self.reigning_champion = None
		self.reigning_finalist = None
		self.current_year = 1
		self.rules = None

	def load_from_config(self, config_path="./config.json"):
		with open(config_path) as f:
			json_obj = json.load(f)

		self.rules = Rules(json_obj)
		self.data = Database(json_obj["Data Path"], self.rules, json_obj["Positional Data Path"])
		self.draft_center.set_roto_mode(self.rules.is_roto())

		for participant in json_obj["Participants"]:
			if participant["Autodraft"]:
				participant_to_add = Agent(participant["Name"], self.rules, participant["Team Name"], participant["Autodraft"])
				participant_to_add.set_mode(participant["Mode"], participant["Tank"], threshold=6)
			else:
				participant_to_add = Participant(participant["Name"], self.rules, participant["Team Name"], participant["Autodraft"])
			self.participants.append(participant_to_add)

	def start_league(self):
		self.rules.get_scoring_rules().display_weights()

		draft_rules = self.rules.get_draft_rules()
		self.draft_center.add_players(self.data, draft_rules.use_scouting(1), draft_rules.get_number_of_games_of_scouting(1))
	
	def run_draft(self, year):

		self.current_year = year + 1
		number_of_rounds, snake, scouting, scouting_games = self.rules.get_draft_rules().get_properties_this_year(self.current_year)
		draft_order, reverse_draft_order = self.draft_center.get_draft_order(self.participants, self.reigning_champion, self.reigning_finalist)

		print("Draft Order")
		for i, participant in enumerate(draft_order):
			print("{}. {}".format(i + 1, participant))
		print()

		self.accept_commands()

		players_to_add = (number_of_rounds * len(self.participants)) if year != 0 else ((number_of_rounds + 1) * len(self.participants))
		draft_group = self.draft_center.get_draftable_players(players_to_add, self.free_agents)

		for current_round in range(number_of_rounds):
			order_to_use = reverse_draft_order if snake and current_round % 2 == 1 else draft_order

			for participant in order_to_use:

				if len(draft_group) == 0:
					print("There are no players available to draft")
					return

				print("\n\nAvailable Players")
				for player in draft_group:
					print(player)
				print()

				valid_selection = False
				while not valid_selection:
					drafter = Participant.get_participant_by_name(participant.get_drafter_name(year, current_round, one_index=False), self.participants)
					print("{}'s turn to select:\n".format(drafter))
					selection = drafter.send_pick_to_commissioner(draft_group)

					if selection == "pass":
						valid_selection = True
					elif selection in draft_group or (self.draft_center.get_player_from_alias(selection) in draft_group and scouting):
						real_selection = selection if (not scouting or selection in draft_group) else self.draft_center.get_player_from_alias(selection)
						player = draft_group.get_player_by_name(real_selection)
						drafter.draft_player(player)
						draft_group.remove(real_selection)
						valid_selection = True
					else:
						response = self.accept_commands(command=selection, display=False)
						if response == TransactionResult.FAILURE:
							print("{} is not a draftable player or a recognized command".format(selection))

		self.free_agents = PlayerGroup([player for player in draft_group])

	def check_roster_eligibility(self):

		second_place = list(reversed(sorted([participant.get_wins_this_season() for participant in self.participants])))[1]
		for participant in self.participants:
			if not participant.is_a_person():
				participant.set_lineup(self.current_year, games_out=second_place - participant.get_wins_this_season())

		all_eligible = True
		for participant in self.participants:
			team_eligible = participant.check_roster_eligibility()
			if not team_eligible:
				print("Warn: {}'s lineup is not eligible".format(participant.get_name()))
			all_eligible = all_eligible and team_eligible
		return all_eligible

	def run_season(self, breakpoints=[]):

		self.update_health_of_teams(guarantee_health=True)
		self.accept_commands()
		season_started = self.check_roster_eligibility()

		while not season_started:
			print("Season failed to start. At least one roster is not eligible")
			self.accept_commands()
			season_started = self.check_roster_eligibility()

		for event_type, (contender_one, contender_two) in Scheduler.schedule(self.participants, 2):
			if event_type == Event.GAME:
				if random.random() > 0.5:
					winner, (contender_one_game, contender_two_game), (contender_one_score, contender_two_score) = MatchupCenter.play_game(contender_one, contender_two, False, self.rules.play_by_play_mode(), self.rules.is_roto())
				else:
					 winner, (contender_two_game, contender_one_game), (contender_two_score, contender_one_score) = MatchupCenter.play_game(contender_two, contender_one, False, self.rules.play_by_play_mode(), self.rules.is_roto())
				contender_one.add_game(contender_one==winner, contender_one_score, game=contender_one_game, other=contender_two_game)
				contender_two.add_game(contender_two==winner, contender_two_score, game=contender_two_game, other=contender_one_game)

				if self.rules.play_by_play_mode():
					contender_one.update_from_box_score(contender_one_game)
					contender_two.update_from_box_score(contender_two_game)

			elif event_type == Event.SEASON_BREAK:
				self.get_rankings(display=True)
				self.update_health_of_teams(guarantee_health=(False or not self.rules.get_team_rules().allow_injuries_mode()))
				self.accept_commands()
				acceptible_teams = self.check_roster_eligibility()
				if not acceptible_teams:
					print("Warn: One team does not meet roster rules")
					self.accept_commands()
					acceptible_teams = self.check_roster_eligibility()

		print("The season is over")
		self.sleep(1)
		print("This year's standings are...")
		self.sleep(3)
		rankings = self.get_rankings(display=True)

		if not self.rules.play_by_play_mode() and not self.rules.is_roto():
			self.sleep(3)
			print("This year's MVP is...")
			self.sleep(3)
			mvp, mvp_stats = self.find_mvp()
			print("{}! ({}ppg)\n\n".format(mvp.get_name().upper(), mvp_stats))
			self.sleep(3)
			print("The members of this year's First Team All-NBA are...")
			all_stars = self.find_all_stars(5)
			for (star, total_points) in all_stars:
				print("{} ({})".format(star.get_name(), round(total_points / 82), 1))
			print()
			self.sleep(3)


	def run_championship(self, dramatic=True):
		rankings = self.get_rankings(display=False)
		contender_one = rankings[0]
		contender_two = rankings[1]

		print("The finals matchup is...")
		print("1. {} v 2. {}".format(contender_one, contender_two))
		for participant in self.participants:
			participant.start_championship()

		self.update_health_of_teams(guarantee_health=True)
		self.accept_commands()

		contender_one_wins = 0
		for game in range(7):
			if dramatic:
				self.sleep(2)
			print(f"Finals Game {(game + 1)}")
			winner, _, _ = MatchupCenter.play_game(contender_one, contender_two, display=True, play_by_play=self.rules.play_by_play_mode(), roto=self.rules.is_roto())
			contender_one_wins = contender_one_wins + 1 if winner == contender_one else contender_one_wins
			print("{} ({}) - {} ({})\n".format(contender_one, contender_one_wins, contender_two, (game + 1) - contender_one_wins))
			if contender_one_wins >= 4 or ((game + 1) - contender_one_wins) >= 4:
				break

		champion = contender_one if contender_one_wins >= 4 else contender_two
		finalist = contender_one if contender_one_wins < 4 else contender_two
		champion.add_championship()
		finalist.add_championship_lost()

		self.sleep(1)
		print("\n...And your champion is...")
		self.sleep(1)
		print("{} in {} games!!!\n".format(champion.get_name().upper(), game + 1))
		self.sleep(2)
		self.reigning_champion = champion
		self.reigning_finalist = finalist

		if not self.rules.play_by_play_mode() and not self.rules.is_roto():
			print("This year's Finals MVP is...")
			self.sleep(3)
			mvp, mvp_score = champion.find_star()
			print("{}! ({}ppg)\n\n".format(mvp.get_name().upper(), round(mvp_score / (game + 1), 2)))
			self.sleep(3)

		return champion, (contender_one, contender_two), (contender_one_wins, game - contender_one_wins)

	def end_season(self):

		rankings = [participant.get_name() for participant in self.get_rankings()]
		for participant in self.participants:
			participant.end_season(ranking=rankings.index(participant.get_name()) + 1)

		free_agents_to_remove = []
		for free_agent in self.free_agents:
			free_agent.age()
			if free_agent.is_expired():
				free_agents_to_remove.append(free_agent)

		for free_agent in free_agents_to_remove:
			self.free_agents.remove(free_agent)

	def accept_commands(self, command=None, display=True):
		if display:
			print("\nAccepting commands")

		results, extras = TransactionCenter.accept_commands(self.participants, command)

		for extra in extras:
			print(extra)
			self.free_agents.append(extra)

		if command != None:
			return TransactionResult.FAILURE if TransactionResult.FAILURE in results else TransactionResult.SUCCESS_NO_ACTION


	def display_final_results(self):
		print()
		print("Final Results")
		for participant in self.participants:
			total_results = participant.get_total_results(year_by_year=False)
			print("{}: {} wins, {} Finals".format(participant.get_name(), participant.get_championships(), participant.get_championships_lost()))

		print()
		self.sleep(3)
		if not self.rules.play_by_play_mode() and not self.rules.is_roto():
			print("Your All-Decade First Team is...")

			all_players = self.draft_center.get_all_players()
			active_players = [player for player in filter(lambda x: x.get_total_points() != 0, all_players)]
			average_player_pts = sum([player.get_total_points() for player in active_players]) / len(active_players)
			sorted_players = sorted(active_players, key=lambda x: x.get_total_points() - average_player_pts, reverse=True)

			for player in sorted_players[0:5]:
				print("{} ({}, {}, {})". format(player.get_name(), player.get_value(), player.get_games_started(), round(player.get_total_points(), 1)))
				self.sleep(1.5)
		print()
		print("End game")


	def get_rankings(self, display=False):
		rankings = sorted(self.participants, key=operator.methodcaller("get_ppg_this_season"), reverse=True)
		rankings = sorted(rankings, key=operator.methodcaller("get_wins_this_season"), reverse=True)
		if display:
			print()
			for i, participant in enumerate(rankings):
				display_stat = f"{participant.get_ppg_this_season()}ppg"  if not self.rules.is_roto() else f"({participant.get_ppg_this_season()}ppg, {participant.get_roto_stats()})"
				print("{}. {} ({}-{}, {})".format(i + 1, participant.get_name(), participant.get_wins_this_season(), \
					participant.get_losses_this_season(), display_stat))
			print()
		return rankings

	def find_mvp(self):
		mvp = None
		mvp_score = 0
		for participant in self.participants:
			star_player, star_score = participant.find_star()
			if star_score > mvp_score:
				mvp = star_player
				mvp_score = star_score
		return mvp, round(mvp_score / 82, 1)

	def find_all_stars(self, num_all_stars):
		all_player_stats = []
		for participant in self.participants:
			player_stats = participant.get_all_player_stats()
			for player_pair in player_stats:
				all_player_stats.append((player_pair[0], random.random(), player_pair[1]))

		sorted_results = list(reversed(sorted(all_player_stats)))
		sorted_results_real = [(player, points) for (points, _, player) in sorted_results]
		return sorted_results_real[:num_all_stars]

	def get_current_year(self):
		return self.current_year

	def update_health_of_teams(self, guarantee_health=False):
		for participant in self.participants:
			if guarantee_health:
				participant.restore_to_health()
			else:
				participant.update_health_status()

	def sleep(self, length):
		if self.rules.dramatic_mode():
			time.sleep(length)





