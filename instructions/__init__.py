import time
import random

from otree.api import *

from game import C as gameConstants

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

    pass


class Instructions(Page):

    pass


class PracticeGetReady(Page):

    pass


page_sequence = [Instructions, PracticeGetReady]
