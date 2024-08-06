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


        if subsession.session.config["name"] == "practice_group":
            
            players = subsession.get_players()
            for player in players:

                player.participant.wait_page_arrival = time.time()

                player.participant.is_dropout = False
                player.participant.wrong_answers = []
                player.participant.exclusion = False
                player.participant.condition = "group"
                player.participant.switched = np.random.choice([True, False])


class C(BaseConstants):
    NAME_IN_URL = 'practice_group'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 4

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

    for player in waiting_players:
        return [player]

def set_game_vars(group):
    for player in group.get_players():
        player.participant.practice_current_bonus = 0
        player.participant.practice_extinct = False
        player.participant.practice_current_group_bonus = 0

class GroupWaitPage(WaitPage):
    
    group_by_arrival_time = True
    after_all_players_arrive = 'set_game_vars'

    body_text = """
        <p>IT IS IMPORTANT THAT YOU KEEP THIS TAB ACTIVE.</p>
        You may have to wait a few minutes while the other players in your group catch up.
        """
    
    def is_displayed(player):
        return player.round_number == 1 and player.participant.condition in ['group', 'voting']

def expected_value_strategy(n_risky, endowment=0, p_survive=0.95, e_risky=5, e_safe = 0.5, n_rounds=100):

    return p_survive**n_risky * (endowment + e_risky * n_risky + e_safe * (n_rounds - n_risky))

class OptimalChoices(Page):
    
    timeout_seconds = 240

    def is_displayed(player):
        return player.round_number == 1 and player.participant.vars['condition'] != 'indy' and player.participant.vars['information'] == 'optimal'

    def vars_for_template(player):
    
        n_rounds = 100
        n_riskys = list(range(n_rounds))
        expected_values = [expected_value_strategy(n_risky) for n_risky in n_riskys]

        # Get max n_riskys
        optimal_n_risky = n_riskys[np.argmax(expected_values)]
        optimal_n_risky_per_player = optimal_n_risky / 5

        return {
            'optimal_n_risky': optimal_n_risky,
            'optimal_n_risky_per_player': optimal_n_risky_per_player,
            'n_riskys': n_riskys,
            'expected_values': expected_values
        }

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

    def vars_for_template(player):
        return {
            'optimal_n_risky': 8
        }

class VotingDecision(Page):

    form_model = 'player'
    form_fields = ['voter_decision']
    timeout_seconds = 60
    
    def is_displayed(player):
        return player.participant.condition == 'voting' and not player.participant.is_dropout
    
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.participant.is_dropout = True

    def vars_for_template(player):
        return {
            'optimal_n_risky': 8
        }

def get_results(group):

    players = group.get_players()

    player = players[0]

    # Voting bit
    if player.participant.condition == 'voting':
        
        player_votes = [random.randint(0, 5) for i in range(4)]
        player_votes.append(player.voter_decision)

        player_votes.sort()
        player.participant.player_votes = player_votes
        risky_count= player_votes[2]
        safe_count = 5 - risky_count

        prob_this_player_risky = 0.2*risky_count
        random_roll_a = random.random()
        if random_roll_a < prob_this_player_risky:
            player.lottery_action = 'risky'
        else:
            player.lottery_action = 'safe'

    # Group bit
    if player.participant.condition == 'group':

        risky_count = random.randint(0, 4)
        if player.lottery_action == 'risky':
            risky_count += 1
        safe_count = 5 - risky_count

    if not player.participant.practice_extinct:
        player.participant.risky_count = risky_count
        
        if player.lottery_action == 'safe':
            other_risky_count = risky_count
            random_roll = random.random()
            if random_roll < 0.5:
                player.participant.vars['last_result'] = "0"
            else:
                player.participant.vars['last_result'] = "1"
                player.participant.vars['practice_current_bonus'] += 1

        if player.lottery_action == 'risky':
            other_risky_count = risky_count - 1
            random_roll = random.random()
            if random_roll < 0.475:
                player.participant.vars['last_result'] = "0"
            elif random_roll < 0.95:
                player.participant.vars['last_result'] = "10"
                player.participant.vars['practice_current_bonus'] += 10
            else:
                player.participant.vars['last_result'] = "extinction"
                player.participant.vars['practice_current_bonus'] = 0

        # Sim other player outcomes
        # Group payout outcomes
        player.participant.practice_current_group_bonus += player.participant.practice_current_bonus
        for _ in range(other_risky_count):
            random_roll_a = random.random()
            if random_roll_a < 0.5:
                player.participant.practice_current_group_bonus += 10

        for _ in range(5-other_risky_count):
            random_roll_a = random.random()
            if random_roll_a < 0.5:
                player.participant.practice_current_group_bonus += 1

        # Group extinction
        random_roll = random.random()
        if random_roll > (0.95**other_risky_count):
            player.participant.vars['last_result'] = "extinction"
            player.participant.practice_current_bonus = 0
            player.participant.practice_current_group_bonus = 0
            player.participant.practice_extinct = True


class ResultsWaitPage(WaitPage):   

    after_all_players_arrive = 'get_results'

    @staticmethod
    def is_displayed(player):
        return player.participant.condition in ['group', 'voting']

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
    
    def before_next_page(player, timeout_happened):
        if player.round_number == C.NUM_ROUNDS:
            player.participant.wait_page_arrival = time.time()

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
    
    def before_next_page(player, timeout_happened):
        if player.round_number == C.NUM_ROUNDS:
            player.participant.wait_page_arrival = time.time()

page_sequence = [GroupWaitPage, 
                 GroupDecision,
                 VotingDecision,
                 ResultsWaitPage,
                 GroupResult,
                 VotingResult]
