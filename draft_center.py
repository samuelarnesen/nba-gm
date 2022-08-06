from player import PlayerGroup
from participant import Participant
import random, sys, copy

class DraftCenter:

	def __init__(self):

		self.order = PlayerGroup()
		self.current_draft_index = 0
		self.players_added = False
		self.aliases_to_player = {}
		self.player_to_aliases = {}

	def add_players(self, data, use_scouting_reports=False, number_of_games_of_scouting=0):

		player_names = data.get_player_names()
		names = copy.deepcopy(player_names)
		random.shuffle(names)
		self.order = PlayerGroup([(name, data.get_player_data(name), random.randint(3, 5)) for name in names])
		self.players_added = True

		current_alias = 0
		for name in names:
			self.aliases_to_player[str(current_alias)] = name
			self.player_to_aliases[name] = str(current_alias)
			if use_scouting_reports:
				if random.random() < 0.5:
					player = self.order.get_player_by_name(name)
					player.generate_scouting_report(number_of_games_of_scouting)
					player.set_alias(current_alias)
			current_alias += 1

	def get_draft_order(self, participants, reigning_champion=None):

		if not self.players_added:
			print("Error: MatchupCenter not established yet. Please add player", file=sys.stderr)
			return None, None

		random.shuffle(participants)
		last_years_results = [participant.get_wins_last_season() for participant in participants]
		draft_order = [participant for _, participant in sorted(zip(last_years_results, participants), key=lambda pair: pair[0])]
		if isinstance(reigning_champion, Participant):
			if draft_order[-1].get_name() != reigning_champion.get_name():
				draft_order[-2] = draft_order[-1]
				draft_order[-1] = reigning_champion
		reverse_draft_order = list(reversed(draft_order))

		return draft_order, reverse_draft_order

	def get_draftable_players(self, players_to_add, free_agents=PlayerGroup()):

		draft_group = PlayerGroup([player for player in free_agents]) if len(free_agents) > 0 else PlayerGroup()
		for i in range(players_to_add):
			if self.current_draft_index < len(self.order):
				draft_group.append(self.order[self.current_draft_index])
				self.current_draft_index += 1

		return draft_group

	def get_all_players(self):
		return copy.deepcopy(self.order)

	def get_alias_from_player(self, player_name):
		if player_name in self.player_to_aliases:
			self.player_to_aliases[player_name]
		return ""

	def get_player_from_alias(self, alias):
		if alias in self.aliases_to_player:
			return self.aliases_to_player[alias]
		return ""


