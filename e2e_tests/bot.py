"""A browser bot that plays through the experiment like a straightforward participant.

It looks at which page it is on, fills in the form the way participant_answers.py
says, presses Next, and repeats until it reaches the final page.

A bot can also be given a DropoutPlan: in one round of the real group game it
either sits idle on the decision page, or closes its window and never returns.
"""

import asyncio
import random
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.async_api import Error as PlaywrightError

from participant_answers import (
    PAGES,
    WAIT_PAGE,
    KEYBOARD_PAGE,
    FINAL_PAGE,
    CONDITION_SEEN_ON_PAGE,
    app_and_page_from_url_path,
    choose_lottery,
)

SECONDS_TO_WAIT_FOR_NEXT_PAGE = 30
# Grouping can take 12 minutes before a participant is sent on to play alone.
SECONDS_TO_WAIT_ON_WAIT_PAGE = 15 * 60
# The experiment gives 90 seconds for a decision. An idle participant should be removed soon after.
SECONDS_UNTIL_AN_IDLE_PARTICIPANT_IS_REMOVED = 90 + 30

REAL_GROUP_GAME_DECISION_PAGES = {("game_group", "GroupDecision"), ("game_group", "VotingDecision")}

SIT_IDLE = "idle"
QUIT_ON_DECISION_PAGE = "quit before deciding"
QUIT_AFTER_DECIDING = "quit after deciding"
WAYS_TO_DROP_OUT = [SIT_IDLE, QUIT_ON_DECISION_PAGE, QUIT_AFTER_DECIDING]


@dataclass
class DropoutPlan:
    how: str
    round_number: int


class BotGotStuck(Exception):
    pass


class Bot:

    def __init__(self, name, page, action_delay_seconds, dropout_plan=None, fills_in_every_text_box=False):
        self.name = name
        self.page = page
        self.action_delay_seconds = action_delay_seconds
        self.dropout_plan = dropout_plan
        # A crude form-filling bot: types into any text box it finds. The experiment's honeypot should catch it.
        self.fills_in_every_text_box = fills_in_every_text_box

        self.condition = None
        self.saw_optimal_strategy = False
        self.pages_completed = 0
        self.times_seen = Counter()                  # (app, page) -> how many times this bot has been shown it
        self.submitted_answers = defaultdict(dict)   # (app, round number) -> {field name: value the bot submitted}
        self.game_round = 0
        self.bonus_pence = None
        self.finished = False
        self.dropped_out = False        # sat idle or closed its window, as planned
        self.closed_window_at = None
        self.problem = None
        self.current_app = None
        self.server_record = None       # filled in after the run, from the server's data export

    @property
    def has_closed_window(self):
        return self.closed_window_at is not None

    async def play(self, join_url):
        await self.page.goto(f"{join_url}?participant_label={self.name}")
        while not self.finished and not self.has_closed_window:
            await self.complete_current_page()
        if self.finished:
            self.say(f"finished with a bonus of {self.bonus_pence}p")

    async def complete_current_page(self):
        url_path = urlparse(self.page.url).path
        app_and_page = app_and_page_from_url_path(url_path)
        if app_and_page not in PAGES:
            page_title = await self.page.title()
            raise BotGotStuck(f"Landed on a page the bot does not know: {self.page.url} (title: {page_title})")
        self.note_progress(*app_and_page)
        what_to_do = PAGES[app_and_page]

        if what_to_do == FINAL_PAGE:
            self.bonus_pence = await self.read_bonus_in_pence()
            self.finished = True
            return

        if what_to_do == WAIT_PAGE:
            await self.wait_until_page_changes(url_path, SECONDS_TO_WAIT_ON_WAIT_PAGE)
            return

        # Each page is shown at most once per round, so the number of times we have seen it is the round number.
        self.times_seen[app_and_page] += 1
        round_number = self.times_seen[app_and_page]

        how_to_drop_out_now = self.how_to_drop_out_on_this_page(app_and_page, round_number)
        if how_to_drop_out_now == SIT_IDLE:
            await self.sit_idle_until_removed(url_path)
            return
        if how_to_drop_out_now == QUIT_ON_DECISION_PAGE:
            self.close_window_for_good()
            return

        await self.pause_like_a_person()
        if what_to_do == KEYBOARD_PAGE:
            lottery = choose_lottery()
            await self.press_key_for_lottery(lottery)
            answers = {"lottery_decision": lottery}
        else:
            answers = what_to_do(await self.page.content())
            for field_name, value in answers.items():
                await self.fill_field(field_name, value)
            if self.fills_in_every_text_box:
                await self.fill_in_every_empty_text_box()
            await self.page.click(".otree-btn-next")
        await self.wait_until_page_changes(url_path, SECONDS_TO_WAIT_FOR_NEXT_PAGE)
        self.pages_completed += 1
        app = app_and_page[0]
        self.submitted_answers[(app, round_number)].update(answers)

        if how_to_drop_out_now == QUIT_AFTER_DECIDING:
            self.close_window_for_good()

    def how_to_drop_out_on_this_page(self, app_and_page, round_number):
        """Returns one of WAYS_TO_DROP_OUT if this is the planned moment, otherwise None."""
        if app_and_page not in REAL_GROUP_GAME_DECISION_PAGES:
            return None
        self.game_round = round_number
        is_planned_round = self.dropout_plan is not None and self.game_round == self.dropout_plan.round_number
        return self.dropout_plan.how if is_planned_round else None

    async def sit_idle_until_removed(self, url_path):
        self.say(f"sitting idle on the decision page of round {self.game_round}")
        await self.wait_until_page_changes(url_path, SECONDS_UNTIL_AN_IDLE_PARTICIPANT_IS_REMOVED)
        app, page_name = app_and_page_from_url_path(urlparse(self.page.url).path)
        if app != "payment":
            raise BotGotStuck(f"Sat idle on a decision page, but was sent to {app}/{page_name} instead of the final survey")
        self.dropped_out = True
        self.say("was removed from the game for idling")

    def close_window_for_good(self):
        """The runner closes the window once play() returns. From here the bot never touches the page again."""
        self.say(f"closing its window in round {self.game_round} ({self.dropout_plan.how})")
        self.dropped_out = True
        self.closed_window_at = time.time()

    async def fill_field(self, field_name, value):
        field = self.page.locator(f'[name="{field_name}"]')
        is_radio_button = await field.first.get_attribute("type") == "radio"
        if is_radio_button:
            await self.page.check(f'input[name="{field_name}"][value="{value}"]')
        else:
            await field.fill(value)

    async def fill_in_every_empty_text_box(self):
        text_boxes = self.page.locator('input[type="text"], textarea')
        for index in range(await text_boxes.count()):
            text_box = text_boxes.nth(index)
            if await text_box.input_value() == "":
                await text_box.fill("filled in by a form-filling bot")

    async def press_key_for_lottery(self, lottery):
        """Individual game: F picks the left lottery, J the right. Which side is risky varies by participant."""
        game_screen = self.page.locator("#game-screen")
        await game_screen.wait_for(state="visible")
        image_source = await game_screen.locator("img").get_attribute("src")
        risky_is_on_the_right = "switched" in image_source
        if risky_is_on_the_right:
            key_for = {"safe": "f", "risky": "j"}
        else:
            key_for = {"risky": "f", "safe": "j"}
        await self.page.keyboard.press(key_for[lottery])

    async def wait_until_page_changes(self, url_path_before, timeout_seconds):
        """Watches the address rather than waiting for one navigation to finish.

        Wait pages reload themselves every so often (same path, with ?reload=1). When
        such a reload collides with the move to the next page, one of the two
        navigations is aborted, which is harmless but must not count as a failure.
        """
        give_up_at = time.monotonic() + timeout_seconds
        while urlparse(self.page.url).path == url_path_before:
            if time.monotonic() > give_up_at:
                form_errors = await self.page.locator(".otree-form-errors, .form-control-errors").all_inner_texts()
                page_title = await self.page.title()
                raise BotGotStuck(
                    f"Still on {url_path_before} after {timeout_seconds} seconds "
                    f"(title: {page_title}; form errors: {form_errors})"
                )
            await asyncio.sleep(0.1)
        try:
            await self.page.wait_for_load_state("domcontentloaded")
        except PlaywrightError:
            pass   # the page moved on again while loading; the next look at the address sorts it out

    async def read_bonus_in_pence(self):
        thank_you_text = await self.page.inner_text("body")
        bonus_statement = re.search(r"bonus payment of (\d+)p", thank_you_text)
        return int(bonus_statement.group(1)) if bonus_statement else 0

    async def pause_like_a_person(self):
        await asyncio.sleep(random.uniform(0.5, 1.5) * self.action_delay_seconds)

    def note_progress(self, app, page_name):
        if page_name in CONDITION_SEEN_ON_PAGE:
            self.condition = CONDITION_SEEN_ON_PAGE[page_name]
        if page_name == "OptimalChoices":
            self.saw_optimal_strategy = True
        if app != self.current_app:
            self.current_app = app
            self.say(f"started {app}")
            if (app, page_name) == ("game_group", "GroupWaitPage"):
                self.say("waiting to be put in a group")

    def say(self, message):
        print(f"{time.strftime('%H:%M:%S')}  {self.name}  {message}", flush=True)
