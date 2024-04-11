from otree.api import *

import time

doc = """
Your app description
"""

<<<<<<< HEAD
=======

>>>>>>> ca28e7d1a85c2ca37b02bcb1729abd99036094c7
class C(BaseConstants):
    NAME_IN_URL = 'consent'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

<<<<<<< HEAD
=======

>>>>>>> ca28e7d1a85c2ca37b02bcb1729abd99036094c7
class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
<<<<<<< HEAD
    consent_1 = models.BooleanField(label="I have read and understand the information above. I have had the opportunity to consider the information.",
=======
    consent_1 = models.BooleanField(label="I have read and understand the information sheet. I have had the opportunity to consider the information.",
>>>>>>> ca28e7d1a85c2ca37b02bcb1729abd99036094c7
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

<<<<<<< HEAD
    consent_6 = models.BooleanField(label="I am over 18 years of age",
=======
    consent_6 = models.BooleanField(label="I am over 18 years of age.",
>>>>>>> ca28e7d1a85c2ca37b02bcb1729abd99036094c7
                                  choices=[
                                      [True, "Yes"],
                                  ]
                                  )
<<<<<<< HEAD
    
=======
>>>>>>> ca28e7d1a85c2ca37b02bcb1729abd99036094c7

    consent_7 = models.BooleanField(label="I consent to take part in this study",
                                  choices=[
                                      [True, "Yes"],
                                  ]
                                  )

<<<<<<< HEAD
    
class Welcome(Page):
    pass
    
=======
class Opening(Page):
  pass

class ParticipantInformation(Page):
  pass


>>>>>>> ca28e7d1a85c2ca37b02bcb1729abd99036094c7
class ParticipantConsent(Page):
    form_model = "player"
    form_fields = ["consent_1", "consent_2", "consent_3", "consent_4", "consent_5", "consent_6", "consent_7"]


<<<<<<< HEAD
page_sequence = [Welcome,
                 ParticipantConsent] 
=======

class Demographics(Page):
	pass

page_sequence = [Opening, ParticipantInformation, ParticipantConsent] 
>>>>>>> ca28e7d1a85c2ca37b02bcb1729abd99036094c7
