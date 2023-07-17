from enum import Enum, auto
import re

class Commands(Enum):
	ROSTER_MOVE = auto()
	TRADE = auto()
	CLEAR = auto()
	NOT_RECOGNIZED = auto()
	CONTINUE = auto()
	READY = auto()

class CommandParser:

	@staticmethod
	def parse_command(command):

		def split_into_picks_and_players(series):
			picks = []
			players = []
			for item in series.split(", "):
				pick_match = re.match("(\d+)-(.*)-(\d+)", item)
				if pick_match != None:
					picks.append((int(pick_match.group(1)), pick_match.group(2), int(pick_match.group(3))))
				else:
					players.append(item)
			return players, picks

		command = command.strip(" ")

		if command == "clear":
			return Commands.CLEAR, None

		if command == "continue":
			return Commands.CONTINUE, None

		if ":" in command:
			split_command = command.split(":")
			if len(split_command) == 2 and split_command[1].lower().strip() == "ready":
				return Commands.READY, (split_command[0],)
			return Commands.ROSTER_MOVE, (split_command[0], split_command[1].split(","))

		trade_match = re.match("Trade (.*) from (.*) to (.*) for (.*)", command)
		if trade_match != None:
			party_one_player_senders, party_one_pick_senders = split_into_picks_and_players(trade_match.group(1))
			party_one_senders = trade_match.group(1).split(", ")
			party_one = trade_match.group(2)
			party_two = trade_match.group(3)
			party_two_player_senders, party_two_pick_senders = split_into_picks_and_players(trade_match.group(4))

			return Commands.TRADE, (party_one, party_one_player_senders, party_two, party_two_player_senders, party_one_pick_senders, party_two_pick_senders)

		return Commands.NOT_RECOGNIZED, None

