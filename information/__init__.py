from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'information'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Player(BasePlayer):
    
    condition_choice = models.StringField(
        label="Please choose the condition you would like to play in.",
        choices=[
            ['indy', 'Independent'],
            ['group', 'Group with Independent Choices'],
            ['voting', 'Group with Median Voting'],
        ],
        widget=widgets.RadioSelect
    )

    information_choice = models.StringField(
        label="Please choose the information you would like to see (group games only).",
        choices=[
            ['none', 'No Information'],
            ['optimal', 'Optimal Choices'],
        ],
        widget=widgets.RadioSelect
    )

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class ConditionChoice(Page):
    form_model = "player"
    form_fields = ["condition_choice", "information_choice"]

    def before_next_page(player, timeout_happened):
        player.participant.vars['condition'] = player.condition_choice
        player.participant.vars['information'] = player.information_choice

class OptimalChoices(Page):
    
    def is_displayed(player):
        return player.participant.vars['condition'] != 'indy' and player.participant.vars['information'] == 'optimal'

class GetReady(Page):
    
    pass
page_sequence = [ConditionChoice, OptimalChoices, GetReady]
