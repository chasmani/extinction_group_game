import numpy as np

def expected_value_strategy(n_risky, group_balance = 0, n_rounds=100, p_survive=0.95, e_risky=5, e_safe = 0.5):

    return p_survive**n_risky * (group_balance + e_risky * n_risky + e_safe * (n_rounds - n_risky))

def get_optimal_n_riskys(total_rounds_left, group_balance=0):

    n_riskys = list(range(total_rounds_left))
    expected_values = [expected_value_strategy(n_risky, group_balance=group_balance, n_rounds=total_rounds_left) for n_risky in n_riskys]

    # Get max n_riskys
    optimal_n_risky = n_riskys[np.argmax(expected_values)]

        # Optimal n_risky if integer or a fraction
    if optimal_n_risky % 5 == 0:
        optimal_n_risky_per_player = optimal_n_risky // 5
    else:
        optimal_n_risky_per_player = "{} to {}".format(optimal_n_risky // 5, int(optimal_n_risky//5 + 1))

    return optimal_n_risky, optimal_n_risky_per_player

