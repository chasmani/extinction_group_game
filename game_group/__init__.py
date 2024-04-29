from otree.api import *

import random
import time

import numpy as np

doc = """
Your app description
"""

def creating_session(subsession):

    if subsession.round_number == 1:
        # The below code only runs if we are running this app in isolation - not in the full experiment
        # If running this app in isolation, set the participant vars so that it works
        # For the full experiment, wait_page_arrival is set in previous app
        # For testing


        if subsession.session.config["name"] == "game_group":

            print("Ho")
            
            players = subsession.get_players()
            for player in players:

                player.participant.wait_page_arrival = time.time()

                player.participant.is_dropout = False
                player.participant.wrong_answers = []
                player.participant.exclusion = False
                player.participant.condition = "voting"
                player.participant.switched = np.random.choice([True, False])

class C(BaseConstants):
    NAME_IN_URL = 'game_group'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    lottery_action = models.StringField(
        label="Please choose the lottery you would like to play this round.",
        choices=[
            ['risky', 'Risky Lottery'],
            ['safe', 'Safe Lottery']
        ],
        widget=widgets.RadioSelect
    )

    voter_decision = models.IntegerField(
        label="Please vote for how many players you would like to play the risky lottery this round.",
        choices=[0,1,2,3,4,5],
        widget=widgets.RadioSelect
    )

    condition_choice = models.StringField(
        label="Please choose the condition you would like to play in.",
        choices=[
            ['group', 'Group with Independent Choices'],
            ['voting', 'Group with Median Voting'],
        ],
        widget=widgets.RadioSelect
    )

    lottery_switch_choice = models.StringField(
        label="Which way round do you want to see the lotteries?",
        choices=[
            ['not_switched', 'Risky Left, Safe Right'],
            ['switched', 'Safe Left, Risky Right']
        ],
        widget=widgets.RadioSelect
    )


def group_by_arrival_time_method(self, waiting_players):

    print(waiting_players)

    for player in waiting_players:
        if len(player.participant.wrong_answers) > 0:
            player.participant.unique_group_id = np.random.randint(1000000000)
            return [player]

    for condition in ["group", "voting"]:
        players_in_condition = []
        for player in waiting_players:
            # Collect the players in each condition
            if player.participant.condition == condition and len(player.participant.wrong_answers) == 0:
                players_in_condition.append(player)
        # If there are enough players in the condition
        if len(players_in_condition) >= 5:
            this_group = players_in_condition[:5]
            unique_group_id = np.random.randint(1000000000)
            # Rnadomly choose information condition
            information_condition = np.random.choice(["none", "optimal"])
            for player in this_group:
                player.participant.unique_group_id = unique_group_id
                player.participant.information = information_condition
            return this_group

    # For players waiting too long
    for player in waiting_players:
        if waiting_too_long(player):
            player.participant.unique_group_id = np.random.randint(1000000000)
            return [player]

def waiting_too_long(player):
    return time.time() - player.participant.wait_page_arrival > 30

class GroupWaitPage(WaitPage):
    
    group_by_arrival_time = True

    body_text = """
        <p>IT IS IMPORTANT THAT YOU KEEP THIS TAB ACTIVE.</p>
        You may have to wait a few minutes while the other players in your group catch up.
        Once everyone catches up the game will start immediately. 
        """
    
    def is_displayed(player):
        return player.round_number == 1 and player.participant.condition in ['group', 'voting']


class OptimalChoices(Page):
    
    timeout_seconds = 240

    def is_displayed(player):
        return player.round_number == 1 and player.participant.vars['condition'] != 'indy' and player.participant.vars['information'] == 'optimal'

class GetReady(Page):

    timeout_seconds = 30
    
    def is_displayed(player):
        return player.round_number == 1 and player.participant.vars['condition'] != 'indy'

class GroupDecision(Page):

    form_model = 'player'
    form_fields = ['lottery_action']
    timeout_seconds = 60
    
    def is_displayed(player):
        return player.participant.condition == 'group' and not player.participant.is_dropout
   
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.participant.is_dropout = True

class VotingDecision(Page):

    form_model = 'player'
    form_fields = ['voter_decision']
    timeout_seconds = 60
    
    def is_displayed(player):
        return player.participant.condition == 'voting' and not player.participant.is_dropout
    
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.participant.is_dropout = True

def get_results(group):

    players = group.get_players()
    if players[0].round_number == 1:
        for player in players:
            player.participant.vars['game_current_bonus'] = 0
            player.participant.vars['game_extinct'] = False

    # Voting bit
    if players[0].participant.condition == 'voting':
        player_votes = [player.field_maybe_none('voter_decision') for player in players]
        
        while len(player_votes) < 5:
            player_votes.append(0)
        # Replace any None
        player_votes = [0 if i is None else i for i in player_votes]

        player_votes.sort()

        risky_count = player_votes[2]

        # Rnadomly choose player indices to play risky lottery
        risky_players = random.sample(range(5), risky_count)

        for i, player in enumerate(players):
            player.participant.player_votes = player_votes
            if i in risky_players:
                player.lottery_action = 'risky'
            else:
                player.lottery_action = 'safe'

    # Group bit
    if players[0].participant.condition == 'group':
        player_choices = [player.field_maybe_none('lottery_action') for player in players]
        while len(player_choices) < 5:
            player_choices.append('safe')
        # Replace any None
        player_choices = ['safe' if i is None else i for i in player_choices]

        risky_count = player_choices.count('risky')

    # Works for both group types
    if not players[0].participant.game_extinct:

        group_extinct = False
        for player in players:

            player.participant.risky_count = risky_count

            random_roll = random.random()

            if player.participant.game_extinct:
                player.participant.vars['last_result'] = "0"
            else:
                if player.lottery_action == 'safe':
                    if random_roll < 0.5:
                        player.participant.vars['last_result'] = "0"
                    else:
                        player.participant.vars['last_result'] = "1"
                        player.participant.vars['game_current_bonus'] += 1

                if player.lottery_action == 'risky':
                    if random_roll < 0.475:
                        player.participant.vars['last_result'] = "0"
                    elif random_roll < 0.95:
                        player.participant.vars['last_result'] = "10"
                        player.participant.vars['game_current_bonus'] += 10
                    else:
                        player.participant.vars['last_result'] = "extinction"
                        print("EXINTG!!")
                        group_extinct = True

        if group_extinct:
            for player in players:
                player.participant.vars['last_result'] = "extinction"
                player.participant.vars['game_extinct'] = True
                player.participant.vars['game_current_bonus'] = 0


class ResultsWaitPage(WaitPage):   

    after_all_players_arrive = 'get_results'

    @staticmethod
    def is_displayed(player):
        return not player.participant.is_dropout

class GroupResult(Page):

    timeout_seconds = 30

    def is_displayed(player):
        return player.participant.condition == 'group' and not player.participant.is_dropout

    def vars_for_template(player):

        risky_count = player.participant.risky_count
        safe_count = 5 - risky_count

        return {
            'risky_count': risky_count,
            'safe_count': safe_count,
        }
 

class VotingResult(Page):

    timeout_seconds = 30
    
    def is_displayed(player):
        return player.participant.condition == 'voting' and not player.participant.is_dropout
    
    def vars_for_template(player):

        # Replace middle value with bold text of value

        player_votes = player.participant.player_votes
        player_votes[2] = f"<strong>{player_votes[2]}</strong>"
        player_votes_string = ', '.join([str(i) for i in player_votes])        

        risky_count = player.participant.risky_count
        safe_count = 5 - risky_count

        return {
            'player_votes': player_votes_string,
            'risky_count': risky_count,
            'safe_count': safe_count,
        }

page_sequence = [GroupWaitPage, 
                OptimalChoices, 
                GetReady,
                 GroupDecision,
                 VotingDecision,
                 ResultsWaitPage,
                 GroupResult,
                 VotingResult]
