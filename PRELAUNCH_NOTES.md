# Pre-launch notes

Findings from a code review, August 2026, before running the study the "normal"
(non-registered-report) way. **No code changes have been made.** This is a record
only — decide what to action with Max.

Repo history: built Oct 2023 – Aug 2024, last commit "All wrapped up and ready to go".
Piloted on Prolific, deployed on Heroku.

---

## Must fix before real participants

**Prolific completion code is the pilot's.**
`payment/ThankYou.html`, line 15. Hardcoded as `CJCUEL6G`:

    <a href="https://app.prolific.co/submissions/complete?cc=CJCUEL6G">click here</a>

A new Prolific study issues a new code. If this isn't updated, participants cannot
mark the submission complete.

**Ethics and institutional text is from the previous approval.**
`consent/ParticipantConsent.html` and `consent/Welcome.html`:

- UCL banner image (`_static/resources/ucl-banner.png`)
- "Ethics Committee of the UCL Research Department of Experimental Psychology,
  ID No: (EP/2021/005)"
- Principal Investigator listed as Henrik Singmann, h.singmann@ucl.ac.uk
- Data controller given as UCL, data-protection@ucl.ac.uk

Needs to match whatever approval covers the new run.

**`payoff` is never set anywhere in the codebase.**
No app assigns `player.payoff` or `participant.payoff`. Consequences:

- oTree's admin Payments page will show the participation fee only, and zero bonus.
- Bonuses must be computed manually from the `game_current_bonus` participant field
  and pushed to Prolific by hand.

Workable, and may well be what was done in the pilot, but worth knowing in advance
rather than discovering on payment day.

---

## Check against the pre-registration

**Condition allocation is hardcoded.**
`consent/__init__.py`, `ParticipantConsent.before_next_page`:

- 50% `group`
- 50% `voting`

Information condition (`none` / `optimal`) is drawn 50/50 at group formation in
`game_group.group_by_arrival_time_method`, unless overridden by the session config.

Both should match whatever Max pre-registers.

**Grouping timeout.**
`game_group.C.TIMEOUT_GROUPING = 720` seconds. After 12 minutes a waiting participant
is placed in a group of one and plays against four simulated players.

Related data gap: for these solo-padded groups, the simulated players' choices and
results are generated inside `get_results` but never written to any player field.
Only the real participant's row is saved. So solo sessions cannot be fully
reconstructed from the exported data. Charlie's view is that full groups are reliable
in practice and this path is rare — noted here for completeness rather than as a
blocker.

**Decision timeouts.**
`TIMEOUT_CHOICE = 90` s on the decision pages, `TIMEOUT_INFO = 30` s on results pages.
A timeout on a decision page sets `participant.is_dropout = True`, after which that
participant skips all remaining `game_group` pages and advances straight to `payment`.

---

## Cosmetic / low severity

**Currency mismatch in participant-facing text.**
`payment/ThankYou.html` describes the bonus as `{{ ... }}p` (pence), while
`settings.py` sets `REAL_WORLD_CURRENCY_CODE = 'USD'`. Only the template text is shown
to participants, so this is presentational, but it is inconsistent.

**`VotingResult.vars_for_template` mutates a participant field in place.**
`game_group/__init__.py` (and the same code in `practice_group`):

    player_votes = player.participant.player_votes
    player_votes[2] = f"<strong>{player_votes[2]}</strong>"

This writes the HTML back into the stored `player_votes` participant var. Refreshing
the results page nests the tags (`<strong><strong>2</strong></strong>`). Harmless to
the game, mildly scruffy in any participant-vars export.

**Dead form fields referencing non-existent models.**

- `instructions.ConditionChoice` — `condition_choice` exists on the model, fine.
- `practice_indy.ConditionChoice` and `game_indy.ConditionChoice` — declare
  `form_fields = ["lottery_switch_choice"]`, but that field is defined only on the
  `instructions` Player model, not on theirs.
- `game_group.ConditionChoice` — declares `form_fields = ["condition_choice",
  "info_choice"]`; neither exists on the `game_group` Player model.

All three pages have `is_displayed` returning `False`, so they never render and never
error. They would break immediately if anyone re-enabled one.

**`practice_group.expected_value_strategy` is dead code** with different parameters
(`e_risky=5`, `e_safe=0.5`) from the live version in `game_group` (`e_risky=25`,
`e_safe=2.5`). Never called. `scratch.py` at the repo root has the same stale
parameters.

**Practice apps write to `game_*` participant fields.**
`practice_group` imports `get_results` from `game_group`, which writes to
`game_current_bonus`, `game_extinct` and `game_current_group_bonus` rather than the
`practice_*` equivalents. These are reset by `set_game_vars` at the start of round 1
of `game_group`, so no value bleeds into the real game. Confusing to read, correct in
effect.

---

## Environment

Original: Python 3.9.16 (`runtime.txt`), `otree>=5.0.0a21`, unpinned.

That `>=` now resolves to oTree 6.0.15, which requires Python 3.10+ and so refuses to
install on 3.9. Heroku no longer supports 3.9 either.

Resolution: oTree 5.11.5 supports Python 3.7–3.13 (confirmed from `setup.py`,
`SUPPORTED_PY3_VERSIONS = [7, 8, 9, 10, 11, 12, 13]`). So the fix is to stay on the
oTree 5 line and move Python forward, avoiding an oTree 6 migration entirely:

    runtime.txt        python-3.12.11      (exact patch version; Heroku rejects "3.12.x")
    requirements.txt   otree==5.11.5
                       psycopg2-binary==2.9.10
                       numpy==2.2.6

`psycopg2-binary` avoids needing `pg_config` / Postgres headers locally. It is only
used for the production database on Heroku; locally oTree uses SQLite.

The pilot ran on oTree 5.10.x, so 5.11.5 is a minor version bump. Low risk, not zero —
worth one click-through of `full_experiment` in the demo before going live.
