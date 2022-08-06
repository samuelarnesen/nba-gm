from enum import Enum, auto

class Event(Enum):
	GAME = auto()
	SEASON_BREAK = auto()

class Scheduler:

	@staticmethod
	def schedule(participants, number_of_breaks):
		max_games = 82
		num_cycles = int(max_games / (len(participants) - 1))

		games_played_per_participant = {}
		for participant in participants:
			games_played_per_participant[participant] = 0

		break_points = [int(max_games * (break_num / (number_of_breaks + 1))) for break_num in range(1, number_of_breaks + 1)]
		expected_breaks = []
		for i in range(max_games):
			if i in break_points:
				expected_breaks.append(expected_breaks[-1] + 1 if i > 0 else 1)
			else:
				expected_breaks.append(expected_breaks[-1] if i > 0 else 0)

		breaks_so_far = 0
		matchups = []
		for cycle in range(num_cycles):
			for i, contender_one in enumerate(participants):
				for contender_two in participants[i + 1:]:
					matchups.append((Event.GAME, (contender_one, contender_two)))
					games_played_per_participant[contender_one] += 1
					games_played_per_participant[contender_two] += 1

			games_played = games_played_per_participant[participants[0]] # all teams will have played the same number of games here so key doesn't matter
			if games_played < len(expected_breaks) and breaks_so_far < expected_breaks[games_played]:
				matchups.append((Event.SEASON_BREAK, (None, None)))
				breaks_so_far += 1

		least_played_pairs = sorted([(games_played_per_participant[participant], participant) for participant in participants], key=lambda x: x[0])
		least_played_games = [games for games, _  in least_played_pairs]

		while min(least_played_games) != max(least_played_games) or min(least_played_games) < max_games:

			matchups.append((Event.GAME, (least_played_pairs[0][1], least_played_pairs[1][1])))
			games_played_per_participant[least_played_pairs[0][1]] += 1
			games_played_per_participant[least_played_pairs[1][1]] += 1

			least_played_pairs = sorted([(games_played_per_participant[participant], participant) for participant in participants], key=lambda x: x[0])
			least_played_games = [games for games, _  in least_played_pairs]

			if min(least_played_games) == max(least_played_games) and breaks_so_far < expected_breaks[games_played]:
				matchups.append((Event.SEASON_BREAK, (None, None)))
				breaks_so_far += 1

		return matchups

