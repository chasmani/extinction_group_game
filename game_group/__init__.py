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

            
            players = subsession.get_players()
            for player in players:

                player.participant.wait_page_arrival = time.time()

                player.participant.is_dropout = False
                player.participant.wrong_answers = []
                player.participant.exclusion = False
                player.participant.condition = np.random.choice(["group", "voting"])
                player.participant.switched = np.random.choice([True, False])

class C(BaseConstants):
    NAME_IN_URL = 'game_group'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20
    TIMEOUT_GROUPING = 1
    TIMEOUT_CHOICE = 60
    TIMEOUT_INFO = 30

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

    optimal_comprehension = models.StringField(
        label="The strategy that should work best for the group is . . . ",
        choices=[
            ["8 and 40", "I personally play a total of 8 risky lotteries (~40 for the group)"], 
            ["1 to 2 and 8", "The group in total plays 8 risky lotteries (~1 to 2 for me personally)"], 
            ["0", "No one should play any risky lotteries"],
            ["3 and 15", "I personally play a total of 3 risky lotteries (~15 for the group)"],
        ],
        widget=widgets.RadioSelect,
        initial=''
        )

    condition_choice = models.StringField(
        label="Please choose the condition you would like to play in.",
        choices=[
            ['group', 'Group with Independent Choices'],
            ['voting', 'Group with Median Voting'],
        ],
        widget=widgets.RadioSelect
    )

    info_choice = models.StringField(
        label="Please choose the information condition you would like to play in.",
        choices=[
            ['none', 'No Information'],
            ['optimal', 'Optimal Information'],
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

def optimal_comprehension_error_message(player, value):
    if value != '1 to 2 and 8':
        player.participant.wrong_answers.append('quiz_group_extinction')
        return 'That is not correct. Please try again.'

def group_by_arrival_time_method(self, waiting_players):

    for player in waiting_players:
        if len(player.participant.wrong_answers) > 0:
            player.participant.unique_group_id = np.random.randint(1000000000)
            player.participant.information = np.random.choice(["none", "optimal"])
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
            # Randomly choose information condition
            information_condition = np.random.choice(["none", "optimal"])
            for player in this_group:
                player.participant.unique_group_id = unique_group_id
                player.participant.information = information_condition
            return this_group

    # For players waiting too long
    for player in waiting_players:
        if waiting_too_long(player):
            player.participant.unique_group_id = np.random.randint(1000000000)
            player.participant.information = np.random.choice(["none", "optimal"])
            return [player]

def waiting_too_long(player):
    return time.time() - player.participant.wait_page_arrival > C.TIMEOUT_GROUPING

def set_game_vars(group):
    for player in group.get_players():
        player.participant.game_current_bonus = 0
        player.participant.game_extinct = False
        player.participant.game_current_group_bonus = 0

class GroupWaitPage(WaitPage):
    
    group_by_arrival_time = True
    after_all_players_arrive = 'set_game_vars'

    body_text = """
        <p>IT IS IMPORTANT THAT YOU KEEP THIS TAB ACTIVE.</p>
        You may have to wait a few minutes while the other players in your group catch up.
        """
    
    def is_displayed(player):
        return player.round_number == 1 and player.participant.condition in ['group', 'voting']

def expected_value_strategy(n_risky, group_balance = 0, p_survive=0.95, e_risky=5, e_safe = 0.5, n_rounds=100):

    return p_survive**n_risky * (group_balance + e_risky * n_risky + e_safe * (n_rounds - n_risky))


class ConditionChoice(Page):

    form_model = "player"
    form_fields = ["condition_choice", "info_choice"]

    def is_displayed(player):
        return player.round_number == 1

    def before_next_page(player, timeout_happened):

        group = player.group
        players = group.get_players()

        for player in players:
            player.participant.condition = player.condition_choice
            player.participant.information = player.info_choice


class OptimalChoices(Page):
    
    timeout_seconds = C.TIMEOUT_CHOICE * 2

    form_model = 'player'
    form_fields = ['optimal_comprehension']

    def is_displayed(player):
        return player.round_number == 1 and player.participant.vars['condition'] != 'indy' and player.participant.vars['information'] == 'optimal'

    def vars_for_template(player):
    
        total_rounds_left = 100
        n_riskys = list(range(total_rounds_left))
        expected_values = [expected_value_strategy(n_risky) for n_risky in n_riskys]

        optimal_n_risky, optimal_n_risky_per_player = get_optimal_n_riskys(total_rounds_left)

        return {
            'optimal_n_risky': optimal_n_risky,
            'optimal_n_risky_per_player': optimal_n_risky_per_player,
            'n_riskys': n_riskys,
            'expected_values': expected_values
        }
    
def get_optimal_n_riskys(total_rounds_left, group_balance=0):

    n_riskys = list(range(total_rounds_left))
    expected_values = [expected_value_strategy(n_risky, group_balance=group_balance) for n_risky in n_riskys]

    # Get max n_riskys
    optimal_n_risky = n_riskys[np.argmax(expected_values)]

        # Optimal n_risky if integer or a fraction
    if optimal_n_risky % 5 == 0:
        optimal_n_risky_per_player = optimal_n_risky // 5
    else:
        optimal_n_risky_per_player = "{} to {}".format(optimal_n_risky // 5, int(optimal_n_risky//5 + 1))

    return optimal_n_risky, optimal_n_risky_per_player


class GetReady(Page):

    timeout_seconds = C.TIMEOUT_INFO
    
    def is_displayed(player):
        return player.round_number == 1 and player.participant.vars['condition'] != 'indy'

class GroupDecision(Page):

    form_model = 'player'
    form_fields = ['lottery_action']
    timeout_seconds = C.TIMEOUT_CHOICE
    
    def is_displayed(player):
        return player.participant.condition == 'group' and not player.participant.is_dropout
   
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.participant.is_dropout = True

    def vars_for_template(player):

        total_rounds_left = (C.NUM_ROUNDS - player.round_number + 1) * 5
        group_balance = player.participant.game_current_group_bonus
        optimal_n_risky, optimal_n_risky_per_player = get_optimal_n_riskys(total_rounds_left, group_balance=group_balance)
        
        return {
            'optimal_n_risky': optimal_n_risky,
            'optimal_n_risky_per_player': optimal_n_risky_per_player
        }

class VotingDecision(Page):

    form_model = 'player'
    form_fields = ['voter_decision']
    timeout_seconds = C.TIMEOUT_CHOICE
    
    def is_displayed(player):
        return player.participant.condition == 'voting' and not player.participant.is_dropout
    
    def before_next_page(player, timeout_happened):
        if timeout_happened:
            player.participant.is_dropout = True

    def vars_for_template(player):
        
        total_rounds_left = (C.NUM_ROUNDS - player.round_number + 1) * 5
        group_balance = player.participant.game_current_group_bonus
        optimal_n_risky, optimal_n_risky_per_player = get_optimal_n_riskys(total_rounds_left, group_balance=group_balance)
        
        return {
            'optimal_n_risky': optimal_n_risky,
            'optimal_n_risky_per_player': optimal_n_risky_per_player
        }


def get_voting_result(group):

    players = group.get_players()

    player_votes = [player.field_maybe_none('voter_decision') for player in players]

    while len(player_votes) < 5:
        player_votes.append(np.random.randint(6))
    # Replace any None
    player_votes = [np.random.randint(6) if i is None else i for i in player_votes]
    player_votes.sort()
    risky_count = player_votes[2]

    # Randomly choose player indices to play risky lottery
    risky_player_indices = random.sample(range(5), risky_count)

    # Get player actions
    player_choices = []
    for i in range(5):
        if i in risky_player_indices:
            player_choices.append('risky')
        else:
            player_choices.append('safe')

    for i, player in enumerate(players):        
        player.participant.player_votes = player_votes
        player.participant.risky_count = risky_count
        if i in risky_player_indices:
            player.lottery_action = 'risky'
        else:
            player.lottery_action = 'safe'

    return player_choices

def get_results(group):

    players = group.get_players()

    # If voting
    if players[0].participant.condition == 'voting':
        player_choices = get_voting_result(group)

    # If group
    if players[0].participant.condition == 'group':
        player_choices = [player.field_maybe_none('lottery_action') for player in players]
        while len(player_choices) < 5:
            player_choices.append(np.random.choice(['risky', 'safe']))
        # Replace any None
        player_choices = ['safe' if i is None else i for i in player_choices]
        
        for player in players:
            player.participant.risky_count = player_choices.count('risky')

    # Get results of choices    
    group_extinct = players[0].participant.game_extinct

    player_results = []
    group_bonus = 0

    for i in range(5):
        player_choice = player_choices[i]
        random_roll = random.random()

        if player_choice == 'safe':
            if random_roll < 0.5:
                player_results.append("0")
            else:
                player_results.append("1")
                group_bonus += 1
        
        if player_choice == 'risky':
            if random_roll < 0.475:
                player_results.append("0")
            elif random_roll < 0.95:
                player_results.append("10")
                group_bonus += 10
            else:
                player_results.append("extinction")
                group_extinct = True

    # Update player data
    if not group_extinct:
        for i, player in enumerate(players):
            player_result = player_results[i]
            if player_result == "1":
                player.participant.game_current_bonus += 1
            if player_result == "10":
                player.participant.game_current_bonus += 10

            player.participant.last_result = player_results[i]

            player.participant.game_current_group_bonus += group_bonus

    if group_extinct:
        for player in players:
            player.participant.game_extinct = True
            player.participant.game_current_bonus = 0
            player.participant.game_current_group_bonus = 0
            player.participant.last_result = "extinction"

            
class ResultsWaitPage(WaitPage):   

    after_all_players_arrive = 'get_results'

    @staticmethod
    def is_displayed(player):
        return not player.participant.is_dropout and player.participant.condition in ['group', 'voting']

class GroupResult(Page):

    timeout_seconds = C.TIMEOUT_INFO

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

    timeout_seconds = C.TIMEOUT_INFO
    
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
                 ConditionChoice,
                OptimalChoices, 
                GetReady,
                 GroupDecision,
                 VotingDecision,
                 ResultsWaitPage,
                 GroupResult,
                 VotingResult]
