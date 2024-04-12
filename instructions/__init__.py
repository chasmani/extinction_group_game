from otree.api import *

import time

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
    quiz_1 = models.StringField(
        label="What happens if you choose the risky lottery and you draw the extinction option?",
        choices=[
            ['lose_nothing', 'Nothing.'],
            ['lose_trial', 'I will not get a bonus for this trial.'],
            ['lose_past', 'I will keep all my past bonus money, but I cannot make more bonus money in the next trials.'],
            ['lose_all', 'I will lose all my bonus money, and I cannot get any more bonus payments for future trials.'],
        ],
        widget=widgets.RadioSelect,
        initial=''
    )

    """
    quiz_2 = models.StringField(
        label="What does the piggy bank on the top right indicate?",
        choices=[
            ['bonus_gamble', 'How much bonus you can make in the next trial with good gambling skills.'],
            ['bonus_predicted', 'Your predicted amount of bonus after the next trial.'],
            ['bonus_current', 'Your current bonus.'],
            ['bonus_random', 'A random number.'],
        ],
        widget=widgets.RadioSelect,
        initial=''
    )
    """

class Instructions1(Page):
    form_model = "player"
    form_fields = ["quiz_1"]

class InstructionsGroup(Page):
    pass

class GroupIndyChoices(Page):
    pass

class GroupVotingChoices(Page):
    pass

class PracticeGetReady(Page):
    pass

class OptimalChoices(Page):
    pass

page_sequence = [Instructions1, 
                 GroupIndyChoices, 
                 GroupVotingChoices, 
                 OptimalChoices,
                 PracticeGetReady]
