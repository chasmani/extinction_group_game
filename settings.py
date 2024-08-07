from os import environ

SESSION_CONFIGS = [
    dict(
        name='game_individual',
        app_sequence=['game_indy'],
        num_demo_participants=5,
    ),
    dict(
        name='instuctions',
        app_sequence=['instructions'],
        num_demo_participants=5,
    ),
    dict(
        name='game_group',
        app_sequence=['game_group'],
        num_demo_participants=10,
    ),
    dict(
        name='practice_group',
        app_sequence=['practice_group'],
        num_demo_participants=10,
    ),
    dict(
        name='payment',
        app_sequence=['payment'],
        num_demo_participants=5,
    ),
    dict(
        name="full_experiment",
        app_sequence=['consent', 'instructions', 'practice_indy', 'practice_group', 'game_indy', 'game_group', 'payment'],
        num_demo_participants=10,
    ),
    dict(name="full_experiment_voting_with_info",
        app_sequence=['consent', 'instructions', 'practice_indy', 'practice_group', 'game_indy', 'game_group', 'payment'],
        num_demo_participants=10,
        condition="voting",
        information="optimal"
    )
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
