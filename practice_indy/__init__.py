from otree.api import *

import random

doc = """
Your app description
"""


def creating_session(subsession):

	if subsession.round_number == 1:
		# The below code only runs if we are running this app in isolation - not in the full experiment
		# If running this app in isolation, set the participant vars so that it works
		# For the full experiment, wait_page_arrival is set in previous app
		# For testing

		if subsession.session.config["name"] == "practice_individual":
			
			players = subsession.get_players()
			for player in players:
				player.participant.condition = "indy"

class C(BaseConstants):
	NAME_IN_URL = 'practice'
	PLAYERS_PER_GROUP = None
	NUM_ROUNDS = 20

class Subsession(BaseSubsession):
	pass

class Group(BaseGroup):
	pass

class Player(BasePlayer):
	lottery_decision = models.StringField(
		label="Please choose the lottery you would like to play this round.",
		choices=[
			['risky', 'Risky Lottery'],
			['safe', 'Safe Lottery']
		],
		widget=widgets.RadioSelect
	)

	lottery_result = models.StringField()
	game_current_bonus = models.IntegerField()
	game_extinct = models.BooleanField()


class ConditionChoice(Page):
	form_model = "player"
	form_fields = ["lottery_switch_choice"]

	def is_displayed(player):
		return False
		#return player.round_number == 1 and "condition" not in player.participant.vars

	def before_next_page(player, timeout_happened):
		player.participant.vars["switched"] = player.lottery_switch_choice == 'switched'

class IndyDecision(Page):

	form_model = 'player'
	form_fields = ['lottery_decision']

	def is_displayed(player):
		return player.participant.condition == 'indy'

	def before_next_page(player, timeout_happened):
		print(player, timeout_happened)

		random_roll = random.random()

		if player.round_number == 1:
			player.participant.practice_current_bonus = 0
			player.participant.practice_extinct = False

		if player.participant.practice_extinct:
			player.participant.vars['last_result'] = "0"
		else:
			if player.lottery_decision == 'safe':
				if random_roll < 0.5:
					player.participant.vars['last_result'] = "0"
				else:
					player.participant.vars['last_result'] = "1"
					player.participant.practice_current_bonus += 1

			if player.lottery_decision == 'risky':
				if random_roll < 0.475:
					player.participant.vars['last_result'] = "0"
				elif random_roll < 0.95:
					player.participant.vars['last_result'] = "10"
					player.participant.practice_current_bonus += 10
					
				else:
					player.participant.vars['last_result'] = "extinction"
					player.participant.practice_extinct = True
			
			player.lottery_result = player.participant.vars['last_result']
			player.game_extinct = player.participant.practice_extinct
			player.game_current_bonus = player.participant.practice_current_bonus


page_sequence = [ConditionChoice, IndyDecision]
