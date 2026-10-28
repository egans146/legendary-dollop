"""Stratégies de Skyjo, de la plus naïve à la plus élaborée."""
from skyjo import COLS, COL_OF

EV = 760 / 150  # espérance d'une carte inconnue (~5,07)


class Random:
    name = "Aléatoire"

    def initial_flips(self, g, p):
        return g.rng.sample(range(12), 2)

    def play(self, g, p):
        b = g.boards[p]
        slots = [i for i in range(12) if not b.removed[i]]
        hidden = b.hidden()
        if g.rng.random() < 0.5:
            g.take_discard_and_swap(p, g.rng.choice(slots))
            return
        card = g.draw_card()
        if hidden and g.rng.random() < 0.5:
            g.reject_drawn_and_flip(p, card, g.rng.choice(hidden))
        else:
            g.keep_drawn(p, card, g.rng.choice(slots))


class Threshold:
    """Stratégie « débutant » : garde toute carte <= seuil, la pose sur une carte
    cachée, sinon retourne une carte. Ignore les colonnes et la fin de manche."""

    def __init__(self, t=4):
        self.t = t
        self.name = f"Seuil simple (≤{t})"

    def initial_flips(self, g, p):
        return g.rng.sample(range(12), 2)

    def _place(self, g, p, card):
        b = g.boards[p]
        hidden = b.hidden()
        vis = [i for i in range(12) if b.visible[i] and not b.removed[i]]
        worst = max(vis, key=lambda i: b.cards[i]) if vis else None
        if worst is not None and b.cards[worst] > card and (not hidden or b.cards[worst] > EV):
            return worst
        return hidden[0] if hidden else worst

    def play(self, g, p):
        b = g.boards[p]
        top = g.discard[-1]
        if top <= self.t:
            g.take_discard_and_swap(p, self._place(g, p, top))
            return
        card = g.draw_card()
        hidden = b.hidden()
        if card <= self.t or not hidden:
            pos = self._place(g, p, card)
            if b.visible[pos] and b.cards[pos] <= card and hidden:
                g.reject_drawn_and_flip(p, card, hidden[0])
            elif b.visible[pos] and b.cards[pos] <= card:
                g.discard.append(card)
            else:
                g.keep_drawn(p, card, pos)
        else:
            g.reject_drawn_and_flip(p, card, hidden[0])


class Smart:
    """Stratégie à évaluation : pour chaque emplacement possible, calcule le gain
    espéré en points. Options :
      columns  – valorise les colonnes (paires, brelans retirés)
      endgame  – ne termine la manche que si l'on est (probablement) le plus bas
      counting – espérance des cartes cachées calculée sur les cartes non vues
      take     – gain minimal pour prendre la défausse
      keep     – gain minimal pour garder une carte piochée
      flip_bonus – valeur donnée au fait de retourner une carte (vitesse)
    """

    def __init__(self, name, columns=True, endgame=True, counting=True,
                 take=1.0, keep=0.0, flip_bonus=0.0, pair_bonus=2.0):
        self.name = name
        self.columns = columns
        self.endgame = endgame
        self.counting = counting
        self.take = take
        self.keep = keep
        self.flip_bonus = flip_bonus
        self.pair_bonus = pair_bonus

    def initial_flips(self, g, p):
        # Deux cartes dans la même colonne : chance de paire visible dès le début.
        if self.columns:
            c = g.rng.randrange(4)
            return [c, c + 4]
        return g.rng.sample(range(12), 2)

    # --- évaluation d'un plateau ---
    def _col_value(self, b, cards, visible, col, ev):
        idx = [i for i in col if not b.removed[i]]
        if not idx:
            return 0.0
        total = 0.0
        vis_vals = []
        for i in idx:
            if visible[i]:
                total += cards[i]
                vis_vals.append(cards[i])
            else:
                total += ev
        if not self.columns or len(idx) < 3:
            return total
        if len(vis_vals) == 3 and vis_vals[0] == vis_vals[1] == vis_vals[2]:
            return 0.0
        # Paire visible + une carte cachée/différente : potentiel de brelan.
        if len(vis_vals) >= 2:
            for v in set(vis_vals):
                if vis_vals.count(v) == 2 and v > 0:
                    if not self._last:
                        total -= min(self.pair_bonus, v)
        return total

    def _board_value(self, g, p, cards, visible, ev):
        b = g.boards[p]
        return sum(self._col_value(b, cards, visible, col, ev) for col in COLS)

    def _estimate(self, g, q, ev):
        b = g.boards[q]
        return sum(b.cards[i] if b.visible[i] else ev
                   for i in range(12) if not b.removed[i])

    def _gain(self, g, p, card, pos, ev, base):
        """Gain (positif = mieux) si on pose `card` en `pos`, None = retourner pos."""
        b = g.boards[p]
        cards = b.cards[:]
        visible = b.visible[:]
        was_hidden = not visible[pos]
        if card is None:  # simple retournement : valeur réelle inconnue
            gain = self.flip_bonus
            visible[pos] = True
            cards = None
        else:
            cards[pos] = card
            visible[pos] = True
            after = self._board_value(g, p, cards, visible, ev)
            gain = base - after
            if was_hidden:
                gain += self.flip_bonus
        if self.endgame and was_hidden and not g.last_turn:
            remaining = sum(1 for i in range(12) if not visible[i] and not b.removed[i])
            if remaining == 0:
                if card is None:
                    my = self._estimate(g, p, ev)
                else:
                    my = sum(cards[i] for i in range(12) if not b.removed[i])
                others = min(self._estimate(g, q, ev) for q in range(g.n) if q != p)
                if my >= others - 1 and my > 0:
                    gain -= my  # risque de score doublé
                else:
                    gain += 3.0  # on finit en tête : on coupe les autres
        return gain

    def _best(self, g, p, card, ev):
        b = g.boards[p]
        self._last = g.last_turn
        base = self._board_value(g, p, b.cards, b.visible, ev)
        best_pos, best_gain = None, -1e9
        for pos in range(12):
            if b.removed[pos]:
                continue
            gain = self._gain(g, p, card, pos, ev, base)
            if gain > best_gain:
                best_pos, best_gain = pos, gain
        return best_pos, best_gain

    def _best_flip(self, g, p, ev):
        b = g.boards[p]
        best_pos, best_gain = None, -1e9
        for pos in b.hidden():
            gain = self._gain(g, p, None, pos, ev, 0)
            # Retourner dans une colonne avec une paire visible : chance de brelan.
            if self.columns:
                vis = [b.cards[i] for i in COLS[COL_OF[pos]] if i != pos and b.visible[i]]
                if len(vis) == 2 and vis[0] == vis[1]:
                    gain += 0.5
                elif len(vis) == 1:
                    gain += 0.1
            if gain > best_gain:
                best_pos, best_gain = pos, gain
        return best_pos, best_gain

    def play(self, g, p):
        ev = g.unseen_mean(p) if self.counting else EV
        b = g.boards[p]
        top = g.discard[-1]
        pos, gain = self._best(g, p, top, ev)
        if gain >= self.take:
            g.take_discard_and_swap(p, pos)
            return
        card = g.draw_card()
        pos, gain = self._best(g, p, card, ev)
        hidden = b.hidden()
        if not hidden:
            if gain > 0:
                g.keep_drawn(p, card, pos)
            else:
                g.discard.append(card)
            return
        fpos, fgain = self._best_flip(g, p, ev)
        if gain >= self.keep and gain >= fgain:
            g.keep_drawn(p, card, pos)
        else:
            g.reject_drawn_and_flip(p, card, fpos)

