import pandas as pd
import glob
import matplotlib.pyplot as plt
import seaborn as sns
import os


path = os.path.join("statistiche", "*.xlsx")
files = glob.glob(path)

# Liste per accumulare i dati aggregati di ogni stagione
history_squadra = []
history_mantra = []

for file in files:
    # Estrai l'anno dal nome del file (es: "2024_25")
    # Modifica lo split in base al formato esatto dei tuoi nomi file
    stagione = (file.split('_')[3] + "_" + file.split('_')[4]).replace(".xlsx", "")

    df = pd.read_excel(file, skiprows=1, header=0)
    df = df[df['Pv'] >= 22]

    # 1. Aggregazione per Squadra/Ruolo
    agg_squadra = df.groupby(['Squadra', 'R'])['Fm'].mean().reset_index()
    agg_squadra['Stagione'] = stagione
    history_squadra.append(agg_squadra)

    # 2. Aggregazione per Ruolo Mantra
    agg_mantra = df.groupby(['Squadra','Rm'])['Fm'].mean().reset_index()
    agg_mantra['Stagione'] = stagione
    history_mantra.append(agg_mantra)

# Uniamo
df_history_squadra = pd.concat(history_squadra)
df_history_mantra = pd.concat(history_mantra)

#print(df_history_mantra)
########################################################################






#EDF
plt.figure(figsize=(12, 7))
sns.set_style("whitegrid")

# Definiamo i colori per ogni ruolo in modo che siano facilmente distinguibili
# P = Blu, D = Verde, C = Arancione, A = Rosso
colori_ruoli = {'P': '#1f77b4', 'D': '#2ca02c', 'C': '#ff7f0e', 'A': '#d62728'}

# 2. PLOT DELLA DENSITÀ (KDE - Empirical Density Function)
# Usiamo il dataframe df_all_players (che contiene tutti i dati non aggregati)
kde_plot = sns.kdeplot(
    data=df_history_squadra,
    x='Fm',
    hue='R',
    palette=colori_ruoli,
    fill=True,           # Riempie l'area sotto la curva
    common_norm=False,    # Normalizza ogni ruolo separatamente per confrontare le forme
    alpha=0.4,           # Trasparenza per vedere le sovrapposizioni
    linewidth=3
)

# 3. PERSONALIZZAZIONE DELLA LEGENDA
# Personalizziamo le etichette per rendere la legenda più leggibile
plt.legend(
    title='Ruoli',
    labels=[ 'Portieri (P)', 'Difensori (D)', 'Centrocampisti (C)','Attaccanti (A)'],
    loc='upper right',
    frameon=True,
    shadow=True
)

# 4. DETTAGLI DEL GRAFICO
plt.title('Distribuzione di Probabilità (EDF) della Fantamedia per Ruolo', fontsize=16, pad=20)
plt.xlabel('Fantamedia (Fm)', fontsize=13)
plt.ylabel('Densità (Frequenza relativa)', fontsize=13)

# Aggiungiamo una linea di riferimento sulla sufficienza
plt.axvline(6.0, color='grey', linestyle='--', alpha=0.6)
plt.text(6.1, 0.05, 'Soglia 6.0', color='grey', fontweight='bold')

# Limiti asse X per focalizzarsi sui voti reali
plt.xlim(4.5, 9.5)

plt.tight_layout()
plt.show()





########################################################################



"""
#Plot ruolo squadra

print("Squadre disponibili:", df_history_mantra['Squadra'].unique())
scelta = input("Inserisci le squadre divise da virgola (es: Inter, Milan, Juventus) o scrivi 'TUTTE': ")

print("Ruoli mantra disponibili:", df_history_mantra['Rm'].unique())

if scelta.upper() == 'TUTTE':
    squadre_da_visualizzare = df_history_mantra['Squadra'].unique()
else:
    # Trasforma la stringa in una lista e rimuove spazi vuoti
    squadre_da_visualizzare = [s.strip() for s in scelta.split(',')]

# 2. SELEZIONA IL RUOLO
ruolo_target = input("Quale ruolo (mantra) vuoi analizzare?: ")

# 3. FILTRA IL DATAFRAME
df_filtrato = df_history_mantra[
    (df_history_mantra['Squadra'].isin(squadre_da_visualizzare)) &
    (df_history_mantra['Rm'] == ruolo_target)
    ]

# 4. PLOT
plt.figure(figsize=(12, 6))

for squadra in squadre_da_visualizzare:
    data_plot = df_filtrato[df_filtrato['Squadra'] == squadra].sort_values('Stagione')

    if not data_plot.empty:
        plt.plot(data_plot['Stagione'], data_plot['Fm'], marker='o', linewidth=2, label=squadra)

plt.title(f'Andamento Fantamedia Ruolo: {ruolo_target} - Selezione Personalizzata')
plt.xlabel('Stagione')
plt.ylabel('Fantamedia Media')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(title="Squadre", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

plt.show()
########################################################################
"""






#Plot per fascia team (alta media bassa)
# --- DEFINIZIONE FASCE ---
fasce = {
    'Top': ['Inter', 'Juventus', 'Milan', 'Napoli', 'Roma', 'Atalanta'],
    'Medie': ['Torino', 'Bologna', 'Sassuolo', 'Udinese', 'Sampdoria', 'Genoa', 'Lazio', 'Verona', 'Fiorentina', 'Como'],
    'Piccole': ['Empoli', 'Cagliari', 'Salernitana', 'Lecce', 'Spezia', 'Venezia', 'Cremonese',
                'Frosinone', 'Benevento', 'SPAL', 'Crotone', 'Parma', 'Brescia', 'Pescara', 'Carpi', 'Chievo', 'Monza']
}


# Funzione per assegnare la fascia
def assegna_fascia(squadra):
    for fascia, lista in fasce.items():
        if squadra in lista:
            return fascia
    return 'Altro'


# Aggiungiamo la colonna Fascia al dataframe storico
df_history_squadra['Fascia'] = df_history_squadra['Squadra'].apply(assegna_fascia)

# Calcoliamo la media per Fascia, Ruolo e Stagione
df_fasce = df_history_squadra.groupby(['Fascia', 'R', 'Stagione'])['Fm'].mean().reset_index()

# --- PLOTTING PER OGNI RUOLO ---
ruoli = ['P', 'D', 'C', 'A']
colori_fasce = {'Top': 'gold', 'Medie': 'silver', 'Piccole': 'brown'}

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
axes = axes.flatten()

for i, ruolo in enumerate(ruoli):
    ax = axes[i]
    for fascia in ['Top', 'Medie', 'Piccole']:
        data_fascia = df_fasce[(df_fasce['Fascia'] == fascia) & (df_fasce['R'] == ruolo)].sort_values('Stagione')

        if not data_fascia.empty:
            ax.plot(data_fascia['Stagione'], data_fascia['Fm'],
                    marker='s', linewidth=3, label=fascia, color=colori_fasce.get(fascia))

    ax.set_title(f'Andamento Fm Media: Ruolo {ruolo}')
    ax.set_xlabel('Stagione')
    ax.set_ylabel('Fantamedia')
    ax.grid(True, alpha=0.3)
    ax.legend()

plt.tight_layout()
plt.show()

########################################################################





df_history_mantra['Fascia'] = df_history_mantra['Squadra'].apply(assegna_fascia)


print("Ruoli Mantra disponibili nel database:", df_history_mantra['Rm'].unique())
ruolo_target = input("Quale ruolo Mantra vuoi plottare? (es: C, T, Pc, Dc, M...): ").strip()

# 4. AGGREGAZIONE PER IL PLOT
# Calcoliamo la media della Fantamedia per ogni fascia in ogni stagione per il ruolo scelto
df_plot = df_history_mantra[df_history_mantra['Rm'].str.contains(ruolo_target, na=False, case=False)]


if df_plot.empty:
    print(f"Errore: Nessun dato trovato per il ruolo {ruolo_target}")
else:
    df_final = df_plot.groupby(['Fascia', 'Stagione'])['Fm'].mean().reset_index()

    # 5. PLOTTING
    plt.figure(figsize=(12, 6))
    colori_fasce = {'Top': 'gold', 'Medie': 'silver', 'Piccole': 'brown'}

    # Ordiniamo le stagioni per l'asse X
    stagioni_ordinate = sorted(df_final['Stagione'].unique())

    for fascia in ['Top', 'Medie', 'Piccole']:
        data_fascia = df_final[df_final['Fascia'] == fascia].set_index('Stagione').reindex(
            stagioni_ordinate).reset_index()

        if not data_fascia['Fm'].isna().all():
            plt.plot(data_fascia['Stagione'], data_fascia['Fm'],
                     marker='o', linewidth=3, label=fascia, color=colori_fasce.get(fascia))

    plt.title(f'Andamento Fantamedia Media per Fascia - Ruolo Mantra: {ruolo_target}', fontsize=15)
    plt.xlabel('Stagione')
    plt.ylabel('Fantamedia Media')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title="Fasce Team")
    plt.tight_layout()

    plt.show()


