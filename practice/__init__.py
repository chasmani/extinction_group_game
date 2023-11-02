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


        if subsession.session.config["name"] == "practice":
            
            players = subsession.get_players()

            player_counter = 0
            group_id =1 
            for player in players:

                player.participant.practice_payoff = 0
                player.participant.practice_extinct = False


class C(BaseConstants):
    NAME_IN_URL = 'practice'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20
    RESULTS_TIME = 5

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    decision = models.StringField(
        choices=[
            ['risky', 'Lottery A'],
            ['safe', 'Lottery B']
        ],
        widget=widgets.RadioSelect
    )
    result = models.StringField(
        choices = [
            ['nothing','nothing'],
            ['extinction','extinction'],
            ['safe_win','safe_win'],
            ['risky_win','risky_win']
        ])
    
class Decision(Page):

    form_model = 'player'
    form_fields = ['decision']

    @staticmethod
    def before_next_page(player, timeout_happened):
        random_number = random.random()
        if player.decision == "risky":
            # Risky lottery
            if random_number < 0.05:
                player.participant.practice_extinct = True
                player.result = "extinction"
            elif random_number < 0.525:
                player.result = "nothing"
            else:
                player.result = "risky_win"
                if not player.participant.practice_extinct:
                    player.participant.practice_payoff += 10 
        else:
            # safe lottery
            if random_number < 0.5:
                player.result = "nothing"
            else:
                player.result = "safe_win"
                if not player.participant.practice_extinct:
                    player.participant.practice_payoff += 1
                


class Result(Page):
    
    @staticmethod
    def vars_for_template(player: Player):
        return {"result":player.result}

    @staticmethod
    def get_timeout_seconds(player):
        return C.RESULTS_TIME

page_sequence = [Decision, Result]
