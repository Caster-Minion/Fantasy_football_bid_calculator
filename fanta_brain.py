import csv
import pulp

# Configurazione Ruoli (Modifica se giochi col Mantra o altro)
ROLES_CONFIG = {
    'P': {'total': 3, 'starters': 1},
    'D': {'total': 8, 'starters': 4},
    'C': {'total': 8, 'starters': 4},  # O 3 se usi trequartisti
    'A': {'total': 6, 'starters': 3}
}


class FantaBrain:
    def __init__(self, csv_path):
        self.db_players = []
        self._load_csv(csv_path)

    def _load_csv(self, path):
        """Carica il CSV fm_forecast"""
        print(f"Caricamento database da {path}...")
        with open(path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                try:
                    p = {
                        'id': row['Id'],  # ID univoco
                        'name': row['Nome'].strip().upper(),
                        'role': row['R'].strip().upper(),  # Ruolo Classic
                        'price_est': int(row['Qt.I']),  # Quotazione Iniziale
                        'fm': float(row['Fm'].replace(',', '.')),  # FM attuale
                        'fm_prev': float(row['Fm_Prevista'].replace(',', '.'))  # FM Prevista
                    }
                    self.db_players.append(p)
                except Exception as e:
                    # Salta righe malformate
                    continue
        print(f"Caricati {len(self.db_players)} giocatori nel database.")

    def get_player_by_name(self, name):
        """Cerca il giocatore nel DB per nome esatto"""
        if not name: return None
        for p in self.db_players:
            if p['name'] == name:
                return p
        return None

    def calcola_offerta_massima(self, my_team_names, taken_players_names, budget, player_in_auction_name):
        """
        my_team_names: lista di nomi dei miei giocatori
        taken_players_names: lista di nomi di giocatori presi dagli ALTRI
        budget: il mio budget residuo
        player_in_auction_name: il nome del giocatore attualmente all'asta
        """

        target_player = self.get_player_by_name(player_in_auction_name)
        if not target_player:
            return 0, "Giocatore non trovato nel database CSV."

        # --- FILTRO GIOCATORI ---
        # 1. Identifichiamo i miei giocatori (oggetti completi)
        my_team = [p for p in self.db_players if p['name'] in my_team_names]

        # 2. Identifichiamo tutti i giocatori presi (da me o altri) per rimuoverli dal pool
        all_taken_names = set(my_team_names + taken_players_names)

        # 3. Pool Disponibile: Tutto il DB meno quelli già presi
        #    ESCLUDENDO però il target_player (lo tratteremo a parte nelle simulazioni)
        pool = [p for p in self.db_players
                if p['name'] not in all_taken_names
                and p['id'] != target_player['id']]

        # --- ALGORITMO DI OTTIMIZZAZIONE (Semplificato per velocità) ---

        # Logica: 
        # Score_BASE = Risolvi squadra ottimale SENZA il giocatore target.
        # Score_WITH = Risolvi squadra ottimale CON il giocatore target (imponendo acquisto).
        # Se Score_WITH > Score_BASE, possiamo spendere.
        # Quanto? Aumentiamo il prezzo finché Score_WITH >= Score_BASE.

        print(f"Analisi per {target_player['name']} (Budget: {budget})...")

        # 1. Calcolo Baseline (Se non lo compro)
        base_score = self._solve_pulp(my_team, pool, budget)
        if base_score == -1:
            return 0, "Errore: Impossibile completare la rosa con il budget attuale."

        # 2. Iterazione Prezzo
        # Partiamo dal prezzo stimato (o 1) e saliamo
        current_bid = max(1, int(target_player['price_est']))
        max_bid = 0

        # Ottimizzazione: Step larghi poi fini
        step = 5
        while current_bid <= budget:
            # Provo a formare la squadra COMPRANDO il target a 'current_bid'
            # (Passo il target come 'forced_player')
            score = self._solve_pulp(my_team, pool, budget, forced_player=target_player, forced_price=current_bid)

            if score >= base_score:
                max_bid = current_bid
                current_bid += step
            else:
                # Se fallisce col passo 5, torniamo indietro e proviamo passo 1
                if step > 1:
                    current_bid -= step
                    step = 1
                    current_bid += 1
                else:
                    break  # Abbiamo trovato il limite

        return max_bid, f"Consigliato fino a {max_bid} (Est: {target_player['price_est']})"

    def _solve_pulp(self, current_team, pool, budget, forced_player=None, forced_price=0):
        """
        Risolve il problema dello zaino.
        Ritorna il Total Projected Score (o -1 se infeasible).
        """
        prob = pulp.LpProblem("Fanta_Opt", pulp.LpMaximize)

        candidates = pool + current_team
        if forced_player:
            candidates.append(forced_player)

        ids = [p['id'] for p in candidates]
        current_ids = [p['id'] for p in current_team]

        # Vars
        x = pulp.LpVariable.dicts("x", ids, cat='Binary')  # Preso in rosa
        y = pulp.LpVariable.dicts("y", ids, cat='Binary')  # Titolare

        # --- VINCOLI ---

        # 1. Quelli che ho già devo tenerli
        for pid in current_ids:
            prob += x[pid] == 1

        # 2. Se c'è un forced player, devo prenderlo
        if forced_player:
            prob += x[forced_player['id']] == 1

        # 3. Budget (solo sui nuovi acquisti)
        cost_expr = 0
        for p in pool:
            cost_expr += x[p['id']] * p['price_est']

        if forced_player:
            cost_expr += forced_price  # Prezzo esplicito per il target

        prob += cost_expr <= budget

        # 4. Composizione Rosa (Slot totali e titolari)
        for role, conf in ROLES_CONFIG.items():
            role_ids = [p['id'] for p in candidates if p['role'] == role]

            # Totale slot ruolo
            prob += pulp.lpSum([x[i] for i in role_ids]) == conf['total']

            # Titolari <= Totali
            for i in role_ids:
                prob += y[i] <= x[i]

            # Max Titolari
            prob += pulp.lpSum([y[i] for i in role_ids]) <= conf['starters']

        # --- OBIETTIVO ---
        # Massimizzare la somma delle FM Previste dei titolari
        # + un piccolo peso per la panchina (0.1) per avere riserve decenti
        obj = 0
        for p in candidates:
            pid = p['id']
            # FM prevista * (Titolare + 0.1 * (Rosa - Titolare))
            # Semplificato: 0.9*FM*y + 0.1*FM*x
            fm = p['fm_prev']
            obj += (0.9 * fm * y[pid]) + (0.1 * fm * x[pid])

        prob += obj

        # Risolvi silenziosamente
        prob.solve(pulp.PULP_CBC_CMD(msg=False))

        if prob.status == 1:
            return pulp.value(prob.objective)
        else:
            return -1