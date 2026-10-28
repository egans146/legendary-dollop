"""Compare les stratégies de Skyjo par simulation.

Usage : python3 tournament.py [nombre_de_parties]
"""
import random
import sys
from itertools import combinations

from skyjo import Game
from strategies import Random, Smart, Threshold


def make_strategies():
    return [
        Random(),
        Threshold(4),
        Smart("Glouton (sans colonnes)", columns=False, endgame=False, counting=False),
        Smart("Colonnes", columns=True, endgame=False, counting=False),
        Smart("Colonnes + fin maîtrisée", columns=True, endgame=True, counting=False),
        Smart("Complète (+ comptage)", columns=True, endgame=True, counting=True),
        Smart("Rush (finir vite)", flip_bonus=2.0),
        Smart("Lente (évite de retourner)", flip_bonus=-1.5),
        Smart("Optimisée (lente + exigeante)", flip_bonus=-2.0, take=3.0, keep=0.0),
    ]


def duel(a, b, n, seed):
    """Parties à 2 joueurs, en alternant le premier siège."""
    rng = random.Random(seed)
    wins = [0, 0]
    pts = [0, 0]
    for k in range(n):
        order = [a, b] if k % 2 == 0 else [b, a]
        totals, _ = Game(order, rng).play()
        if k % 2:
            totals = totals[::-1]
        pts[0] += totals[0]
        pts[1] += totals[1]
        if totals[0] < totals[1]:
            wins[0] += 1
        elif totals[1] < totals[0]:
            wins[1] += 1
        else:
            wins[0] += 0.5
            wins[1] += 0.5
    return wins, pts


def round_stats(strat, n, seed):
    """Score moyen par manche d'une stratégie jouant contre des copies d'elle-même (4 joueurs)."""
    rng = random.Random(seed)
    total = rounds = 0
    for _ in range(n):
        g = Game([strat] * 4, rng)
        scores, _ = g.play_round(None)
        total += sum(scores)
        rounds += 4
    return total / rounds


def free_for_all(strats, n, seed):
    """Parties à 4 joueurs, sièges tirés au hasard."""
    rng = random.Random(seed)
    wins = {s.name: 0 for s in strats}
    games = {s.name: 0 for s in strats}
    for _ in range(n):
        table = rng.sample(strats, 4)
        totals, _ = Game(table, rng).play()
        best = min(totals)
        winners = [s for s, t in zip(table, totals) if t == best]
        for s in table:
            games[s.name] += 1
        for s in winners:
            wins[s.name] += 1 / len(winners)
    return {k: wins[k] / games[k] for k in wins}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    strats = make_strategies()

    print("== Score moyen par manche (4 joueurs, même stratégie) ==")
    for s in strats:
        print(f"  {s.name:32s} {round_stats(s, n, 1):6.1f}")

    print(f"\n== Duels (2 joueurs, {n} parties par paire) : % de victoires ==")
    score = {s.name: [0, 0] for s in strats}
    for a, b in combinations(strats, 2):
        (wa, wb), _ = duel(a, b, n, 2)
        score[a.name][0] += wa; score[a.name][1] += n
        score[b.name][0] += wb; score[b.name][1] += n
        print(f"  {a.name:32s} vs {b.name:32s} {100 * wa / n:5.1f}%")
    print("\n  Classement duels :")
    for name, (w, t) in sorted(score.items(), key=lambda kv: -kv[1][0] / kv[1][1]):
        print(f"    {name:32s} {100 * w / t:5.1f}%")

    print(f"\n== Mêlée à 4 joueurs ({n * 4} parties) : % de victoires (25% = hasard) ==")
    res = free_for_all(strats, n * 4, 3)
    for name, r in sorted(res.items(), key=lambda kv: -kv[1]):
        print(f"    {name:32s} {100 * r:5.1f}%")


if __name__ == "__main__":
    main()
