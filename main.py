import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker

# -------------------------
# CONFIG
# -------------------------
NUM_PLAYERS = 100000
SIM_TIME = 20000
PLAYERS_PER_TICK = 8

TEAM_SIZE = 5
MATCH_SIZE = TEAM_SIZE * 2

BASE_SKILL = 1000
SKILL_STD = 200

SBMM_THRESHOLD = 100
EXPANSION_RATE = 5


# -------------------------
# PLAYER CLASS
# -------------------------
class Player:
    def __init__(self, skill, join_time):
        self.skill = skill
        self.join_time = join_time


# -------------------------
# HELPERS
# -------------------------
def generate_player(current_time):
    skill = random.gauss(BASE_SKILL, SKILL_STD)
    return Player(skill, current_time)


def team_skill(team):
    return sum(p.skill for p in team)


def calculate_balance(teamA, teamB):
    return abs(team_skill(teamA) - team_skill(teamB))


def split_teams(players):
    random.shuffle(players)
    return players[:TEAM_SIZE], players[TEAM_SIZE:]


# -------------------------
# MATCHMAKING
# -------------------------

# 🔴 No SBMM
def matchmaking_random(queue, current_time):
    matches = []
    while len(queue) >= MATCH_SIZE:
        players = random.sample(queue, MATCH_SIZE)
        for p in players:
            queue.remove(p)

        teamA, teamB = split_teams(players)

        matches.append((teamA, teamB, players))
    return matches


# 🟢 SBMM estricto
def matchmaking_strict(queue, current_time):
    matches = []
    queue.sort(key=lambda p: p.skill)

    i = 0
    while i + MATCH_SIZE <= len(queue):
        group = queue[i:i + MATCH_SIZE]

        if max(p.skill for p in group) - min(p.skill for p in group) <= SBMM_THRESHOLD:
            for p in group:
                queue.remove(p)

            teamA, teamB = split_teams(group)
            matches.append((teamA, teamB, group))
        else:
            i += 1

    return matches


# 🟡 SBMM dinámico (realista)
def matchmaking_dynamic(queue, current_time):
    matches = []
    queue.sort(key=lambda p: p.skill)

    i = 0
    while i + MATCH_SIZE <= len(queue):
        group = queue[i:i + MATCH_SIZE]

        max_wait = max(current_time - p.join_time for p in group)
        allowed_range = SBMM_THRESHOLD + max_wait * EXPANSION_RATE

        if max(p.skill for p in group) - min(p.skill for p in group) <= allowed_range:
            for p in group:
                queue.remove(p)

            teamA, teamB = split_teams(group)
            matches.append((teamA, teamB, group))
        else:
            i += 1

    return matches


# -------------------------
# SIMULATION
# -------------------------
def run_simulation(matchmaking_fn):
    queue = []
    wait_times = []
    skill_diffs = []

    for t in range(SIM_TIME):

        # llegan jugadores
        for _ in range(np.random.poisson(PLAYERS_PER_TICK)):
            queue.append(generate_player(t))

        # matchmaking
        matches = matchmaking_fn(queue, t)

        # procesar matches
        for teamA, teamB, players in matches:
            skills = [p.skill for p in players]
            skill_diff = max(skills) - min(skills)
            skill_diffs.append(skill_diff)

            avg_wait = sum(t - p.join_time for p in players) / len(players)
            wait_times.append(avg_wait)

    return skill_diffs, wait_times

def plot_distribution_curve(data, label, bins=50):
    counts, bin_edges = np.histogram(data, bins=bins, density=True)
    centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    plt.plot(centers, counts, label=label)

# -------------------------
# RUN
# -------------------------
print("Running simulations...")

s_random, w_random = run_simulation(matchmaking_random)
s_strict, w_strict = run_simulation(matchmaking_strict)
s_dynamic, w_dynamic = run_simulation(matchmaking_dynamic)


# -------------------------
# RESULTS
# -------------------------
def summarize(name, balances, waits):
    print(f"\n{name}")
    print(f"Avg Balance: {np.mean(balances):.2f}")
    print(f"Avg Wait: {np.mean(waits):.2f}")


summarize("No SBMM", s_random, w_random)
summarize("SBMM Strict", s_strict, w_strict)
summarize("SBMM Dynamic", s_dynamic, w_dynamic)


# -------------------------
# PLOTS
# -------------------------

# Scatter: Balance vs Wait

plt.figure()
plt.scatter(w_random, s_random, alpha=0.3, label="No SBMM")
plt.scatter(w_strict, s_strict, alpha=0.3, label="SBMM Strict")
plt.scatter(w_dynamic, s_dynamic, alpha=0.3, label="SBMM Dynamic")

plt.xscale("asinh")
plt.gca().xaxis.set_major_formatter(ticker.ScalarFormatter())
plt.xlabel("Wait Time")
plt.ylabel("Skill Difference")
plt.title("Balance vs Wait Time")
plt.legend()
plt.show()


# Boxplot Balance
plt.figure()
plt.boxplot(
    [s_random, s_strict, s_dynamic],
    labels=["No SBMM", "SBMM Strict", "SBMM Dynamic"]
)
plt.title("Skill Difference per Match")
plt.ylabel("Skill Range (max - min)")
plt.show()


# Boxplot Wait
plt.figure()
plt.boxplot(
    [w_random, w_strict, w_dynamic],
    labels=["No SBMM", "SBMM Strict", "SBMM Dynamic"]
)
plt.yscale("asinh")
plt.gca().yaxis.set_major_formatter(ticker.ScalarFormatter())
plt.title("Wait Time per Match")
plt.ylabel("Average Wait Time")
plt.show()

plt.figure()
plt.hist(s_random, alpha=0.5, label="No SBMM", bins=30)
plt.hist(s_strict, alpha=0.5, label="Strict", bins=30)
plt.hist(s_dynamic, alpha=0.5, label="Dynamic", bins=30)

plt.title("Skill Difference Distribution")
plt.xlabel("Skill Range")
plt.ylabel("Frequency")
plt.legend()
plt.show()

# plt.figure()
# plt.hist(w_random, alpha=0.5, label="No SBMM", bins=30)
# plt.hist(w_strict, alpha=0.5, label="Strict", bins=30)
# plt.hist(w_dynamic, alpha=0.5, label="Dynamic", bins=30)
#
# plt.yscale("asinh")
# plt.xscale("asinh")
# plt.gca().xaxis.set_major_formatter(ticker.ScalarFormatter())
# plt.gca().yaxis.set_major_formatter(ticker.ScalarFormatter())
# plt.title("Wait Time Distribution")
# plt.xlabel("Wait Time")
# plt.ylabel("Frequency")
# plt.legend()
# plt.show()

plt.figure()

plot_distribution_curve(s_random, "No SBMM")
plot_distribution_curve(s_strict, "SBMM Strict")
plot_distribution_curve(s_dynamic, "SBMM Dynamic")

plt.title("Match Count by Skill Gap")
plt.xlabel("Skill Gap (max - min)")
plt.ylabel("Density of Matches")
plt.legend()
plt.show()

plt.figure()

plot_distribution_curve(w_random, "No SBMM")
plot_distribution_curve(w_strict, "SBMM Strict")
plot_distribution_curve(w_dynamic, "SBMM Dynamic")

plt.xscale("asinh")
plt.gca().xaxis.set_major_formatter(ticker.ScalarFormatter())
plt.title("Match Count by Wait Time")
plt.xlabel("Wait Time")
plt.ylabel("Density of Matches")
plt.legend()
plt.show()