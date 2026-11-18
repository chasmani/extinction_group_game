from os import environ

FULL_EXPERIMENT = ['consent', 'instructions', 'practice_group', 'practice_indy', 'game_group', 'game_indy', 'payment']

SESSION_CONFIGS = [
    dict(
        name='demo_individual',
        display_name='Individual',
        app_sequence=FULL_EXPERIMENT,
        num_demo_participants=1,
        condition='indy',
    ),
    dict(
        name='demo_group_no_info',
        display_name='Group, independent choices, no strategy information',
        app_sequence=FULL_EXPERIMENT,
        num_demo_participants=5,
        condition='group',
        information='none',
    ),
    dict(
        name='demo_group_optimal',
        display_name='Group, independent choices, with optimal strategy information',
        app_sequence=FULL_EXPERIMENT,
        num_demo_participants=5,
        condition='group',
        information='optimal',
    ),
    dict(
        name='demo_voting_no_info',
        display_name='Group, voting, no strategy information',
        app_sequence=FULL_EXPERIMENT,
        num_demo_participants=5,
        condition='voting',
        information='none',
    ),
    dict(
        name='demo_voting_optimal',
        display_name='Group, voting, with optimal strategy information',
        app_sequence=FULL_EXPERIMENT,
        num_demo_participants=5,
        condition='voting',
        information='optimal',
    ),
    dict(
        name='full_experiment',
        display_name='Full experiment, random assignment',
        app_sequence=FULL_EXPERIMENT,
        num_demo_participants=10,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)
PARTICIPANT_FIELDS = [
    "practice_extinct",
    "practice_current_bonus",
    "game_current_bonus",
    "game_extinct",
    "practice_current_group_bonus",
    "game_current_group_bonus",
    "last_result",
    "group_last_result",
    "condition",
    "information",
    "wrong_answers",
    "exclusion",
    "is_dropout",
    "switched",
    "unique_group_id",
    "wait_page_arrival",
    "risky_count",
    "player_votes"
]

SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '9656245084441'
