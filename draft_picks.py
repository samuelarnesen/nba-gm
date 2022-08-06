import sys

class DraftPickStore:

	def __init__(self, name, draft_rules):
		self.name = name
		self.store = []
		for year in range(10):
			self.store.append([])
			num_rounds, _, _, _ = draft_rules.get_properties_this_year(year, one_index=False)
			for round_number in range(num_rounds):
				self.store[-1].append(name)

	def get_pick_owner(self, year, current_round, one_index=True):
		if one_index:
			year -= 1
			current_round -= 1
		if year < 0 or year >= len(self.store):
			print("Error: pick is not an eligible pick", file=sys.stderr)
			return ""
		if current_round < 0 or current_round >= len(self.store[year]):
			print("Error: pick is not an eligible pick", file=sys.stderr)
			return ""
		return self.store[year][current_round]

	def transfer_pick(self, pick, recipient, one_index=True, suppress_check=False):
		year, owner, pick_round = pick

		if not suppress_check:
			if self.get_pick_owner(year, pick_round) != owner:
				print("Error: pick could not be transferred because it is not owned by sender", file=sys.stderr)
				return False

		if one_index:
			self.store[year - 1][pick_round - 1] = recipient
		else:
			self.store[year][pick_round] = recipient
