from otree.api import *

import random

doc = """
Your app description
"""

class C(BaseConstants):
	NAME_IN_URL = 'consent'
	PLAYERS_PER_GROUP = None
	NUM_ROUNDS = 1

class Subsession(BaseSubsession):
	pass

class Group(BaseGroup):
	pass


class Player(BasePlayer):
	consent_1 = models.BooleanField(label="I have read and understand the information above. I have had the opportunity to consider the information.",
								  choices=[
									  [True, "Yes"],
								  ]
								  )

	consent_2 = models.BooleanField(label="I understand that all information collected will be treated as strictly confidential and handled in accordance with the provisions of the General Data Protection Regulation.",
								  choices=[
									  [True, "Yes"],
								  ]
								  )


	consent_3 = models.BooleanField(label="I understand that anonymous data that cannot be traced back to me individually may be used in academic publications and shared in accordance with open science guidelines and I consent to this.",
								  choices=[
									  [True, "Yes"],
								  ]
								  )


	consent_4 = models.BooleanField(label="I understand that the legal basis for processing any personal information about me is my consent.",
								  choices=[
									  [True, "Yes"],
								  ]
								  )


	consent_5 = models.BooleanField(label="I understand that I can withdraw from the study at any time but that it will be difficult or impossible to withdraw my data once the task has been completed.",
								  choices=[
									  [True, "Yes"],
								  ]
								  )

	consent_6 = models.BooleanField(label="I am over 18 years of age",
								  choices=[
									  [True, "Yes"],
								  ]
								  )
	

	consent_7 = models.BooleanField(label="I consent to take part in this study",
								  choices=[
									  [True, "Yes"],
								  ]
								  )
	
class Welcome(Page):
	pass
	
class ParticipantConsent(Page):
	form_model = "player"
	form_fields = ["consent_1", "consent_2", "consent_3", "consent_4", "consent_5", "consent_6", "consent_7"]

	def before_next_page(player, timeout_happened):
		random_draw = random.random()
		if random_draw < 0.2:
			player.participant.vars['condition'] = 'indy'
		elif random_draw < 0.6:
			player.participant.vars['condition'] = 'group'
		else:
			player.participant.vars['condition'] = 'voting'
	   
		random_draw_2 = random.random()
		if random_draw_2 < 0.5:
			player.participant.vars["switched"] = True
		else:
			player.participant.vars["switched"] = False

		player.participant.wrong_answers = []
		player.participant.is_dropout = False


page_sequence = [Welcome,
				 ParticipantConsent] 
