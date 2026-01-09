import pandas as pd
import numpy as np
import os
import re
import glob




#NOTA QUI VOTO E VOTO SECCO NON FANTAVOTO
# --- STEP 1: CARICAMENTO PARTITE (Cartella 'partite_20_25') ---

cartella_partite = 'partite_20_25'
lista_dfs_partite = []
cols_numeriche = ['Voto', 'Gf', 'Gs', 'Rs', 'Rf', 'Au', 'Amm', 'Esp', 'Ass']

print("--- INIZIO ELABORAZIONE PARTITE ---")

if os.path.exists(cartella_partite):
    for nome_file in os.listdir(cartella_partite):
        try:
            if nome_file.endswith(".xlsx") or nome_file.endswith(".xls"):
                percorso_completo = os.path.join(cartella_partite, nome_file)

                # Lettura file
                df = pd.read_excel(percorso_completo, skiprows=5)

                # --- Estrazione Stagione ---
                # Regex: cerca "20_21" o "20-21"
                match_anno = re.search(r'(\d{2}[_-]\d{2})', nome_file)
                if match_anno:
                    # Normalizziamo tutto con underscore (es. "20-21" diventa "20_21")
                    stagione = match_anno.group(1).replace("-", "_")
                else:
                    stagione = "ND"

                # --- Estrazione Giornata ---
                match_giornata = re.search(r'(?:Giornata|G)[_.\s]*(\d+)', nome_file, re.IGNORECASE)
                giornata = int(match_giornata.group(1)) if match_giornata else 0

                # --- Pulizia ---
                df_clean = df[df['Ruolo'].notna()].copy()
                df_clean = df_clean[df_clean['Cod.'] != 'Cod.'].reset_index(drop=True)

                # Aggiunta colonne chiave
                df_clean['Stagione'] = stagione
                df_clean['Giornata'] = giornata

                # Conversione colonne numeriche
                for col in cols_numeriche:
                    if col in df_clean.columns:
                        if df_clean[col].dtype == 'object':
                            df_clean[col] = df_clean[col].astype(str).str.replace(',', '.')
                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

                # *** IMPORTANTE: Conversione Cod. a Intero ***
                if 'Cod.' in df_clean.columns:
                    df_clean['Cod.'] = pd.to_numeric(df_clean['Cod.'], errors='coerce').fillna(0).astype(int)

                # Selezione colonne finali
                colonne_base = ['Stagione', 'Giornata', 'Squadra', 'Cod.', 'Ruolo', 'Nome']
                cols_finali = [c for c in colonne_base + cols_numeriche if c in df_clean.columns]
                df_clean = df_clean[cols_finali]

                lista_dfs_partite.append(df_clean)

        except Exception as e:
            print(f"Errore nel file {nome_file}: {e}")
else:
    print(f"Errore: La cartella '{cartella_partite}' non esiste.")

# Creazione DataFrame Unico Partite
if lista_dfs_partite:
    df_totale_partite = pd.concat(lista_dfs_partite, ignore_index=True)
    print(f"Totale righe partite caricate: {len(df_totale_partite)}")
else:
    df_totale_partite = pd.DataFrame()
    print("Nessuna partita caricata.")

print(df_totale_partite)




# --- STEP 2: CARICAMENTO RUOLI MANTRA (Cartella 'statistiche') ---

print("\n--- INIZIO ELABORAZIONE RUOLI ---")

path_stat = os.path.join("statistiche", "*.xlsx")
files_stat = glob.glob(path_stat)
lista_ruoli = []

for file in files_stat:
    try:
        # --- 1. ESTRAZIONE STAGIONE ---
        stagione = file.split('_')[3][-2:] + "_" + file.split('_')[4].replace(".xlsx", "")

        # --- 2. LETTURA FILE ---
        df_temp = pd.read_excel(file, skiprows=1, header=0)
        df_temp['Stagione'] = stagione

        # --- 3. SELEZIONE E RINOMINA ---
        if 'Id' in df_temp.columns and 'Rm' in df_temp.columns:

            # Prepariamo la lista delle colonne da estrarre
            colonne_da_estrarre = ['Id', 'Rm', 'Stagione']

            # AGGIUNTA RICHIESTA: Se c'è la colonna 'Squadra', la prendiamo
            if 'Squadra' in df_temp.columns:
                colonne_da_estrarre.append('Squadra')

            # Selezioniamo le colonne
            df_clean = df_temp[colonne_da_estrarre].copy()

            # Dizionario per rinominare le colonne
            rename_map = {'Id': 'Cod.'}


            # Applichiamo la rinomina
            df_clean = df_clean.rename(columns=rename_map)

            # Conversione a Intero (essenziale per il merge)
            df_clean['Cod.'] = pd.to_numeric(df_clean['Cod.'], errors='coerce').fillna(0).astype(int)

            lista_ruoli.append(df_clean)
        else:
            print(f"Attenzione: Colonne 'Id' o 'Rm' mancanti nel file: {file}")

    except IndexError:
        print(f"Errore formato nome file: {file}. Impossibile estrarre stagione.")
    except Exception as e:
        print(f"Errore generico leggendo {file}: {e}")

# --- 4. CREAZIONE DATAFRAME UNICO RUOLI ---
if lista_ruoli:
    df_ruoli = pd.concat(lista_ruoli, ignore_index=True)

    # Rimuoviamo duplicati (stesso giocatore stessa stagione)
    df_ruoli = df_ruoli.drop_duplicates(subset=['Cod.', 'Stagione'])

    print(f"Database ruoli creato correttamente.")
    print(f"Totale giocatori unici per stagione: {len(df_ruoli)}")

    # Check visuale
    if 'Squadra_Stat' in df_ruoli.columns:
        print("Colonna 'Squadra' importata correttamente.")
else:
    df_ruoli = pd.DataFrame()
    print("Nessun ruolo caricato.")

print(df_ruoli.head())

# --- STEP 3: MERGE FINALE ---

print("\n--- ESECUZIONE MERGE ---")

if not df_totale_partite.empty and not df_ruoli.empty:

    # Merge Left
    df_completo = pd.merge(
        df_totale_partite,
        df_ruoli,
        on=['Cod.', 'Stagione'],
        how='left'
    )

    print("Merge completato con successo!")
    print(df_completo.head())

    df_completo.dropna()
    # Se vuoi vedere se ci sono differenze tra la squadra del match e quella delle statistiche:
    if 'Squadra_Stat' in df_completo.columns:
        print("\nEsempio confronto Squadra Match vs Squadra Statistiche:")
        print(df_completo[['Nome', 'Stagione', 'Squadra', 'Squadra_Stat']].head())

    # Controllo errori
    mancanti = df_completo['Rm'].isna().sum()
    print(f"Righe senza ruolo Mantra associato: {mancanti}")

else:
    print("Impossibile fare il merge: uno dei due DataFrame è vuoto.")


df_completo = df_completo.dropna(subset=['Voto'])








########################################################################
# CREAZIONE DEL GRAFO DEI RUOLI MANTRA E CORRELAZIONI DELLE PERFORMORMANCE
########################################################################


import seaborn as sns
import matplotlib.pyplot as plt

# --- PREPARAZIONE DATI ---
df_completo['Voto_Norm'] = df_completo['Voto'] - 6





# 1. Preparazione e 'Esplosione' dei ruoli (Come prima)
df_mantra_split = df_completo.dropna(subset=['Rm', 'Voto']).copy()
df_mantra_split['Rm_Singolo'] = df_mantra_split['Rm'].astype(str).str.split(';')
df_mantra_split = df_mantra_split.explode('Rm_Singolo')
df_mantra_split['Rm_Singolo'] = df_mantra_split['Rm_Singolo'].str.strip()

# Definiamo l'ordine tattico
ruoli_mantra = ['Por', 'Dd', 'Ds', 'Dc', 'E', 'M', 'C', 'W', 'T', 'A', 'Pc']
# Filtriamo solo i ruoli validi
df_mantra_split = df_mantra_split[df_mantra_split['Rm_Singolo'].isin(ruoli_mantra)]

# 2. Inizializzazione Matrice Vuota
# Creiamo un DataFrame vuoto 11x11
matrix_corr = pd.DataFrame(index=ruoli_mantra, columns=ruoli_mantra, dtype=float)

print("Calcolo delle correlazioni coppia per coppia in corso...")

# 3. Calcolo Loop (Coppia per Coppia)
for r1 in ruoli_mantra:
    for r2 in ruoli_mantra:
        if r1 == r2:
            matrix_corr.loc[r1, r2] = 1.0
            continue

        # Prendiamo i subset per i due ruoli
        # Ci servono: Stagione, Giornata, Squadra (chiave partita), Cod. (per controllo), Voto_Norm
        sub1 = df_mantra_split[df_mantra_split['Rm_Singolo'] == r1][
            ['Stagione', 'Giornata', 'Squadra', 'Cod.', 'Voto_Norm']]
        sub2 = df_mantra_split[df_mantra_split['Rm_Singolo'] == r2][
            ['Stagione', 'Giornata', 'Squadra', 'Cod.', 'Voto_Norm']]

        # Facciamo un MERGE sulla partita
        # Questo crea tutte le combinazioni possibili tra i giocatori del ruolo 1 e del ruolo 2 nella stessa squadra
        merged = pd.merge(
            sub1,
            sub2,
            on=['Stagione', 'Giornata', 'Squadra'],
            suffixes=('_1', '_2')
        )

        # *** IL PUNTO CRUCIALE ***
        # Rimuoviamo le righe dove il Codice Giocatore è lo stesso
        merged_clean = merged[merged['Cod._1'] != merged['Cod._2']]

        if len(merged_clean) < 50:  # Se abbiamo troppi pochi dati per la correlazione, saltiamo
            matrix_corr.loc[r1, r2] = float('nan')
            continue

        # Ora dobbiamo raggruppare per partita.
        # Esempio: Se ci sono 2 Dc e 1 Dd diversi tra loro, il merge crea 2 righe.
        # Dobbiamo mediare i voti per quella singola partita/squadra dopo aver pulito i self-match.
        stats_match = merged_clean.groupby(['Stagione', 'Giornata', 'Squadra'])[['Voto_Norm_1', 'Voto_Norm_2']].mean()

        # Calcolo correlazione
        corr = stats_match['Voto_Norm_1'].corr(stats_match['Voto_Norm_2'])
        matrix_corr.loc[r1, r2] = corr

print("Calcolo completato.")

# 4. Grafico Heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(
    matrix_corr,
    annot=True,
    fmt=".2f",
    cmap='coolwarm',
    center=0,
    linewidths=.5,
    square=True,
    cbar_kws={"shrink": .8}
)

plt.title('Correlazione Voti Intra-Squadra (NO SELF-CORRELATION)')
plt.show()





print("--- ANALISI 1: CORRELAZIONI RUOLI MANTRA (INTRA-SQUADRA) ---")

# 1. Creazione Pivot Table MANTRA
# L'indice ora include 'Squadra': raggruppiamo per singola prestazione di squadra
df_pivot_mantra = df_completo.pivot_table(
    index=['Stagione', 'Giornata', 'Squadra'],
    columns='Rm',
    values='Voto_Norm',
    aggfunc='mean' # Se ci sono 2 'Dc' nella stessa squadra, fa la media dei loro voti
)

print("Esempio dati raggruppati (Mantra):")
print(df_pivot_mantra.head())

# 2. Calcolo Correlazione
corr_mantra = df_pivot_mantra.corr()

# 3. Grafico Heatmap Mantra
plt.figure(figsize=(12, 10))
sns.heatmap(
    corr_mantra,
    annot=True,
    fmt=".2f",
    cmap='coolwarm',
    center=0,
    linewidths=.5,
    square=True
)
plt.title('Correlazione Voti (vs Sufficienza) per Ruolo MANTRA nella STESSA SQUADRA')
plt.show()



print("\n--- ANALISI 2: CORRELAZIONI RUOLI CLASSIC (INTRA-SQUADRA) ---")

# 1. Creazione Pivot Table CLASSIC
df_pivot_classic = df_completo.pivot_table(
    index=['Stagione', 'Giornata', 'Squadra'],
    columns='Ruolo',
    values='Voto_Norm',
    aggfunc='mean'
)

print("Esempio dati raggruppati (Classic):")
print(df_pivot_classic.head())

# 2. Calcolo Correlazione
corr_classic = df_pivot_classic.corr()

# 3. Grafico Heatmap Classic
plt.figure(figsize=(10, 8))
sns.heatmap(
    corr_classic,
    annot=True,
    fmt=".2f",
    cmap='coolwarm',
    center=0,
    linewidths=.5,
    square=True
)
plt.title('Correlazione Voti (vs Sufficienza) per Ruolo CLASSIC nella STESSA SQUADRA')
plt.show()


## Check

# Lista dei ruoli esatti che stai cercando
target_roles = ['Dc;Dd']

# Filtro del DataFrame
entries_trovate = df_completo[df_completo['Rm'].isin(target_roles)]

# Output dei risultati

print(f"Totale righe con ruoli mantra richiesti trovate: {len(entries_trovate)}")

if not entries_trovate.empty:
    # Mostriamo solo le colonne più utili per leggere il risultato
    cols_view = ['Stagione', 'Giornata', 'Squadra', 'Nome', 'Rm', 'Voto']

    print("\nEcco le prime 20 occorrenze:")
    print(entries_trovate[cols_view].head(2000))

    # Se vuoi vedere l'elenco UNICO dei giocatori trovati (senza ripetizioni delle giornate)
    print("\n--- Elenco Giocatori Unici Trovati ---")
    giocatori_unici = entries_trovate[['Nome', 'Squadra', 'Rm', 'Stagione']].drop_duplicates()
    print(giocatori_unici)
else:
    print("Nessuna entry trovata con questi ruoli esatti.")








print("\n--- ANALISI 3: 'MIGLIOR COMPAGNO' QUANDO SI SEGNA ---")
# Obiettivo: Per ogni goal, chi ha il voto più alto ESCLUSO il marcatore?

# 1. Filtriamo solo le righe dove qualcuno ha segnato
df_marcatori = df_completo[df_completo['Gf'] > 0].copy()

# Lista per accumulare i ruoli dei migliori compagni
ruoli_best_teammate = []

print(f"Analisi di {df_marcatori['Gf'].sum():.0f} eventi goal totali...")

# 2. Iteriamo su ogni marcatore (ogni riga è un giocatore che ha segnato in una partita)
for idx, row in df_marcatori.iterrows():

    stagione = row['Stagione']
    giornata = row['Giornata']
    squadra = row['Squadra']
    codice_marcatore = row['Cod.']
    numero_goal = int(row['Gf'])  # Se ha fatto doppietta, il peso vale doppio

    # 3. Troviamo i compagni di quella specifica partita
    # Filtri: Stessa stagione, giornata, squadra, MA codice diverso dal marcatore
    compagni = df_completo[
        (df_completo['Stagione'] == stagione) &
        (df_completo['Giornata'] == giornata) &
        (df_completo['Squadra'] == squadra) &
        (df_completo['Cod.'] != codice_marcatore) &
        (df_completo['Rm'].notna())  # Assicuriamoci che abbiano un ruolo
        ]

    if compagni.empty:
        continue

    # 4. Troviamo il Voto Massimo tra i compagni
    max_voto = compagni['Voto'].max()

    # 5. Chi ha preso questo voto massimo? (Potrebbero essere più di uno a pari merito)
    top_performers = compagni[compagni['Voto'] == max_voto]

    # 6. Estraiamo i ruoli e aggiungiamoli alla lista
    # Ripetiamo l'operazione per il numero di goal segnati dal marcatore originale
    # (Se Lukaku fa 2 goal, cerchiamo il miglior compagno per il 1° goal e per il 2° goal)
    for _ in range(numero_goal):
        for _, top_p in top_performers.iterrows():
            # Gestione doppi ruoli (es. "W;T"): contiamo entrambi perché quel giocatore
            # avrebbe garantito il voto alto in entrambi gli slot.
            ruoli_grezzi = str(top_p['Rm']).split(';')
            for r in ruoli_grezzi:
                r_clean = r.strip()
                if r_clean in ruoli_mantra:  # Usiamo la lista ruoli definita prima
                    ruoli_best_teammate.append(r_clean)




# --- VISUALIZZAZIONE RISULTATI ---

from collections import Counter

# Contiamo le occorrenze
conteggio_ruoli = Counter(ruoli_best_teammate)

# Creiamo un DataFrame per il grafico
df_best_mate = pd.DataFrame.from_dict(conteggio_ruoli, orient='index', columns=['Conteggio'])
df_best_mate = df_best_mate.sort_values(by='Conteggio', ascending=False)

# Calcoliamo la percentuale sul totale degli eventi
totale_eventi = df_best_mate['Conteggio'].sum()
df_best_mate['Percentuale'] = (df_best_mate['Conteggio'] / totale_eventi) * 100

print("\nClassifica Ruoli con Voto più alto quando un compagno segna:")
print(df_best_mate)

# Grafico a Barre
plt.figure(figsize=(12, 6))
sns.barplot(x=df_best_mate.index, y=df_best_mate['Percentuale'], palette='viridis')

plt.title('Ruolo Mantra con Voto più alto (escluso il marcatore) per ogni Goal segnato')
plt.ylabel('% di volte in cui il ruolo è stato il migliore in campo (tra i non marcatori)')
plt.xlabel('Ruolo Mantra')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Aggiungiamo le etichette sopra le barre
for i, v in enumerate(df_best_mate['Percentuale']):
    plt.text(i, v + 0.5, f"{v:.1f}%", ha='center', fontweight='bold')

plt.show()








import matplotlib.pyplot as plt
import seaborn as sns

print("\n--- ANALISI COMBINATA: GOAL E ASSIST PER RUOLO (NORMALIZZATI) ---")

# 1. PREPARAZIONE DATI
# Creiamo un dataset ridotto ed esplodiamo i ruoli multipli
df_bonus = df_completo[['Rm', 'Gf', 'Ass']].dropna().copy()

# Gestione multiruolo (es. "W;A" -> conta sia come W che come A)
df_bonus['Rm_Singolo'] = df_bonus['Rm'].astype(str).str.split(';')
df_bonus = df_bonus.explode('Rm_Singolo')
df_bonus['Rm_Singolo'] = df_bonus['Rm_Singolo'].str.strip()

# Filtriamo solo i ruoli Mantra ufficiali
ruoli_mantra_validi = ['Por', 'Dd', 'Ds', 'Dc', 'E', 'M', 'C', 'W', 'T', 'A', 'Pc']
df_bonus = df_bonus[df_bonus['Rm_Singolo'].isin(ruoli_mantra_validi)]

# 2. CALCOLO MEDICHE
# Calcoliamo la media (valore atteso per partita) di Goal e Assist
stats_ruoli = df_bonus.groupby('Rm_Singolo')[['Gf', 'Ass']].mean()
stats_ruoli.columns = ['Media_Goal', 'Media_Assist']

# Aggiungiamo il conteggio per info
stats_ruoli['Presenze'] = df_bonus.groupby('Rm_Singolo')['Gf'].count()

# Ordiniamo per una metrica combinata (Fantasy Value puramente offensivo: Goal*3 + Assist*1)
# Questo aiuta a ordinare la tabella in modo sensato per il fantacalcio
stats_ruoli['Fanta_Score_Offensivo'] = (stats_ruoli['Media_Goal'] * 3) + stats_ruoli['Media_Assist']
stats_ruoli = stats_ruoli.sort_values(by='Fanta_Score_Offensivo', ascending=False)

print("Statistiche Medie per Partita (Goal e Assist):")
print(stats_ruoli[['Media_Goal', 'Media_Assist', 'Presenze']].round(3))


# --- VISUALIZZAZIONE 1: GRAFICO A BARRE AFFIANCATE ---
# Resettiamo l'indice per usare Seaborn
df_plot = stats_ruoli.reset_index().melt(id_vars='Rm_Singolo', value_vars=['Media_Goal', 'Media_Assist'],
                                         var_name='Tipo_Bonus', value_name='Media_Partita')

plt.figure(figsize=(14, 7))
sns.barplot(data=df_plot, x='Rm_Singolo', y='Media_Partita', hue='Tipo_Bonus', palette={'Media_Goal': '#d62728', 'Media_Assist': '#1f77b4'})

plt.title('Confronto Goal vs Assist per Ruolo (Media a Partita)')
plt.ylabel('Media per Partita')
plt.xlabel('Ruolo Mantra')
plt.legend(title='Bonus')
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.show()


# --- VISUALIZZAZIONE 2: SCATTER PLOT (MAPPA DEI RUOLI) ---
# Questo grafico è il più utile per capire le categorie di giocatori
plt.figure(figsize=(10, 8))

# Scatter plot
sns.scatterplot(data=stats_ruoli, x='Media_Assist', y='Media_Goal', s=200, color='purple', alpha=0.7)

# Etichette per ogni punto
for ruolo in stats_ruoli.index:
    x_pos = stats_ruoli.loc[ruolo, 'Media_Assist']
    y_pos = stats_ruoli.loc[ruolo, 'Media_Goal']
    # Spostiamo leggermente l'etichetta per non sovrapporla al punto
    plt.text(x_pos + 0.001, y_pos + 0.005, ruolo, fontsize=12, fontweight='bold')

# Linee medie per creare quadranti
avg_goal_all = df_bonus['Gf'].mean()
avg_ass_all = df_bonus['Ass'].mean()
plt.axhline(y=avg_goal_all, color='red', linestyle='--', alpha=0.3, label='Media Goal Generale')
plt.axvline(x=avg_ass_all, color='blue', linestyle='--', alpha=0.3, label='Media Assist Generale')

plt.title('Mappa dei Ruoli: Finalizzatori vs Rifinitori')
plt.xlabel('Media ASSIST a partita (Creatività)')
plt.ylabel('Media GOAL a partita (Finalizzazione)')
plt.grid(True, linestyle='--', alpha=0.3)

plt.show()

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

print("\n--- ANALISI 6: COMBINAZIONI REALI DI RUOLI (Raw Combinations) ---")

# 1. PREPARAZIONE DATI
# Prendiamo i dati grezzi senza "esplodere" la colonna Rm
df_combo = df_completo[['Rm', 'Gf', 'Ass']].dropna().copy()

# Pulizia base: rimuoviamo spazi vuoti o nulli
df_combo = df_combo[df_combo['Rm'] != '']

# 2. AGGREGAZIONE
# Calcoliamo media Goal, media Assist e numero di Presenze per ogni combinazione UNICA
stats_combo = df_combo.groupby('Rm').agg(
    Media_Goal=('Gf', 'mean'),
    Media_Assist=('Ass', 'mean'),
    Presenze=('Gf', 'count')
)

# 3. FILTRO E ORDINAMENTO
# Filtriamo combinazioni con poche presenze per pulire il grafico da outliers statistici
# (Adatta questo numero in base alla grandezza del tuo database, 50 è un buon numero per più stagioni)
min_presenze = 50
stats_combo_filtered = stats_combo[stats_combo['Presenze'] > min_presenze].copy()

# Creiamo un punteggio per ordinare il grafico (Goal*3 + Assist*1)
stats_combo_filtered['Score_Offensivo'] = (stats_combo_filtered['Media_Goal'] * 3) + stats_combo_filtered[
    'Media_Assist']
stats_combo_filtered = stats_combo_filtered.sort_values(by='Score_Offensivo', ascending=False)

print(f"Mostrando le combinazioni con almeno {min_presenze} presenze totali.")
print(stats_combo_filtered[['Media_Goal', 'Media_Assist', 'Presenze']].head(10))

# --- VISUALIZZAZIONE 1: GRAFICO A BARRE (GOAL vs ASSIST) ---

# Riorganizziamo per il barplot
df_plot_combo = stats_combo_filtered.reset_index().melt(
    id_vars='Rm',
    value_vars=['Media_Goal', 'Media_Assist'],
    var_name='Tipo_Bonus',
    value_name='Media_Partita'
)

plt.figure(figsize=(16, 8))
sns.barplot(
    data=df_plot_combo,
    x='Rm',
    y='Media_Partita',
    hue='Tipo_Bonus',
    palette={'Media_Goal': '#d62728', 'Media_Assist': '#1f77b4'}
)

plt.title(f'Performance per COMBINAZIONE DI RUOLO (Min. {min_presenze} presenze)')
plt.ylabel('Media per Partita')
plt.xlabel('Combinazione Mantra')
plt.xticks(rotation=45, ha='right')  # Ruotiamo le etichette perché le combinazioni sono lunghe
plt.legend(title='Bonus')
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()

# --- VISUALIZZAZIONE 2: SCATTER PLOT (MAPPA DELLE COMBINAZIONI) ---

plt.figure(figsize=(12, 10))

# Scatter plot
sns.scatterplot(
    data=stats_combo_filtered,
    x='Media_Assist',
    y='Media_Goal',
    size='Presenze',  # La grandezza del punto indica quanto è comune quel ruolo
    sizes=(50, 400),
    hue='Score_Offensivo',  # Il colore indica la pericolosità totale
    palette='viridis',
    legend=False
)

# Etichette
for rm in stats_combo_filtered.index:
    x_pos = stats_combo_filtered.loc[rm, 'Media_Assist']
    y_pos = stats_combo_filtered.loc[rm, 'Media_Goal']

    # Mettiamo il testo leggermente sfalsato
    plt.text(x_pos + 0.0005, y_pos + 0.002, rm, fontsize=10, fontweight='bold', alpha=0.9)

# Linee medie di riferimento
avg_goal = df_combo['Gf'].mean()
avg_ass = df_combo['Ass'].mean()
plt.axhline(y=avg_goal, color='red', linestyle='--', alpha=0.2, label='Media Goal Generale')
plt.axvline(x=avg_ass, color='blue', linestyle='--', alpha=0.2, label='Media Assist Generale')

plt.title('Mappa delle Combinazioni: Efficacia Reale in Campo')
plt.xlabel('Media ASSIST a partita')
plt.ylabel('Media GOAL a partita')
plt.grid(True, linestyle='--', alpha=0.3)

plt.show()

print("\n--- ANALISI 7: GOAL E ASSIST PER RUOLO DIVISI PER TIER ---")

# --- 1. DEFINIZIONE DEI TIER ---
tiers_dict = {
    'Top': ['Inter', 'Juventus', 'Milan', 'Napoli', 'Roma', 'Atalanta'],
    'Medie': ['Torino', 'Bologna', 'Sassuolo', 'Udinese', 'Sampdoria', 'Genoa', 'Lazio', 'Verona', 'Fiorentina',
              'Como'],
    'Piccole': ['Empoli', 'Cagliari', 'Salernitana', 'Lecce', 'Spezia', 'Venezia', 'Cremonese',
                'Frosinone', 'Benevento', 'SPAL', 'Crotone', 'Parma', 'Brescia', 'Pescara', 'Carpi', 'Chievo', 'Monza']
}

# Invertiamo il dizionario per mappare: Squadra -> Tier
squadra_to_tier = {}
for tier, squadre in tiers_dict.items():
    for sq in squadre:
        squadra_to_tier[sq] = tier

# --- 2. PREPARAZIONE DATI ---
# Copiamo il dataframe completo
df_tier = df_completo[['Squadra', 'Rm', 'Gf', 'Ass']].dropna().copy()

# Mappiamo il Tier
df_tier['Fascia'] = df_tier['Squadra'].map(squadra_to_tier)

# Rimuoviamo squadre che non sono nel dizionario (opzionale, per evitare errori su squadre mancanti)
df_tier = df_tier.dropna(subset=['Fascia'])

# Gestione multiruolo (Esplosione)
df_tier['Rm_Singolo'] = df_tier['Rm'].astype(str).str.split(';')
df_tier = df_tier.explode('Rm_Singolo')
df_tier['Rm_Singolo'] = df_tier['Rm_Singolo'].str.strip()

# Ordine tattico per il grafico
ordine_ruoli = ['Por', 'Dd', 'Ds', 'Dc', 'E', 'M', 'C', 'W', 'T', 'A', 'Pc']
df_tier = df_tier[df_tier['Rm_Singolo'].isin(ordine_ruoli)]

# --- 3. AGGREGAZIONE ---
# Calcoliamo la media per Fascia e Ruolo
stats_tier = df_tier.groupby(['Fascia', 'Rm_Singolo'])[['Gf', 'Ass']].mean().reset_index()

# Ristrutturiamo per il grafico (Melt)
df_plot_tier = stats_tier.melt(
    id_vars=['Fascia', 'Rm_Singolo'],
    value_vars=['Gf', 'Ass'],
    var_name='Tipo_Bonus',
    value_name='Media_Partita'
)

print("Esempio dati elaborati per Fascia:")
print(stats_tier.head())

# --- 4. VISUALIZZAZIONE (3 SUBPLOTS) ---

# Creiamo una figura con 3 righe (una per tier)
fig, axes = plt.subplots(3, 1, figsize=(14, 18), sharey=True)
fig.suptitle('Performance Medie (Goal vs Assist) per Ruolo e Fascia Squadra', fontsize=16)

# Lista ordinata delle fasce per il loop
fasce_order = ['Top', 'Medie', 'Piccole']

for i, fascia in enumerate(fasce_order):
    ax = axes[i]

    # Filtriamo i dati per la fascia corrente
    data_subset = df_plot_tier[df_plot_tier['Fascia'] == fascia]

    # Creiamo il barplot
    sns.barplot(
        data=data_subset,
        x='Rm_Singolo',
        y='Media_Partita',
        hue='Tipo_Bonus',
        palette={'Gf': '#d62728', 'Ass': '#1f77b4'},  # Rosso Goal, Blu Assist
        order=ordine_ruoli,  # Mantiene l'ordine tattico (Difesa -> Attacco)
        ax=ax
    )

    # Personalizzazione Grafica
    ax.set_title(f'Fascia: {fascia.upper()}', fontsize=14, fontweight='bold', color='black')
    ax.set_xlabel('')
    ax.set_ylabel('Media per Partita')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend(loc='upper left', title='Bonus')

    # Aggiungiamo i valori sopra le barre
    for container in ax.containers:
        ax.bar_label(container, fmt='%.3f', padding=3, fontsize=9)

# Aggiustiamo l'etichetta dell'asse X solo sull'ultimo grafico in basso
axes[2].set_xlabel('Ruolo Mantra', fontsize=12)

plt.tight_layout(rect=[0, 0.03, 1, 0.97])  # Lascia spazio per il titolo principale
plt.show()









print("\n--- ANALISI 8: COMBINAZIONI RUOLI (RAW) DIVISE PER TIER ---")


# --- 2. PREPARAZIONE DATI ---
# Usiamo i ruoli 'grezzi' (Rm) senza esploderli
df_combo_tier = df_completo[['Squadra', 'Rm', 'Gf', 'Ass']].dropna().copy()
df_combo_tier = df_combo_tier[df_combo_tier['Rm'] != '']  # Rimuoviamo vuoti

# Mappiamo la Fascia
df_combo_tier['Fascia'] = df_combo_tier['Squadra'].map(squadra_to_tier)
df_combo_tier = df_combo_tier.dropna(subset=['Fascia'])

# Parametro: Minimo presenze per apparire nel grafico (per evitare outlier statistici)
min_presenze = 20

# --- 3. VISUALIZZAZIONE ---
fig, axes = plt.subplots(3, 1, figsize=(16, 20), sharey=True)  # Sharey permette confronto diretto altezze
fig.suptitle(f'Performance Combinazioni Ruoli per Fascia (Min. {min_presenze} presenze)', fontsize=16)

fasce_order = ['Top', 'Medie', 'Piccole']

for i, fascia in enumerate(fasce_order):
    ax = axes[i]

    # Filtriamo per fascia
    subset = df_combo_tier[df_combo_tier['Fascia'] == fascia]

    # Aggreghiamo i dati
    stats = subset.groupby('Rm').agg(
        Media_Goal=('Gf', 'mean'),
        Media_Assist=('Ass', 'mean'),
        Presenze=('Gf', 'count')
    ).reset_index()

    # FILTRO: Teniamo solo combinazioni con abbastanza dati
    stats = stats[stats['Presenze'] >= min_presenze]

    # ORDINAMENTO: Ordiniamo per "Pericolosità" (Goal*3 + Assist) decrescente
    stats['Score'] = (stats['Media_Goal'] * 3) + stats['Media_Assist']
    stats = stats.sort_values(by='Score', ascending=False)

    # Prepariamo per il grafico (Melt)
    df_plot = stats.melt(id_vars='Rm', value_vars=['Media_Goal', 'Media_Assist'],
                         var_name='Tipo_Bonus', value_name='Media_Partita')

    # Plot
    sns.barplot(
        data=df_plot,
        x='Rm',
        y='Media_Partita',
        hue='Tipo_Bonus',
        palette={'Media_Goal': '#d62728', 'Media_Assist': '#1f77b4'},
        ax=ax
    )

    # Styling
    ax.set_title(f'Fascia: {fascia.upper()}', fontsize=14, fontweight='bold', color='black')
    ax.set_xlabel('')
    ax.set_ylabel('Media Punti Bonus')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.legend(loc='upper right', title='Bonus')

    # Rotazione etichette asse X per leggibilità
    ax.tick_params(axis='x', rotation=45)

    # Etichette valori sulle barre
    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', padding=3, fontsize=8, rotation=90)

# Aggiustamenti finali
axes[2].set_xlabel('Combinazione Ruolo Mantra', fontsize=12)
plt.tight_layout(rect=[0, 0.02, 1, 0.98])
plt.show()
