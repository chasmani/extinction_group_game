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
    lottery_decision = models.StringField(
        label="Please choose the lottery you would like to play this round.",
        choices=[
            ['risky', 'Risky Lottery'],
            ['safe', 'Safe Lottery']
        ],
        widget=widgets.RadioSelect
    )

    voter_decision = models.IntegerField(
        label="Please vote for how many players you would like to play the risky lottery.",
        choices=[0,1,2,3,4,5],
        widget=widgets.RadioSelect
    )

    condition_choice = models.StringField(
        label="Please choose the condition you would like to play in.",
        choices=[
            ['indy', 'Independent'],
            ['group', 'Group with Independent Choices'],
            ['voting', 'Group with Median Voting'],
        ],
        widget=widgets.RadioSelect
    )


class ConditionChoice(Page):
    form_model = "player"
    form_fields = ["condition_choice"]

    def is_displayed(player):
        return player.round_number == 1

    def before_next_page(player, timeout_happened):
        player.participant.vars['condition'] = player.condition_choice

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

class GroupDecision(Page):
    
    def is_displayed(player):
        return player.participant.condition == 'group'


class GroupResult(Page):

    def is_displayed(player):
        return player.participant.condition == 'group'

    def vars_for_template(player):

        risky_count = 3
        safe_count = 2

        return {
            'risky_count': risky_count,
            'safe_count': safe_count,
        }
    
class VotingDecision(Page):
    
    def is_displayed(player):
        return player.participant.condition == 'group'

class VotingResult(Page):
    
    def is_displayed(player):
        return player.participant.condition == 'group'

page_sequence = [ConditionChoice, 
                 IndyDecision, 
                 GroupDecision,
                 GroupResult,
                 VotingDecision,
                 VotingResult]
