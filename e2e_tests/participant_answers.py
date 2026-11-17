"""What a sensible participant submits on each page of the experiment.

Pure Python. It knows page names and form fields, and nothing about browsers.

Pages are keyed by (app, page), exactly as they appear in an oTree URL:

    /p/<participant_code>/<app>/<PageName>/<page_index>

Each entry is either a function that takes the page's HTML and returns the form
answers as {field_name: value}, or one of the markers below for pages that have
no ordinary form.
"""

import random

WAIT_PAGE = "wait page"            # nothing to submit, oTree moves us on when ready
KEYBOARD_PAGE = "keyboard page"    # individual game: the choice is a key press
FINAL_PAGE = "final page"          # end of the experiment

RISKY_CHOICE_PROBABILITY = 0.08    # close to the optimal rate, so most groups survive
VOTES = [0, 1, 2]
VOTE_WEIGHTS = [6, 3, 1]           # mostly vote for 0 risky lotteries, sometimes 1, rarely 2


def choose_lottery():
    return "risky" if random.random() < RISKY_CHOICE_PROBABILITY else "safe"


def just_press_next(page_html):
    return {}


def give_consent(page_html):
    return {f"consent_{i}": "True" for i in range(1, 8)}


def answer_first_quiz(page_html):
    plays_alone = "total of 100 rounds" in page_html
    return {
        "quiz_extinction": "lose_all",
        "quiz_total_rounds": "total_100" if plays_alone else "total_20",
    }


def answer_group_quiz(page_html):
    return {"quiz_group_extinction": "extinct_all"}


def answer_voting_quiz(page_html):
    return {"quiz_group_extinction": "extinct_all", "quiz_voting": "voting_median"}


def answer_optimal_strategy_quiz(page_html):
    return {"optimal_comprehension_group": "8"}


def choose_lottery_in_group(page_html):
    return {"lottery_action": choose_lottery()}


def vote_for_number_of_risky_lotteries(page_html):
    vote = random.choices(VOTES, weights=VOTE_WEIGHTS)[0]
    return {"voter_decision": str(vote)}


def answer_final_survey(page_html):
    return {
        "strategy_question": "I mostly went for the safe lottery because extinction would wipe out the whole bonus.",
        "free_text_box": "It all worked fine for me. (Automated test participant.)",
    }


def answer_optimal_belief(page_html):
    return {"optimal_belief": random.choice(["Yes", "No", "I'm Not Sure"])}


def explain_optimal_belief(page_html):
    return {"optimal_belief_text": "I was not sure the suggested number of risky lotteries was really the best."}


PAGES = {
    ("consent", "Welcome"): just_press_next,
    ("consent", "ParticipantConsent"): give_consent,

    ("instructions", "Instructions1"): answer_first_quiz,
    ("instructions", "GroupInstructions2"): answer_group_quiz,
    ("instructions", "VoterInstructions2"): answer_voting_quiz,
    ("instructions", "Screenshot"): just_press_next,
    ("instructions", "PracticeGetReady"): just_press_next,

    ("practice_group", "GroupWaitPage"): WAIT_PAGE,
    ("practice_group", "GroupDecision"): choose_lottery_in_group,
    ("practice_group", "VotingDecision"): vote_for_number_of_risky_lotteries,
    ("practice_group", "ResultsWaitPage"): WAIT_PAGE,
    ("practice_group", "GroupResult"): just_press_next,
    ("practice_group", "VotingResult"): just_press_next,

    ("practice", "IndyDecision"): KEYBOARD_PAGE,

    ("game_group", "GroupWaitPage"): WAIT_PAGE,
    ("game_group", "OptimalChoices"): answer_optimal_strategy_quiz,
    ("game_group", "GetReady"): just_press_next,
    ("game_group", "GroupDecision"): choose_lottery_in_group,
    ("game_group", "VotingDecision"): vote_for_number_of_risky_lotteries,
    ("game_group", "ResultsWaitPage"): WAIT_PAGE,
    ("game_group", "GroupResult"): just_press_next,
    ("game_group", "VotingResult"): just_press_next,

    ("game", "GetReady"): just_press_next,
    ("game", "IndyDecision"): KEYBOARD_PAGE,

    ("payment", "PostSurvey"): answer_final_survey,
    ("payment", "PostSurveyOptimal"): answer_optimal_belief,
    ("payment", "PostSurveyOptimal2"): explain_optimal_belief,
    ("payment", "ThankYou"): FINAL_PAGE,
}

# Pages that tell us which condition the server assigned to this participant.
CONDITION_SEEN_ON_PAGE = {
    "GroupDecision": "group",
    "VotingDecision": "voting",
    "IndyDecision": "indy",
}


def app_and_page_from_url_path(url_path):
    """'/p/abc123/game_group/VotingDecision/57' -> ('game_group', 'VotingDecision')"""
    parts = url_path.strip("/").split("/")
    is_participant_page = len(parts) >= 4 and parts[0] == "p"
    if not is_participant_page:
        return None
    return parts[2], parts[3]
