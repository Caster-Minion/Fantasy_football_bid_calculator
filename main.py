import time
import os
import sys
from fanta_scraper import inizializza_browser, ottieni_stato_asta
from fanta_brain import FantaBrain

# --- CONFIGURAZIONE ---
URL_ASTA = "https://app.fantalab.it/asta?asta=630148e4-fd5e-48e8-9bba-ba36a88cd98c"
PATH_CSV = "fm_forecast.csv"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def seleziona_tua_squadra(driver):
    """
    Scansiona le squadre e chiede all'utente di inserire il numero (ID)
    della propria squadra. Ritorna il NOME della squadra.
    """
    print("\n--- RILEVAMENTO SQUADRE ---")
    print("Scansiono le squadre presenti (attendi qualche secondo)...")
    time.sleep(2)  # Piccola pausa per dare tempo al sito di caricare il DOM

    stato = ottieni_stato_asta(driver)
    squadre = stato['squadre']

    if not squadre:
        print("❌ Nessuna squadra trovata! Assicurati di essere nella pagina dell'asta e di aver fatto il LOGIN.")
        input("Premi INVIO per riprovare...")
        return None

    print("\nElenco squadre trovate:")
    for sq in squadre:
        print(f"[{sq['id']}] {sq['nome']} (Crediti: {sq['crediti']})")

    while True:
        try:
            scelta_input = input("\nInserisci il NUMERO della tua squadra (es. 0): ")
            scelta_idx = int(scelta_input)

            # Cerchiamo la squadra con quell'ID esatto
            squadra_scelta = next((s for s in squadre if s['id'] == scelta_idx), None)

            if squadra_scelta:
                print(f"✅ Hai selezionato: {squadra_scelta['nome']}")
                return squadra_scelta['nome']  # Ritorniamo il NOME per usarlo come riferimento stabile
            else:
                print("❌ Numero non valido. Riprova.")

        except ValueError:
            print("❌ Devi inserire un numero intero.")


def main():
    print("--- FANTALAB BOT AI 3.2 (No-Dupes Edition) ---")

    # 1. Caricamento Cervello
    try:
        brain = FantaBrain(PATH_CSV)
    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file {PATH_CSV}. Crealo prima di avviare.")
        return

    # 2. Avvio Browser
    print("Avvio Browser...")
    driver = inizializza_browser(URL_ASTA)

    print("\n" + "=" * 50)
    print(" 1. Fai il LOGIN su Fantalab.")
    print(" 2. Vai nella schermata dell'asta.")
    print(" 3. Quando vedi le squadre caricate, torna qui.")
    print("=" * 50)
    input(">>> PREMI INVIO PER SCEGLIERE LA SQUADRA <<<")

    # 3. Selezione Squadra Interattiva
    MIO_NOME_SQUADRA = None
    while not MIO_NOME_SQUADRA:
        MIO_NOME_SQUADRA = seleziona_tua_squadra(driver)

    print("\nAvvio monitoraggio in tempo reale...")
    time.sleep(1)

    try:
        while True:
            # A. Ottieni stato dal browser
            stato = ottieni_stato_asta(driver)
            giocatore_corrente = stato['giocatore_asta']

            # Pulizia schermo
            clear_screen()
            print(f"📡 STATO ASTA - {time.strftime('%H:%M:%S')}")
            print(f"👤 Utente: {MIO_NOME_SQUADRA}")
            print("-" * 40)

            # B. Analisi Squadre e Budget (Ritroviamo la squadra tramite il NOME)
            mia_squadra_data = next((s for s in stato['squadre'] if s['nome'] == MIO_NOME_SQUADRA), None)

            if not mia_squadra_data:
                print(f"⚠️ ATTENZIONE: Non trovo la squadra '{MIO_NOME_SQUADRA}' nella scansione corrente.")
                print("Possibili cause: caricamento lento o cambio nome.")
                time.sleep(2)
                continue

            mio_budget = mia_squadra_data['crediti']
            miei_giocatori = mia_squadra_data['rosa_nomi']

            # Raccogliamo giocatori presi dagli altri
            altri_giocatori = []
            for s in stato['squadre']:
                if s['nome'] != MIO_NOME_SQUADRA:
                    altri_giocatori.extend(s['rosa_nomi'])

            print(f"💰 Tuo Budget: {mio_budget}")
            print(f"📋 Tua Rosa: {len(miei_giocatori)} giocatori")

            # C. Logica Asta
            if giocatore_corrente and giocatore_corrente != "NESSUNO":
                print(f"\n🔥 IN ASTA: >>> {giocatore_corrente} <<<")

                max_bid, msg = brain.calcola_offerta_massima(
                    my_team_names=miei_giocatori,
                    taken_players_names=altri_giocatori,
                    budget=mio_budget,
                    player_in_auction_name=giocatore_corrente
                )

                print(f"\n🤖 CONSIGLIO AI:")
                print(f"   {msg}")
            else:
                print("\n💤 In attesa di chiamata...")

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nChiusura in corso...")
        driver.quit()
    except Exception as e:
        print(f"\nErrore Critico: {e}")
        # driver.quit()


if __name__ == "__main__":
    main()