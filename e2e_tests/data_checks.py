"""Checks the server's exported data against what the bots actually did and saw.

Each bot keeps a record of every answer it submitted. Here we look each one up
in the session's data export, and also check a few things the analysis and the
bonus payments will depend on.
"""

from collections import defaultdict

# The app name in a page's address is not always the app's folder name, which is what the export uses.
EXPORT_NAME_OF_APP = {"practice": "practice_indy", "game": "game_indy"}
ROUNDS_IN_GROUP_GAME = 20
MOST_MISMATCHES_TO_LIST_PER_BOT = 3


def as_exported(submitted_value):
    """The export writes yes/no answers as 1 and 0."""
    return {"True": "1", "False": "0"}.get(submitted_value, submitted_value)


def compare_submitted_answers_with_export(bots):
    """Returns (number of answers compared, list of problems)."""
    number_compared = 0
    problems = []
    for bot in bots:
        if bot.server_record is None:
            continue
        mismatches = []
        for (app, round_number), answers in bot.submitted_answers.items():
            export_app = EXPORT_NAME_OF_APP.get(app, app)
            for field_name, submitted_value in answers.items():
                column = f"{export_app}.{round_number}.player.{field_name}"
                exported_value = bot.server_record.get(column)
                number_compared += 1
                if exported_value != as_exported(submitted_value):
                    mismatches.append(f"{column}: submitted {submitted_value!r}, export has {exported_value!r}")
        for mismatch in mismatches[:MOST_MISMATCHES_TO_LIST_PER_BOT]:
            problems.append(f"{bot.name} {mismatch}")
        if len(mismatches) > MOST_MISMATCHES_TO_LIST_PER_BOT:
            problems.append(f"{bot.name} has {len(mismatches) - MOST_MISMATCHES_TO_LIST_PER_BOT} more answers that differ from the export.")
    return number_compared, problems


def find_condition_and_bonus_problems(bots):
    problems = []
    for bot in bots:
        record = bot.server_record
        if record is None or bot.condition is None:
            continue

        if record.get("participant.condition") != bot.condition:
            problems.append(
                f"{bot.name} was shown the {bot.condition} pages, but the export says its condition is {record.get('participant.condition')!r}."
            )

        in_a_group_condition = bot.condition in ("group", "voting")
        if in_a_group_condition and bot.finished:
            export_says_optimal = record.get("participant.information") == "optimal"
            if export_says_optimal != bot.saw_optimal_strategy:
                problems.append(
                    f"{bot.name}: export says information is {record.get('participant.information')!r}, "
                    f"but the bot {'saw' if bot.saw_optimal_strategy else 'did not see'} the optimal strategy page."
                )

        if bot.finished and not bot.dropped_out:
            exported_bonus = int(record.get("participant.game_current_bonus") or 0)
            if exported_bonus != bot.bonus_pence:
                problems.append(
                    f"{bot.name} was told its bonus is {bot.bonus_pence}p, but the export says {exported_bonus}p."
                )
    return problems


HONEYPOT_COLUMN = "consent.1.player.further_details"


def honeypot_caught(bot):
    return bool(bot.server_record.get(HONEYPOT_COLUMN))


def find_honeypot_problems(bots):
    """The honeypot should catch exactly the bots that fill in every text box, and nobody else."""
    bots_with_records = [bot for bot in bots if bot.server_record is not None]
    if not bots_with_records:
        return []
    if HONEYPOT_COLUMN not in bots_with_records[0].server_record:
        return [f"The export has no honeypot column ({HONEYPOT_COLUMN}). Is the honeypot deployed on this server?"]

    problems = []
    for bot in bots_with_records:
        if bot.fills_in_every_text_box and not honeypot_caught(bot):
            problems.append(f"{bot.name} fills in every text box, but the honeypot did not catch it.")
        if honeypot_caught(bot) and not bot.fills_in_every_text_box:
            problems.append(f"{bot.name} played like a normal participant, but the honeypot flagged it.")
    return problems


def find_median_vote_problems(bots):
    """In a full voting group with no dropouts, the number of risky lotteries played each round
    should be the middle value of the five votes the bots cast."""
    members_of_group = defaultdict(list)
    for bot in bots:
        if bot.server_record is not None and bot.condition == "voting":
            members_of_group[bot.server_record.get("participant.unique_group_id")].append(bot)

    problems = []
    for group_id, members in members_of_group.items():
        everyone_played_every_round = all(member.finished and not member.dropped_out for member in members)
        if len(members) != 5 or not everyone_played_every_round:
            continue
        for round_number in range(1, ROUNDS_IN_GROUP_GAME + 1):
            votes_cast = [member.submitted_answers[("game_group", round_number)].get("voter_decision") for member in members]
            if not all(vote is not None and vote.isdigit() for vote in votes_cast):
                continue
            votes = sorted(int(vote) for vote in votes_cast)
            middle_vote = votes[2]
            risky_lotteries_played = sum(
                member.server_record.get(f"game_group.{round_number}.player.lottery_action") == "risky" for member in members
            )
            if risky_lotteries_played != middle_vote:
                problems.append(
                    f"Group {group_id}, round {round_number}: votes were {votes}, so {middle_vote} risky lotteries "
                    f"should have been played, but the export shows {risky_lotteries_played}."
                )
    return problems
