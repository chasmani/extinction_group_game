from otree.api import *

import time

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
    consent_1 = models.BooleanField(label="I have read and understand the information sheet. I have had the opportunity to consider the information.",
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

    consent_6 = models.BooleanField(label="I am over 18 years of age.",
                                  choices=[
                                      [True, "Yes"],
                                  ]
                                  )

    consent_7 = models.BooleanField(label="I consent to take part in this study",
                                  choices=[
                                      [True, "Yes"],
                                  ]
                                  )

class Opening(Page):
  pass

class ParticipantInformation(Page):
  pass


class ParticipantConsent(Page):
    form_model = "player"
    form_fields = ["consent_1", "consent_2", "consent_3", "consent_4", "consent_5", "consent_6", "consent_7"]



class Demographics(Page):
	pass

page_sequence = [Opening, ParticipantInformation, ParticipantConsent] 