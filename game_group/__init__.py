from otree.api import *

import random
import time

import numpy as np

doc = """
Your app description
"""

def creating_session(subsession):

	if subsession.round_number == 1:
		# The below code only runs if we are running this app in isolation - not in the full experiment
		# If running this app in isolation, set the participant vars so that it works
		# For the full experiment, wait_page_arrival is set in previous app
		# For testing


		if subsession.session.config["name"] == "game_group":

			
			players = subsession.get_players()
			for player in players:

				player.participant.wait_page_arrival = time.time()

				player.participant.is_dropout = False
				player.participant.wrong_answers = []
				player.participant.exclusion = False
				player.participant.condition = np.random.choice(["group", "voting"])
				player.participant.switched = np.random.choice([True, False])

class C(BaseConstants):
	NAME_IN_URL = 'game_group'
	PLAYERS_PER_GROUP = None
	NUM_ROUNDS = 20
	TIMEOUT_GROUPING = 720
	TIMEOUT_CHOICE = 90
	TIMEOUT_INFO = 30

class Subsession(BaseSubsession):
	pass

class Group(BaseGroup):
	pass

class Player(BasePlayer):
	lottery_action = models.StringField(
		label="Please choose the lottery you would like to play this round.",
		choices=[
			['risky', 'Risky Lottery'],
			['safe', 'Safe Lottery']
		],
		widget=widgets.RadioSelect
	)

	voter_decision = models.IntegerField(
		label="Please vote for how many players you would like to play the risky lottery this round.",
		choices=[0,1,2,3,4,5],
		widget=widgets.RadioSelect
	)

	optimal_comprehension_group = models.StringField(
		label="For the group as a whole, the optimal total number of risky lotteries is . . .  ",
		choices=[
			["20", "The group in total plays 20 risky strategies over the entire game"], 
			["8", "The group in total plays 8 risky strategies over the entire game"], 
			["0", "The group in total plays 0 risky strategies over the entire game"],
		],
		widget=widgets.RadioSelect,
		initial=''
		)
	
	optimal_comprehension_indy = models.StringField(
		label="If each player wants the group to play the optimal number of risky lotteries, how many risky lotteries should each player play on average?",
		choices=[
			["5 to 6", "Each player plays 5 to 6 risky lotteries over the entire game"], 
			["1 to 2", "Each player plays 1 to 2 risky lotteries over the entire game"], 
			["0 to 1", "Each player plays 0 to 1 risky lotteries over the entire game"],
			["0", "Each player plays 0 risky lotteries over the entire game"],
		],
		widget=widgets.RadioSelect,
		initial=''
		)

	lottery_result = models.StringField()
	game_current_bonus = models.IntegerField()
	game_extinct = models.BooleanField()
	game_current_group_bonus = models.IntegerField()

def optimal_comprehension_group_error_message(player, value):
	if value != '8':
		player.participant.wrong_answers.append('optimal_comprehension_group')
		return 'That is not correct. Please try again.'
	
def optimal_comprehension_indy_error_message(player, value):
	if value != '1 to 2':
		player.participant.wrong_answers.append('optimal_comprehension_indy')
		return 'That is not correct. Please try again.'

def group_by_arrival_time_method(self, waiting_players):

	for player in waiting_players:
		if len(player.participant.wrong_answers) > 0:
			player.participant.unique_group_id = np.random.randint(1000000000)
			if 'information' in player.session.config:
				player.participant.information = player.session.config["information"]
			else:
				player.participant.information = np.random.choice(["none", "optimal"])
			return [player]

	for condition in ["group", "voting"]:
		players_in_condition = []
		for player in waiting_players:
			# Collect the players in each condition
			if player.participant.condition == condition and len(player.participant.wrong_answers) == 0:
				players_in_condition.append(player)
		# If there are enough players in the condition
		if len(players_in_condition) >= 5:
			this_group = players_in_condition[:5]
			unique_group_id = np.random.randint(1000000000)
			# Randomly choose information condition

			if 'information' in player.session.config:
				info_condition = player.session.config["information"]
			else:
				info_condition = np.random.choice(["none", "optimal"])

			for player in this_group:
				player.participant.information = info_condition
				player.participant.unique_group_id = unique_group_id
			return this_group

	# For players waiting too long
	for player in waiting_players:
		if waiting_too_long(player):
			player.participant.unique_group_id = np.random.randint(1000000000)

			if 'information' in player.session.config:
				player.participant.information = player.session.config["information"]
			else:
				player.participant.information = np.random.choice(["none", "optimal"])
			return [player]

def waiting_too_long(player):
	return time.time() - player.participant.wait_page_arrival > C.TIMEOUT_GROUPING

def set_game_vars(group):
	for player in group.get_players():
		player.participant.game_current_bonus = 0
		player.participant.game_extinct = False
		player.participant.game_current_group_bonus = 0

class GroupWaitPage(WaitPage):
	
	group_by_arrival_time = True
	after_all_players_arrive = 'set_game_vars'

	body_text = """
		<p>IT IS IMPORTANT THAT YOU KEEP THIS TAB ACTIVE.</p>
		You may have to wait a few minutes while the other players in your group catch up.
		Waiting more than 5 minutes? Try refreshing the page.
		"""
	
	def is_displayed(player):
		print("Game_group wait page 1: " , player.participant.vars)
		return player.round_number == 1 and player.participant.condition in ['group', 'voting']

def expected_value_strategy(n_risky, group_balance = 0, n_rounds=100, p_survive=0.95, e_risky=25, e_safe = 2.5):

	return p_survive**n_risky * (group_balance + e_risky * n_risky + e_safe * (n_rounds - n_risky))

def get_optimal_n_riskys(total_rounds_left, group_balance=0):

	n_riskys = list(range(total_rounds_left))
	expected_values = [expected_value_strategy(n_risky, group_balance=group_balance, n_rounds=total_rounds_left) for n_risky in n_riskys]

	# Get max n_riskys
	optimal_n_risky = n_riskys[np.argmax(expected_values)]

		# Optimal n_risky if integer or a fraction
	if optimal_n_risky % 5 == 0:
		optimal_n_risky_per_player = optimal_n_risky // 5
	else:
		optimal_n_risky_per_player = "{} to {}".format(optimal_n_risky // 5, int(optimal_n_risky//5 + 1))

	return optimal_n_risky, optimal_n_risky_per_player


class ConditionChoice(Page):

	form_model = "player"
	form_fields = ["condition_choice", "info_choice"]

	def is_displayed(player):
		return False
		#return player.round_number == 1

	def before_next_page(player, timeout_happened):        
		player.participant.condition = player.condition_choice
		player.participant.information = player.info_choice


class OptimalChoices(Page):
	
	timeout_seconds = C.TIMEOUT_CHOICE * 2

	form_model = 'player'
	form_fields = ['optimal_comprehension_group', 'optimal_comprehension_indy']

	def is_displayed(player):
		
		return player.round_number == 1 and player.participant.vars['condition'] != 'indy' and player.participant.vars['information'] == 'optimal'

	def vars_for_template(player):
	
		total_rounds_left = 100
		n_riskys = list(range(total_rounds_left))
		expected_values = [expected_value_strategy(n_risky) for n_risky in n_riskys]

		optimal_n_risky, optimal_n_risky_per_player = get_optimal_n_riskys(total_rounds_left=total_rounds_left)

		return {
			'optimal_n_risky': optimal_n_risky,
			'optimal_n_risky_per_player': optimal_n_risky_per_player,
			'n_riskys': n_riskys,
			'expected_values': expected_values
		}
	

class GetReady(Page):

	timeout_seconds = 120
	
	def is_displayed(player):
		return player.round_number == 1 and player.participant.vars['condition'] != 'indy'

class GroupDecision(Page):

	form_model = 'player'
	form_fields = ['lottery_action']
	timeout_seconds = C.TIMEOUT_CHOICE
	
	def is_displayed(player):
		return player.participant.condition == 'group' and not player.participant.is_dropout
   
	def before_next_page(player, timeout_happened):
		if timeout_happened:
			player.participant.is_dropout = True

	def vars_for_template(player):

		total_rounds_left = (C.NUM_ROUNDS - player.round_number + 1) * 5
		group_balance = player.participant.game_current_group_bonus
		optimal_n_risky, optimal_n_risky_per_player = get_optimal_n_riskys(total_rounds_left=total_rounds_left, group_balance=group_balance)
		
		return {
			'optimal_n_risky': optimal_n_risky,
			'optimal_n_risky_per_player': optimal_n_risky_per_player
		}

class VotingDecision(Page):

	form_model = 'player'
	form_fields = ['voter_decision']
	timeout_seconds = C.TIMEOUT_CHOICE
	
	def is_displayed(player):
		return player.participant.condition == 'voting' and not player.participant.is_dropout
	
	def before_next_page(player, timeout_happened):
		if timeout_happened:
			player.participant.is_dropout = True

	def vars_for_template(player):
		
		total_rounds_left = (C.NUM_ROUNDS - player.round_number + 1) * 5
		group_balance = player.participant.game_current_group_bonus
		optimal_n_risky, optimal_n_risky_per_player = get_optimal_n_riskys(total_rounds_left=total_rounds_left, group_balance=group_balance)
		
		return {
			'optimal_n_risky': optimal_n_risky,
			'optimal_n_risky_per_player': optimal_n_risky_per_player
		}


def get_voting_result(group):

	players = group.get_players()

	player_votes = [player.field_maybe_none('voter_decision') for player in players]

	while len(player_votes) < 5:
		if np.random.random() < 0.5:
			player_votes.append(1)
		else:
			player_votes.append(0)

	# Replace any None
	player_votes = [np.random.randint(2) if i in [None, ''] else i for i in player_votes]
	player_votes.sort()
	risky_count = player_votes[2]

	# Randomly choose player indices to play risky lottery
	risky_player_indices = random.sample(range(5), risky_count)

	# Get player actions
	player_choices = []
	for i in range(5):
		if i in risky_player_indices:
			player_choices.append('risky')
		else:
			player_choices.append('safe')

	for i, player in enumerate(players):        
		player.participant.player_votes = player_votes
		player.participant.risky_count = risky_count
		if i in risky_player_indices:
			player.lottery_action = 'risky'
		else:
			player.lottery_action = 'safe'

	return player_choices

def get_results(group):

	players = group.get_players()

	# If voting
	if players[0].participant.condition == 'voting':
		player_choices = get_voting_result(group)

	# If group  
	if players[0].participant.condition == 'group':
		player_choices = [player.field_maybe_none('lottery_action') for player in players]
		while len(player_choices) < 5:
			if np.random.random() < 0.08:
				player_choices.append('risky')
			else:
				player_choices.append('safe')
		# Replace any None
		player_choices = ['safe' if i in [None, ''] else i for i in player_choices]

		for player in players:
			player.participant.risky_count = player_choices.count('risky')

	# Get results of choices    
	group_extinct = players[0].participant.game_extinct

	player_results = []
	group_bonus = 0

	for i in range(5):
		player_choice = player_choices[i]
		random_roll = random.random()

		if player_choice == 'safe':
			if random_roll < 0.5:
				player_result = "0"
			else:
				player_result = "5"
				group_bonus += 5
		
		if player_choice == 'risky':
			if random_roll < 0.475:
				player_result = "0"
			elif random_roll < 0.95:
				player_result = "50"
				group_bonus += 50
			else:
				player_result = "extinction"
				group_extinct = True
		player_results.append(player_result)

	# Update player data
	if not group_extinct:
		for i, player in enumerate(players):
			player_result = player_results[i]
			if player_result == "5":
				player.participant.game_current_bonus += 5
			if player_result == "50":
				player.participant.game_current_bonus += 50

			player.participant.last_result = player_results[i]

			player.participant.game_current_group_bonus += group_bonus

	if group_extinct:
		for player in players:
			player.participant.game_extinct = True
			player.participant.game_current_bonus = 0
			player.participant.game_current_group_bonus = 0
			player.participant.last_result = "extinction"

	for player in players:
		player.lottery_result = player.participant.last_result
		player.game_current_bonus = player.participant.game_current_bonus
		player.game_extinct = player.participant.game_extinct
		player.game_current_group_bonus = player.participant.game_current_group_bonus

			
class ResultsWaitPage(WaitPage):   

	after_all_players_arrive = 'get_results'

	@staticmethod
	def is_displayed(player):
		return not player.participant.is_dropout and player.participant.condition in ['group', 'voting']

class GroupResult(Page):

	timeout_seconds = C.TIMEOUT_INFO

	def is_displayed(player):
		return player.participant.condition == 'group' and not player.participant.is_dropout

	def vars_for_template(player):

		risky_count = player.participant.risky_count
		safe_count = 5 - risky_count

		return {
			'risky_count': risky_count,
			'safe_count': safe_count,
		}
 

class VotingResult(Page):

	timeout_seconds = C.TIMEOUT_INFO
	
	def is_displayed(player):
		return player.participant.condition == 'voting' and not player.participant.is_dropout
	
	def vars_for_template(player):

		# Replace middle value with bold text of value

		player_votes = player.participant.player_votes
		player_votes[2] = f"<strong>{player_votes[2]}</strong>"
		player_votes_string = ', '.join([str(i) for i in player_votes])        

		risky_count = player.participant.risky_count
		safe_count = 5 - risky_count

		return {
			'player_votes': player_votes_string,
			'risky_count': risky_count,
			'safe_count': safe_count,
		}

page_sequence = [GroupWaitPage, 
				 ConditionChoice,
				OptimalChoices, 
				GetReady,
				 GroupDecision,
				 VotingDecision,
				 ResultsWaitPage,
				 GroupResult,
				 VotingResult]
