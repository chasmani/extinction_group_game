from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'game'
    PLAYERS_PER_GROUP = 5
    NUM_ROUNDS = 20
    TREATMENTS = [True, False]

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

class GroupWaitPage(WaitPage):

    group_by_arrival_time = True

    body_text = """
        <p>IT IS IMPORTANT THAT YOU KEEP THIS TAB ACTIVE.</p>
        You may have to wait a few minutes while the other players in your group catch up.
        Once everyone catches up the game will start immediately. 
        """

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1
    
class Decision(Page):

    form_model = 'player'
    form_fields = ['decision']

class ResultsWaitPage(WaitPage):
    pass

class Results(Page):
    
    @staticmethod
    def vars_for_template(player: Player):
        pass

class OptimalChoices(Page):
    pass

page_sequence = [GroupWaitPage, OptimalChoices, Decision, ResultsWaitPage, Results]
