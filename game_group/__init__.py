from otree.api import *

import random

doc = """
Your app description
"""

class C(BaseConstants):
    NAME_IN_URL = 'game_group'
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


class ConditionChoice(Page):
    form_model = "player"
    form_fields = ["condition_choice"]

    def is_displayed(player):
        return player.round_number == 1

    def before_next_page(player, timeout_happened):
        player.participant.vars['condition'] = player.condition_choice

class GroupDecision(Page):

    form_model = 'player'
    form_fields = ['lottery_decision']
    
    def is_displayed(player):
        return player.participant.condition == 'group'


class GroupResult(Page):

    def is_displayed(player):
        return player.participant.condition == 'group'

    def vars_for_template(player):

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

        risky_count = random.randint(0, 4)
        if player.lottery_decision == 'risky':
            risky_count += 1
        safe_count = 5 - risky_count

        for i in range(risky_count):
            if random.random() < 0.05:
                other_extinction = True
                player.participant.vars['extinct'] = True
                player.participant.vars['last_result'] = "extinction"

        return {
            'risky_count': risky_count,
            'safe_count': safe_count,
        }
    
class VotingDecision(Page):

    form_model = 'player'
    form_fields = ['voter_decision']
    
    def is_displayed(player):
        return player.participant.condition == 'voting'

class VotingResult(Page):
    
    def is_displayed(player):
        return player.participant.condition == 'voting'
    
    def vars_for_template(player):

        player_votes = [random.randint(0, 5) for i in range(4)]
        player_votes.append(player.voter_decision)
        # Sort in place
        player_votes.sort()
        risky_count= player_votes[2]
        safe_count = 5 - risky_count

        prob_this_player_risky = 0.2*risky_count
        random_roll_a = random.random()
        if random_roll_a < prob_this_player_risky:
            player.lottery_decision = 'risky'
        else:
            player.lottery_decision = 'safe'

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

        for i in range(risky_count):
            if random.random() < 0.05:
                other_extinction = True
                player.participant.vars['extinct'] = True
                player.participant.vars['last_result'] = "extinction"

        # Replace middle value with bold text of value

        player_votes[2] = f"<strong>{player_votes[2]}</strong>"
       

        player_votes_string = ', '.join([str(i) for i in player_votes])        


        return {
            'player_votes': player_votes_string,
            'risky_count': risky_count,
            'safe_count': safe_count,
        }

page_sequence = [ConditionChoice,  
                 GroupDecision,
                 GroupResult,
                 VotingDecision,
                 VotingResult]
