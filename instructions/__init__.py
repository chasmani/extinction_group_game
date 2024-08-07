from otree.api import *

import time

doc = """
Your app description
"""

class C(BaseConstants):
	NAME_IN_URL = 'instructions'
	PLAYERS_PER_GROUP = None
	NUM_ROUNDS = 1

class Subsession(BaseSubsession):
	pass


class Group(BaseGroup):
	pass

class Player(BasePlayer):
	
	quiz_extinction = models.StringField(
		label="What happens if you choose the risky lottery and you draw the extinction option?",
		choices=[
			['lose_nothing', 'Nothing.'],
			['lose_round', 'I will not get a bonus for this round.'],
			['lose_past', 'I will keep all my past bonus money, but I cannot make more bonus money in the next rounds.'],
			['lose_all', 'I will lose all my bonus money, and I cannot get any more bonus payments for future rounds.'],
		],
		widget=widgets.RadioSelect,
		initial=''
	)

	quiz_total_rounds = models.StringField(
		label="How many rounds will you play in the experiment?",
		choices=[
			['total_10', '10 rounds.'],
			['total_20', '20 rounds.'],
			['total_50', '50 rounds.'],
			['total_100', '100 rounds.'],
		],
		widget=widgets.RadioSelect,
		initial=''
	)

	quiz_group_extinction = models.StringField(
		label="What happens if one of the players draws the extinction outcome in the risky lottery?",
		choices=[
			['extinct_none', 'Nothing.'],
			['extinct_one', 'Only the player who drew the extinction outcome will go extinct.'],
			['extinct_some', 'Only the players who chose the risky lottery will go extinct.'],
			['extinct_all', 'The entire group will go extinct, and lose all the bonus.'],
		],
		widget=widgets.RadioSelect,
		initial=''
	)

	quiz_voting = models.StringField(
		label="How is the group decision made for how many players will play the risky lottery?",
		choices=[
			['voting_median', 'The group decision is the middle value of the ordered votes.'],
			['voting_random', 'The group decision is randomly chosen.'],
			['voting_leader', 'The group decision is the choice of the leader.'],
			['voting_all', 'All players must choose the same option.'],
		],
		widget=widgets.RadioSelect,
		initial=''
	)

	condition_choice = models.StringField(
		label="Please choose the condition you would like to play in.",
		choices=[
			['group_info', 'Group with Independent Choices. With optimal information.'],
			['group_no_info', 'Group with Independent Choices. Without optimal information.'],
			['voting_info', 'Group with Median Voting. With optimal information.'],
			['voting_no_info', 'Group with Median Voting. Without optimal information.'],
			['indy', 'Independent.'],
		],
		widget=widgets.RadioSelect
	)
	
	lottery_switch_choice = models.StringField(
		label="Which way round do you want to see the lotteries?",
		choices=[
			['not_switched', 'Risky Left, Safe Right'],
			['switched', 'Safe Left, Risky Right']
		],
		widget=widgets.RadioSelect
	)


def quiz_extinction_error_message(player, value):
	if value != 'lose_all':
		player.participant.wrong_answers.append('quiz_extinction')
		return 'That is not correct. Please try again.'

def quiz_total_rounds_error_message(player, value):
	if player.participant.condition == "indy":
		if value != 'total_100':
			player.participant.wrong_answers.append('quiz_total_rounds')
			return 'That is not correct. Please try again.'
	else:
		if value != 'total_20':
			player.participant.wrong_answers.append('quiz_total_rounds')
			return 'That is not correct. Please try again.'    
	

def quiz_group_extinction_error_message(player, value):
	if value != 'extinct_all':
		player.participant.wrong_answers.append('quiz_group_extinction')
		return 'That is not correct. Please try again.'

def quiz_voting_error_message(player, value):
	if value != 'voting_median':
		player.participant.wrong_answers.append('quiz_voting')
		return 'That is not correct. Please try again.'


class ConditionChoice(Page):
	form_model = "player"
	form_fields = ["condition_choice", "lottery_switch_choice"]

	def is_displayed(player):
		return "condition" not in player.participant.vars

	def before_next_page(player, timeout_happened):
		player.participant.vars['condition'] = player.condition_choice
		player.participant.vars["switched"] = player.lottery_switch_choice == 'switched'
		player.participant.wrong_answers = []


class ConditionChoice(Page):

	form_model = "player"
	form_fields = ["condition_choice"]

	def is_displayed(player):
		return True

	def before_next_page(player, timeout_happened):
		condition_choice = player.condition_choice
		if condition_choice == 'indy':
			player.participant.condition = 'indy'
			player.participant.information = 'none'

		elif condition_choice == 'group_info':
			player.participant.condition = 'group'
			player.participant.information = 'optimal'
		elif condition_choice == 'group_no_info':
			player.participant.condition = 'group'
			player.participant.information = 'none'
		elif condition_choice == 'voting_info':
			player.participant.condition = 'voting'
			player.participant.information = 'optimal'
		elif condition_choice == 'voting_no_info':
			player.participant.condition = 'voting'
			player.participant.information = 'none'

		print("Instructions ConditionChoice: ", player.participant.vars)

class Instructions1(Page):
	form_model = "player"
	form_fields = ["quiz_extinction", "quiz_total_rounds"]

class GroupInstructions2(Page):
	form_model = "player"
	form_fields = ["quiz_group_extinction"]

	def is_displayed(player):
		return player.participant.condition == 'group'

class VoterInstructions2(Page):
	form_model = "player"
	form_fields = ["quiz_group_extinction",
				   "quiz_voting"]
	
	def is_displayed(player):
		return player.participant.condition == 'voting'

class Screenshot(Page):
	pass

class PracticeGetReady(Page):
	pass


page_sequence = [ConditionChoice,
				 Instructions1,
				 GroupInstructions2,
				 VoterInstructions2,
				 Screenshot,
				 PracticeGetReady]
