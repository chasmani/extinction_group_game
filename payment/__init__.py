import random

from otree.api import *

doc = """
Your app description
"""

def creating_session(subsession):

    if subsession.round_number == 1:
        # The below code only runs if we are running this app in isolation - not in the full experiment
        # If running this app in isolation, set the participant vars so that it works
        # For the full experiment, wait_page_arrival is set in previous app
        # For testing

        if subsession.session.config["name"] == "payment":
            
            players = subsession.get_players()
            for player in players:

                player.participant.information = random.choice(["optimal", "none"])

class C(BaseConstants):
    NAME_IN_URL = 'payment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass

class Player(BasePlayer):

    # Survey question
    optimal_belief = models.StringField(
        label="Did you believe that the optimal strategy that we showed you was correct, in terms of being the best strategy for the group?",
        choices=["Yes", "No", "I'm Not Sure"],
        widget=widgets.RadioSelect,
        initial='')
    
    optimal_belief_text = models.LongStringField(
        label='If you did not answer "Yes" above, please explain why.',
        blank=True
    )

    free_text_box = models.LongStringField(
        label="Please provide any additional feedback or comments about the experiment.",
        blank=True
    )

class PostSurveyOptimal(Page):

    form_model = "player"
    form_fields = ['optimal_belief', 'optimal_belief_text']

    def is_displayed(player):
        if player.participant.condition in ["voting", "group"]:
            if player.participant.information == "optimal":
                return True
        return False
    
class PostSurvey(Page):

    form_model = "player"
    form_fields = ['free_text_box']


class ThankYou(Page):
    pass

page_sequence = [PostSurveyOptimal, PostSurvey, ThankYou]
