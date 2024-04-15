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

        if subsession.session.config["name"] == "game_individual":
            
            players = subsession.get_players()
            for player in players:

                player.participant.condition = "indy"

class C(BaseConstants):
    NAME_IN_URL = 'game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 100

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

class IndyDecision(Page):

    form_model = 'player'
    form_fields = ['lottery_decision']

    def is_displayed(player):
        return player.participant.condition == 'indy'

    def before_next_page(player, timeout_happened):
        print(player, timeout_happened)

        random_roll = random.random()

        if player.round_number == 1:
            player.participant.vars['current_bonus'] = 0
            player.participant.vars['extinct'] = False

        if player.participant.extinct:
            player.participant.vars['last_result'] = "0"
        else:
            if player.lottery_decision == 'safe':
                if random_roll < 0.5:
                    player.participant.vars['last_result'] = "0"
                else:
                    player.participant.vars['last_result'] = "1"
                    player.participant.vars['current_bonus'] += 0.01

            if player.lottery_decision == 'risky':
                if random_roll < 0.475:
                    player.participant.vars['last_result'] = "0"
                elif random_roll < 0.95:
                    player.participant.vars['last_result'] = "10"
                    player.participant.vars['current_bonus'] += 0.1
                else:
                    player.participant.vars['last_result'] = "extinction"
                    player.participant.vars['extinct'] = True



page_sequence = [IndyDecision]
