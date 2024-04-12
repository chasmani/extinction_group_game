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
    
    quiz_extinction = models.StringField(
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

    quiz_group_extinction = models.StringField(
        label="What happens if one of the players draws the extinction outcome in the risky lottery?",
        choices=[
            ['extinct_none', 'Nothing.'],
            ['extinct_one', 'Only the player who drew the extinction outcome will go extinct.'],
            ['extinct_some', 'Only the players who chose the risky lottery will go extinct.'],
            ['extinct_all', 'The entire group will go extinct, and lose all the bonus.'],
        ],
        widget=widgets.RadioSelect,
        initial=''
    )

    quiz_voting = models.StringField(
        label="How is the group decision made for how many players will play the risky lottery?",
        choices=[
            ['voting_median', 'The group decision is the middle value of the choices.'],
            ['voting_random', 'The group decision is randomly chosen.'],
            ['voting_leader', 'The group decision is the choice of the leader.'],
            ['voting_all', 'All players must choose the same option.'],
        ],
        widget=widgets.RadioSelect,
        initial=''
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

def quiz_extinction_error_message(player, value):
    if value != 'lose_all':
        return 'That is not correct. Please try again.'

def quiz_group_extinction_error_message(player, value):
    if value != 'extinct_all':
        return 'That is not correct. Please try again.'

def quiz_voting_error_message(player, value):
    if value != 'voting_median':
        return 'That is not correct. Please try again.'

class ConditionChoice(Page):
    form_model = "player"
    form_fields = ["condition_choice"]

    def before_next_page(player, timeout_happened):
        player.participant.vars['condition'] = player.condition_choice

class Instructions1(Page):
    form_model = "player"
    form_fields = ["quiz_extinction"]

class GroupInstructions2(Page):
    form_model = "player"
    form_fields = ["quiz_group_extinction"]

class VoterInstructions2(Page):
    form_model = "player"
    form_fields = ["quiz_group_extinction",
                   "quiz_voting"]

class PracticeGetReady(Page):
    pass

page_sequence = [ConditionChoice,
                 Instructions1,
                 GroupInstructions2,
                 VoterInstructions2,
                 PracticeGetReady]
