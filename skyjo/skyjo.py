"""Simulateur de Skyjo pour comparer des stratégies.

Règles (officielles) :
- 150 cartes : 5x -2, 10x -1, 15x 0, 10x chacune de 1 à 12.
- Chaque joueur a 12 cartes face cachée (3 lignes x 4 colonnes) et en retourne 2.
- À son tour : prendre la carte de la défausse (et l'échanger obligatoirement avec
  une de ses cartes), ou piocher : garder la carte (échange) ou la défausser et
  retourner une carte cachée.
- Une colonne de 3 cartes visibles identiques est retirée.
- Quand un joueur a tout retourné, chaque autre joueur joue un dernier tour.
- Si celui qui a fini n'a pas le score strictement le plus bas, son score
  (s'il est positif) est doublé.
- La partie s'arrête quand un joueur atteint 100 points ; le plus bas gagne.
"""
import random

DECK = [-2] * 5 + [-1] * 10 + [0] * 15 + [v for v in range(1, 13) for _ in range(10)]
COLS = [(c, c + 4, c + 8) for c in range(4)]
COL_OF = [i % 4 for i in range(12)]


class Board:
    __slots__ = ("cards", "visible", "removed")

    def __init__(self, cards):
        self.cards = cards
        self.visible = [False] * 12
        self.removed = [False] * 12

    def hidden(self):
        return [i for i in range(12) if not self.visible[i] and not self.removed[i]]

    def all_revealed(self):
        return all(self.visible[i] or self.removed[i] for i in range(12))

    def visible_score(self):
        return sum(self.cards[i] for i in range(12) if self.visible[i] and not self.removed[i])

    def score(self):
        return sum(self.cards[i] for i in range(12) if not self.removed[i])

    def check_columns(self, discard):
        for col in COLS:
            if all(self.visible[i] and not self.removed[i] for i in col):
                v = self.cards[col[0]]
                if all(self.cards[i] == v for i in col):
                    for i in col:
                        self.removed[i] = True
                    discard.extend([v, v, v])


class Game:
    def __init__(self, strategies, rng, verbose=False):
        self.strategies = strategies
        self.n = len(strategies)
        self.rng = rng

    # ---- cartes ----
    def draw(self):
        if not self.deck:
            top = self.discard.pop()
            self.deck = self.discard
            self.rng.shuffle(self.deck)
            self.discard = [top]
        return self.deck.pop()

    def unseen_mean(self, me):
        """Espérance d'une carte inconnue pour le joueur `me` (comptage de cartes)."""
        known = list(self.discard)
        for b in self.boards:
            known.extend(b.cards[i] for i in range(12) if b.visible[i] and not b.removed[i])
        total = sum(DECK) - sum(known)
        count = len(DECK) - len(known)
        return total / count if count else 5.0

    # ---- manche ----
    def play_round(self, first):
        deck = DECK[:]
        self.rng.shuffle(deck)
        self.deck = deck
        self.boards = [Board([self.deck.pop() for _ in range(12)]) for _ in range(self.n)]
        self.discard = [self.deck.pop()]
        for p, b in enumerate(self.boards):
            for i in self.strategies[p].initial_flips(self, p):
                b.visible[i] = True
        if first is None:
            first = max(range(self.n), key=lambda p: self.boards[p].visible_score())
        finisher = None
        p = first
        turns = 0
        while True:
            self.last_turn = finisher is not None
            self.strategies[p].play(self, p)
            b = self.boards[p]
            b.check_columns(self.discard)
            turns += 1
            if finisher is None and b.all_revealed():
                finisher = p
            p = (p + 1) % self.n
            if finisher is not None and p == finisher:
                break
            if turns > 2000:
                break
        for b in self.boards:
            for i in range(12):
                b.visible[i] = True
            b.check_columns(self.discard)
        scores = [b.score() for b in self.boards]
        if finisher is not None:
            s = scores[finisher]
            if s > 0 and any(scores[q] <= s for q in range(self.n) if q != finisher):
                scores[finisher] = 2 * s
        return scores, finisher

    def play(self):
        totals = [0] * self.n
        first = None
        rounds = 0
        while max(totals) < 100:
            scores, finisher = self.play_round(first)
            totals = [t + s for t, s in zip(totals, scores)]
            first = finisher
            rounds += 1
        return totals, rounds

    # ---- actions offertes aux stratégies ----
    def take_discard_and_swap(self, p, pos):
        card = self.discard.pop()
        self._swap(p, card, pos)

    def draw_card(self):
        return self.draw()

    def keep_drawn(self, p, card, pos):
        self._swap(p, card, pos)

    def reject_drawn_and_flip(self, p, card, pos):
        self.discard.append(card)
        self.boards[p].visible[pos] = True

    def _swap(self, p, card, pos):
        b = self.boards[p]
        old = b.cards[pos]
        b.cards[pos] = card
        b.visible[pos] = True
        self.discard.append(old)
