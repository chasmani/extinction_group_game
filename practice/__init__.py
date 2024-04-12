from otree.api import *

import random

doc = """
Your app description
"""

class C(BaseConstants):
    NAME_IN_URL = 'practice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    decision = models.StringField(
        choices=[
            ['risky', 'f'],
            ['safe', 'j']
        ],
        widget=widgets.RadioSelect
    )

class Decision(Page):

    form_model = 'player'
    form_fields = ['decision']

    def before_next_page(player, timeout_happened):
        print(player, timeout_happened)

        random_roll = random.random()

        if player.round_number == 1:
            player.participant.vars['current_bonus'] = 0
            player.participant.vars['extinct'] = False

        if player.decision == 'safe':
            if random_roll < 0.5:
                player.participant.vars['last_result'] = "0"
            else:
                player.participant.vars['last_result'] = "1"
                player.participant.vars['current_bonus'] += 0.01

        if player.decision == 'risky':
            if random_roll < 0.475:
                player.participant.vars['last_result'] = "0"
            elif random_roll < 0.95:
                player.participant.vars['last_result'] = "10"
                player.participant.vars['current_bonus'] += 0.1
            else:
                player.participant.vars['last_result'] = "extinction"
                player.participant.vars['extinct'] = True
                


page_sequence = [Decision]
