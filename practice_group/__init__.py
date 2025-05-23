from otree.api import *

import random
import time

import numpy as np

from game_group import get_results

doc = """
Your app description
"""

def creating_session(subsession):

	if subsession.round_number == 1:
		# The below code only runs if we are running this app in isolation - not in the full experiment
		# If running this app in isolation, set the participant vars so that it works
		# For the full experiment, wait_page_arrival is set in previous app
		# For testing


		if subsession.session.config["name"] == "practice_group":

			
			players = subsession.get_players()
			for player in players:

				player.participant.wait_page_arrival = time.time()

				player.participant.is_dropout = False
				player.participant.wrong_answers = []
				player.participant.exclusion = False
				player.participant.condition = np.random.choice(["group", "voting"])
				player.participant.switched = np.random.choice([True, False])
				
			players = subsession.get_players()
		

class C(BaseConstants):
	NAME_IN_URL = 'practice_group'
	PLAYERS_PER_GROUP = None
	NUM_ROUNDS = 4

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

	lottery_result = models.StringField()
	game_current_bonus = models.IntegerField()
	game_extinct = models.BooleanField()
	game_current_group_bonus = models.IntegerField()


def group_by_arrival_time_method(self, waiting_players):

	for player in waiting_players:
		return [player]

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
		"""
	
	def is_displayed(player):
		return player.round_number == 1 and player.participant.condition in ['group', 'voting']

def expected_value_strategy(n_risky, endowment=0, p_survive=0.95, e_risky=5, e_safe = 0.5, n_rounds=100):

	return p_survive**n_risky * (endowment + e_risky * n_risky + e_safe * (n_rounds - n_risky))

class GetReady(Page):

	def is_displayed(player):
		return player.round_number == 1 and player.participant.vars['condition'] != 'indy'

class GroupDecision(Page):

	form_model = 'player'
	form_fields = ['lottery_action']
	
	def is_displayed(player):
		return player.participant.condition == 'group'

class VotingDecision(Page):

	form_model = 'player'
	form_fields = ['voter_decision']
	
	def is_displayed(player):
		return player.participant.condition == 'voting'

class ResultsWaitPage(WaitPage):   

	after_all_players_arrive = 'get_results'

	@staticmethod
	def is_displayed(player):
		return player.participant.condition in ['group', 'voting']

class GroupResult(Page):

	def is_displayed(player):
		return player.participant.condition == 'group'

	def vars_for_template(player):

		risky_count = player.participant.risky_count
		safe_count = 5 - risky_count

		return {
			'risky_count': risky_count,
			'safe_count': safe_count,
		}
	
	def before_next_page(player, timeout_happened):
		if player.round_number == C.NUM_ROUNDS:
			player.participant.wait_page_arrival = time.time()

class VotingResult(Page):
	
	def is_displayed(player):
		return player.participant.condition == 'voting'
	
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
	
	def before_next_page(player, timeout_happened):
		if player.round_number == C.NUM_ROUNDS:
			player.participant.wait_page_arrival = time.time()

page_sequence = [GroupWaitPage, 
				 GroupDecision,
				 VotingDecision,
				 ResultsWaitPage,
				 GroupResult,
				 VotingResult]
