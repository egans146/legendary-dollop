"""Recherche des meilleurs réglages de la stratégie Smart (duels contre la référence)."""
import sys
from strategies import Smart
from tournament import duel

n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
ref = Smart("Référence")
rows = []
for fb in (-3.0, -2.0, -1.5, -1.0, -0.5, 0.0):
    for take in (0.0, 1.0, 2.0):
        for keep in (-1.0, 0.0, 1.0):
            s = Smart("x", flip_bonus=fb, take=take, keep=keep)
            (w, _), (pa, pb) = duel(s, ref, n, 7)
            rows.append((w / n, fb, take, keep, pa / n, pb / n))
            print(f"flip_bonus={fb:5.1f} take={take:3.1f} keep={keep:4.1f}  victoires {100*w/n:5.1f}%  pts {pa/n:5.1f} vs {pb/n:5.1f}", flush=True)
print("\nTop 5 :")
for r in sorted(rows, reverse=True)[:5]:
    print(f"  flip_bonus={r[1]} take={r[2]} keep={r[3]} -> {100*r[0]:.1f}%")
