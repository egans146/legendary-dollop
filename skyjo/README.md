# Analyse des tactiques de Skyjo

Simulateur des règles officielles (`skyjo.py`), stratégies (`strategies.py`),
tournoi (`tournament.py`) et recherche de réglages (`sweep.py`).
Résultats bruts : `results.txt` (tournoi, 300 parties par duel, 1 200 parties à 4)
et `sweep_results.txt` (réglages).

```
python3 tournament.py 300   # ~3 min
python3 sweep.py 300
```

## Stratégies testées

| Stratégie | Idée |
|---|---|
| Aléatoire | référence plancher |
| Seuil simple (≤4) | garde toute carte ≤ 4, sinon retourne une carte |
| Glouton (sans colonnes) | pose chaque carte là où elle fait gagner le plus de points |
| Colonnes | + cherche les paires/brelans verticaux (colonne retirée) |
| Colonnes + fin maîtrisée | + ne retourne sa dernière carte que si l'on est sûr d'être le plus bas |
| Complète (+ comptage) | + estime les cartes cachées à partir des cartes déjà vues |
| Rush | + bonus pour retourner des cartes (finir la manche vite) |
| Lente | + malus pour retourner des cartes |
| **Optimisée** | lente + ne prend la défausse que si elle fait gagner ≥ 3 points |

## Résultats

| Stratégie | Score moyen / manche | Duels gagnés | Victoires à 4 (25 % = hasard) |
|---|---:|---:|---:|
| **Optimisée (lente + exigeante)** | **19,9** | **79,6 %** | **43,1 %** |
| Lente | 22,3 | 72,6 % | 31,4 % |
| Complète (+ comptage) | 24,2 | 60,0 % | 34,7 % |
| Colonnes + fin maîtrisée | 25,1 | 57,9 % | 31,2 % |
| Colonnes | 25,9 | 58,0 % | 28,9 % |
| Seuil simple (≤4) | 27,4 | 47,8 % | 25,6 % |
| Rush | 28,4 | 37,2 % | 17,4 % |
| Glouton (sans colonnes) | 29,1 | 36,9 % | 14,0 % |
| Aléatoire | 73,0 | 0 % | 0 % |

## Ce qui marche (par ordre d'importance)

1. **Ne pas se presser de retourner ses cartes.** C'est le facteur n°1.
   Une carte cachée vaut ~5 en moyenne, mais la retourner ne fait rien gagner
   et rapproche la fin de manche. Mieux vaut améliorer les cartes déjà visibles
   (remplacer un 9 par un 6) et laisser les adversaires terminer : celui qui
   finit sans être le plus bas voit son score **doublé**. Le « Rush » est
   la pire stratégie raisonnable.
2. **Être exigeant avec la défausse.** Ne la prendre que si elle fait gagner
   au moins ~3 points (une carte ≤ 2 sur une carte cachée, ou une carte qui
   remplace une carte visible plus haute d'au moins 3, ou qui complète une
   colonne). Sinon piocher : la pioche offre deux options (garder ou retourner)
   et peut sortir un -2/-1/0. Les réglages entre 2 et 5 points se valent.
3. **Jouer les colonnes.** Commencer par retourner 2 cartes de la même colonne,
   poser les cartes identiques dans une même colonne, viser les brelans de
   cartes hautes (trois 10 retirés = -30 points). Gain : ~+20 points de % de
   victoire en duel par rapport au glouton.
4. **Maîtriser la fin.** Ne retourner sa dernière carte que si son score est
   nettement le plus bas ; dans ce cas, finir vite pour piéger les autres.
5. **Compter les cartes** (espérance des cartes cachées selon ce qui est sorti) :
   petit gain supplémentaire (~+3 % de victoires à 4).

## La meilleure tactique, en résumé

> Commence avec deux cartes d'une même colonne. Ne prends la défausse que pour
> une très bonne affaire (≥ 3 points gagnés ou une colonne complétée). Sinon,
> pioche : garde la carte si elle remplace une carte visible plus forte, sinon
> défausse-la. Retourne des cartes cachées le moins possible. Laisse les autres
> finir la manche, et ne la termine toi-même que si tu es clairement en tête.

## Limites

- Les stratégies sont des heuristiques, pas une solution exacte du jeu.
- Les adversaires simulés ne s'adaptent pas : face à un humain qui joue lui
  aussi lentement, l'avantage de la lenteur diminue (les manches s'allongent et
  la pioche se recycle).
