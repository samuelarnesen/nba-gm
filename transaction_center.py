import sys
from enum import Enum, auto
from command_parser import CommandParser, Commands
from participant import Participant
from player import Player

class TransactionResult(Enum):
	FAILURE = auto()
	SUCCESS_CUT_PLAYER = auto()
	SUCCESS_NO_ACTION = auto()
	NOT_RECOGNIZED = auto()

class TransactionCenter:

	@staticmethod
	def read_input(outside_command=None):
		input_value = outside_command
		if outside_command == None:
			input_value = input()
		return input_value

	@staticmethod
	def accept_commands(participants, outside_command=None):
		results = []
		extras = []

		input_value = TransactionCenter.read_input(outside_command)
		command, args = CommandParser.parse_command(input_value)
		while command != Commands.CONTINUE and not TransactionCenter.all_participants_ready(participants):
			result = None
			extra = None
			if command == Commands.CLEAR:
				result = TransactionCenter.clear()
				print("Command executed")
			elif command == Commands.ROSTER_MOVE:
				results, extra = TransactionCenter.process_roster_move(participants, args)
				print("Command executed")
			elif command == Commands.TRADE:
				result = TransactionCenter.process_trade(participants, args)
				print("Command executed")
			elif command == Commands.READY:
				TransactionCenter.mark_participant_as_ready(participants, args)
			else:
				print("Warn: Do not recognize command. Input was {}. Outside command was {}".format(input_value, outside_command), file=sys.stderr)


			if not isinstance(result, type(None)):
				results.append(result)
			if not isinstance(extra, type(None)):
				for player in extra:
					extras.append(player)

			if outside_command != None:
				break

			if TransactionCenter.all_participants_ready(participants):
				break

			input_value = TransactionCenter.read_input(outside_command=None)
			command, args = CommandParser.parse_command(input_value)

		TransactionCenter.reset_all_participant_ready_status(participants)
		return results, extras

	
	@staticmethod
	def process_trade(participants, args):

		def meets_roster_size_limits(party, sending_length, receiving_length):
			if not party.can_accept_trade(sending_length, receiving_length):
				print("Warn: {} would have too many players.".format(party))
				return False
			return True

		def has_players_check(party, senders):
			for player in senders:
				if player not in party:
					print("Warn: {} does not have {}".format(party, player))
					return False
			return True

		def has_picks_check(party, picks):
			for pick in picks:
				year, name, pick_round = pick
				if party.get_pick_by_year_and_round(year, pick_round) != name:
					print("Warn: {} does not own pick".format(party), file=sys.stderr)
					return False
			return True

		def send_players(party, senders):
			sending_players = []
			for player in senders:
				leaving_player = party.remove_player(player)
				sending_players.append(leaving_player)

			return sending_players

		def receive_players(party, receivers):
			for player in receivers:
				party.add_player(player)

		def send_picks(party, picks_to_send, recipient):
			for pick in picks_to_send:
				sending_party = Participant.get_participant_by_name(pick[1], participants)
				sending_party.transfer_pick(pick, recipient, suppress_check=True)

		party_one = Participant.get_participant_by_name(args[0], participants)
		party_two = Participant.get_participant_by_name(args[2], participants)
		party_one_senders = args[1]
		party_two_senders = args[3]
		party_one_pick_senders = args[4]
		party_two_pick_senders = args[5]

		if not isinstance(party_one, Participant) or not isinstance(party_two, Participant):
			print("Warn: At least one participant could not be found", file=sys.stderr)
			return TransactionResult.FAILURE

		if not meets_roster_size_limits(party_one, len(party_one_senders), len(party_two_senders)):
			return TransactionResult.FAILURE

		if not meets_roster_size_limits(party_two, len(party_two_senders), len(party_one_senders)):
			return TransactionResult.FAILURE

		if not has_players_check(party_one, party_one_senders) or not has_players_check(party_two, party_two_senders):
			return TransactionResult.FAILURE

		if not has_picks_check(party_one, party_one_pick_senders) or not has_picks_check(party_two, party_two_pick_senders):
			return TransactionResult.FAILURE

		players_to_send_to_two = send_players(party_one, party_one_senders)
		players_to_send_to_one = send_players(party_two, party_two_senders)
		receive_players(party_one, players_to_send_to_one)
		receive_players(party_two, players_to_send_to_two)

		send_picks(party_one, party_one_pick_senders, party_two.get_name())
		send_picks(party_two, party_two_pick_senders, party_one.get_name())

		print("Trade complete\n")
		return TransactionResult.SUCCESS_NO_ACTION

	@staticmethod
	def process_roster_move(participants, args):

		participant_name = args[0]
		moves = args[1]

		responses = []
		cut_players = []
		participant = Participant.get_participant_by_name(participant_name, participants)
		if participant != None:
			participant.reset_ready()
			for move in moves:
				result = participant.execute_move(move.strip(" \n"))
				if isinstance(result, Player):
					cut_players.append(result)
					responses.append(TransactionResult.SUCCESS_CUT_PLAYER)
				else:
					responses.append(TransactionResult.SUCCESS_NO_ACTION if result != False else TransactionResult.FAILURE)
			if len(moves) > 1:
				participant.execute_move("display team")
		else:
			print("Warn: did not recognize participant", file=sys.stderr)
			responses.append(TransactionResult.FAILURE)

		return responses, cut_players

	@staticmethod
	def clear(participants):
		for i in range(50):
			print()
		print("Accepting commands")
		return TransactionResult.SUCCESS_NO_ACTION

	@staticmethod
	def all_participants_ready(participants):
		for participant in participants:
			if not participant.is_ready():
				return False
		return True

	@staticmethod
	def reset_all_participant_ready_status(participants):
		for participant in participants:
			participant.reset_ready()

	@staticmethod
	def mark_participant_as_ready(participants, args):
		participant = Participant.get_participant_by_name(args[0], participants)
		if participant is not None:
			participant.mark_ready()
