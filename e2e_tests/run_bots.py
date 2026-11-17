"""Send browser bots through the experiment as ordinary participants.

Each bot is a real Chromium window with its own cookies. Bots join through the session-wide link,
so the server assigns their condition and forms their groups, as it would for
people arriving from Prolific.

    python e2e_tests/run_bots.py http://localhost:8000
    python e2e_tests/run_bots.py http://localhost:8000 --dropouts 4
    python e2e_tests/run_bots.py https://your-app.herokuapp.com --rest-key KEY --admin-password PASSWORD
    python e2e_tests/run_bots.py http://localhost:8000/join/abcdefgh

Given a server address, a new session is created for the bots. On a server
with OTREE_AUTH_LEVEL set, that needs the server's OTREE_REST_KEY, and reading
group ids back from the data export needs the admin password.

Given a session-wide link (.../join/...), the bots join that existing session
instead. The summary then has no group ids and no server-side checks, because
the link does not tell us which session's data to read.

Bots that are not placed in a full group wait on the grouping page for the
experiment's 12 minute limit and then play on alone, as real participants would.

--dropouts N makes N bots drop out in a random round of the real group game,
by sitting idle on the decision page until the page times out. This works
against any server, including `otree devserver`.

--close-windows makes some of those bots close their window instead, before
or after deciding. Only use this against Heroku (or another server running
`otree prodserver` on Postgres). Timing out a participant whose window is
closed is done by the server, which devserver does not do at all and which
fails on a local SQLite database, so their group would wait forever.
"""

import argparse
import asyncio
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from bot import Bot, DropoutPlan, SIT_IDLE, WAYS_TO_DROP_OUT
from data_checks import (
    compare_submitted_answers_with_export,
    find_condition_and_bonus_problems,
    find_median_vote_problems,
)
from server_records import read_participant_records

OUTPUT_FOLDER = Path(__file__).parent / "output"
SECONDS_BETWEEN_ARRIVALS = 1
ROUNDS_IN_GROUP_GAME = 20
# A vanished participant is walked forward by the server: 10s after a wait page,
# then the result page's 30s limit, then the decision page's 90s limit, each with a few seconds' slack.
SECONDS_FOR_SERVER_TO_REMOVE_A_VANISHED_PARTICIPANT = 180

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 760
WINDOWS_PER_ROW = 5
WINDOW_STEP_RIGHT = 190
WINDOW_STEP_DOWN = 60

UNKNOWN = "?"
NOT_APPLICABLE = "-"


def read_options():
    parser = argparse.ArgumentParser(description="Send browser bots through the experiment.")
    parser.add_argument("target", help="server address, or a session-wide link (.../join/...)")
    parser.add_argument("--bots", type=int, default=24, help="number of bots (default 24)")
    parser.add_argument("--dropouts", type=int, default=0, help="how many of the bots drop out during the group game (default 0)")
    parser.add_argument("--close-windows", action="store_true", help="some dropouts close their window instead of idling (Heroku only)")
    parser.add_argument("--config", default="full_experiment", help="session config to create (default full_experiment)")
    parser.add_argument("--rest-key", default=os.environ.get("OTREE_REST_KEY"), help="server's OTREE_REST_KEY, if it has one")
    parser.add_argument("--admin-password", default=os.environ.get("OTREE_ADMIN_PASSWORD"), help="server's admin password, if it needs a login")
    parser.add_argument("--delay", type=float, default=0.3, help="typical pause before each action, in seconds (default 0.3)")
    parser.add_argument("--headless", action="store_true", help="run without visible browser windows")
    return parser.parse_args()


def is_session_wide_link(target):
    return "/join/" in target or "/room/" in target


async def create_session(api, server_url, session_config_name, number_of_participants):
    response = await api.post(
        f"{server_url}/api/sessions",
        data={"session_config_name": session_config_name, "num_participants": number_of_participants},
    )
    if not response.ok:
        sys.exit(f"Could not create a session on {server_url}: HTTP {response.status} {await response.text()}")
    session = await response.json()
    # Rebuild the link from the address we were given, in case the server reports a different scheme or host.
    join_url = server_url + urlparse(session["session_wide_url"]).path
    return join_url, session["code"]


def plan_dropouts(number_of_bots, number_of_dropouts, may_close_windows):
    """Returns {bot number: DropoutPlan}. A bot that lands in the individual condition never gets to use its plan."""
    ways_to_drop_out = WAYS_TO_DROP_OUT if may_close_windows else [SIT_IDLE]
    bots_that_drop_out = random.sample(range(number_of_bots), min(number_of_dropouts, number_of_bots))
    return {
        bot_number: DropoutPlan(
            how=ways_to_drop_out[position % len(ways_to_drop_out)],
            round_number=random.randint(1, ROUNDS_IN_GROUP_GAME),
        )
        for position, bot_number in enumerate(bots_that_drop_out)
    }


async def spread_windows_across_screen(page, bot_number):
    """Without this every bot's window opens in the same spot. Cosmetic only, so failures are ignored."""
    column = bot_number % WINDOWS_PER_ROW
    row = bot_number // WINDOWS_PER_ROW
    bounds = {
        "left": column * WINDOW_STEP_RIGHT,
        "top": 30 + row * WINDOW_STEP_DOWN,
        "width": WINDOW_WIDTH,
        "height": WINDOW_HEIGHT,
    }
    try:
        chromium = await page.context.new_cdp_session(page)
        window = await chromium.send("Browser.getWindowForTarget")
        await chromium.send("Browser.setWindowBounds", {"windowId": window["windowId"], "bounds": bounds})
    except Exception:
        pass


async def save_screenshot_if_possible(page, name):
    try:
        OUTPUT_FOLDER.mkdir(exist_ok=True)
        await page.screenshot(path=OUTPUT_FOLDER / f"{name}_stuck.png", full_page=True)
    except Exception:
        pass


async def run_one_bot(browser, bot_number, join_url, options, dropout_plan):
    """Each bot gets its own window and its own cookies, inside one shared browser."""
    name = f"bot_{bot_number + 1:02d}"
    await asyncio.sleep(bot_number * SECONDS_BETWEEN_ARRIVALS)

    private_window = await browser.new_context(no_viewport=True)
    page = await private_window.new_page()
    await spread_windows_across_screen(page, bot_number)
    bot = Bot(name, page, options.delay, dropout_plan)
    try:
        await bot.play(join_url)
    except Exception as problem:
        bot.problem = str(problem).splitlines()[0]
        bot.say(f"STUCK: {bot.problem}")
        await save_screenshot_if_possible(page, name)
    finally:
        await private_window.close()
    return bot


async def wait_for_server_to_remove_vanished_bots(bots):
    times_windows_closed = [bot.closed_window_at for bot in bots if bot.has_closed_window]
    if not times_windows_closed:
        return
    seconds_left = max(times_windows_closed) + SECONDS_FOR_SERVER_TO_REMOVE_A_VANISHED_PARTICIPANT - time.time()
    if seconds_left > 0:
        print(f"Waiting {seconds_left:.0f}s for the server to time out the bots that closed their windows.")
        await asyncio.sleep(seconds_left)


def group_id_of(bot):
    if bot.server_record is None:
        return UNKNOWN
    return bot.server_record.get("participant.unique_group_id") or NOT_APPLICABLE


def server_says(bot, participant_field):
    """True or False from the server's record of a yes/no participant field, or None if we have no record."""
    if bot.server_record is None:
        return None
    return bot.server_record.get(f"participant.{participant_field}") in ("1", "True")


def describe_dropout(bot):
    if not bot.dropped_out:
        return NOT_APPLICABLE
    return f"{bot.dropout_plan.how}, round {bot.dropout_plan.round_number}"


def describe_outcome(bot):
    if bot.problem:
        return f"STUCK: {bot.problem}"
    if bot.has_closed_window:
        return "closed its window"
    if bot.dropped_out:
        return "removed for idling, then finished the survey"
    return "finished"


def find_problems(bots):
    problems = []
    for bot in bots:
        if bot.problem:
            problems.append(f"{bot.name} got stuck: {bot.problem}")
        if bot.dropped_out and bot.finished and bot.bonus_pence:
            problems.append(f"{bot.name} dropped out, but its Thank You page showed a bonus of {bot.bonus_pence}p.")
        if bot.server_record is None:
            continue

        marked_as_dropout = server_says(bot, "is_dropout")
        if bot.dropped_out and not marked_as_dropout:
            problems.append(f"{bot.name} dropped out ({describe_dropout(bot)}), but the server did not mark it as a dropout.")
        if marked_as_dropout and not bot.dropped_out:
            problems.append(f"{bot.name} played normally, but the server marked it as a dropout.")

        app_on_server = bot.server_record.get("participant._current_app_name")
        if bot.has_closed_window and app_on_server != "payment":
            problems.append(
                f"{bot.name} closed its window, but the server left it in {app_on_server} instead of moving it on to the final survey."
            )

    number_compared, answer_problems = compare_submitted_answers_with_export(bots)
    return problems + answer_problems + find_condition_and_bonus_problems(bots) + find_median_vote_problems(bots)


def print_summary(bots):
    bots = sorted(bots, key=lambda bot: (bot.condition or UNKNOWN, group_id_of(bot), bot.name))
    yes_or_no = {True: "yes", False: "no", None: UNKNOWN}

    print()
    print(
        f"{'bot':8}{'condition':11}{'optimal info':14}{'group':12}{'extinct':9}"
        f"{'dropped out':32}{'pages':7}{'bonus':7}outcome"
    )
    for bot in bots:
        condition = bot.condition or UNKNOWN
        in_a_group_condition = condition in ("group", "voting")
        optimal_info = yes_or_no[bot.saw_optimal_strategy] if in_a_group_condition else NOT_APPLICABLE
        extinct = yes_or_no[server_says(bot, "game_extinct")]
        bonus = f"{bot.bonus_pence}p" if bot.finished else "-"
        print(
            f"{bot.name:8}{condition:11}{optimal_info:14}{group_id_of(bot):12}{extinct:9}"
            f"{describe_dropout(bot):32}{bot.pages_completed:<7}{bonus:7}{describe_outcome(bot)}"
        )

    print()
    print_extinction_counts(bots)
    print(f"{sum(bot.finished for bot in bots)} of {len(bots)} bots reached the Thank You page.")
    number_compared, _ = compare_submitted_answers_with_export(bots)
    if number_compared:
        print(f"Compared {number_compared} answers the bots submitted with the exported data.")

    problems = find_problems(bots)
    print()
    if problems:
        print("PROBLEMS")
        for problem in problems:
            print(f"  {problem}")
        if any(bot.problem for bot in bots):
            print(f"  Screenshots of stuck bots are in {OUTPUT_FOLDER}")
    else:
        print("No problems found.")


def print_extinction_counts(bots):
    """Extinction is counted once per group, since a group goes extinct together."""
    bots_with_records = [bot for bot in bots if bot.server_record is not None]
    if not bots_with_records:
        print("No group ids, extinction counts or dropout checks: they need the server's data export, which was not available.")
        return

    members_of_group = defaultdict(list)
    for bot in bots_with_records:
        if group_id_of(bot) != NOT_APPLICABLE:
            members_of_group[group_id_of(bot)].append(bot)
    full_groups = [members for members in members_of_group.values() if len(members) == 5]
    playing_alone = [members for members in members_of_group.values() if len(members) < 5]
    individuals = [[bot] for bot in bots_with_records if bot.condition == "indy"]

    for kind, units in (
        ("full groups of five", full_groups),
        ("playing alone in a group condition", playing_alone),
        ("individual condition", individuals),
    ):
        if units:
            number_extinct = sum(server_says(unit[0], "game_extinct") for unit in units)
            print(f"Extinct, {kind}: {number_extinct} of {len(units)}")

    # Those playing alone are left out here: their simulated partners' lotteries are not in the export.
    risky_lotteries = extinctions = 0
    for unit in full_groups + individuals:
        risky_lotteries_of_unit, extinctions_of_unit = risky_lotteries_and_extinctions(unit)
        risky_lotteries += risky_lotteries_of_unit
        extinctions += extinctions_of_unit
    if risky_lotteries:
        print(
            f"Risky lotteries played by individuals and full groups: {risky_lotteries}, "
            f"of which {extinctions} ended in extinction ({extinctions / risky_lotteries:.0%}; the game is set to 5%)."
        )


GAME_APP_AND_CHOICE_FIELD = {
    "indy": ("game_indy", "lottery_decision", 100),
    "group": ("game_group", "lottery_action", ROUNDS_IN_GROUP_GAME),
    "voting": ("game_group", "lottery_action", ROUNDS_IN_GROUP_GAME),
}


def risky_lotteries_and_extinctions(members):
    """For one individual or one full group: risky lotteries played while still alive, and whether one ended it."""
    app, choice_field, number_of_rounds = GAME_APP_AND_CHOICE_FIELD[members[0].condition]
    risky_lotteries_played = 0
    for round_number in range(1, number_of_rounds + 1):
        risky_lotteries_played += sum(
            member.server_record.get(f"{app}.{round_number}.player.{choice_field}") == "risky" for member in members
        )
        went_extinct_this_round = members[0].server_record.get(f"{app}.{round_number}.player.game_extinct") == "1"
        if went_extinct_this_round:
            return risky_lotteries_played, 1
    return risky_lotteries_played, 0


async def run_bots(options):
    target = options.target.rstrip("/")
    async with async_playwright() as playwright:
        rest_headers = {"otree-rest-key": options.rest_key} if options.rest_key else {}
        api = await playwright.request.new_context(extra_http_headers=rest_headers)

        if is_session_wide_link(target):
            join_url = target.split("?")[0]
            server_url = session_code = None
        else:
            server_url = target
            join_url, session_code = await create_session(api, server_url, options.config, options.bots)
            print(f"Created session {session_code} ({options.config}) with {options.bots} participants.")
        print(f"Bots are joining through {join_url}")
        dropout_plans = plan_dropouts(options.bots, options.dropouts, options.close_windows)
        if dropout_plans:
            print(f"{len(dropout_plans)} bots are set to drop out during the group game.")
        print()

        browser = await playwright.chromium.launch(headless=options.headless)
        bots = await asyncio.gather(
            *(
                run_one_bot(browser, bot_number, join_url, options, dropout_plans.get(bot_number))
                for bot_number in range(options.bots)
            )
        )
        await browser.close()

        if session_code:
            await wait_for_server_to_remove_vanished_bots(bots)
            records = await read_participant_records(api, server_url, session_code, options.admin_password)
            for bot in bots:
                bot.server_record = records.get(bot.name)
        await api.dispose()

    print_summary(bots)
    return not find_problems(bots)


if __name__ == "__main__":
    no_problems = asyncio.run(run_bots(read_options()))
    sys.exit(0 if no_problems else 1)
