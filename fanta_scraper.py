from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def inizializza_browser(url_asta):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url_asta)
    return driver


def ottieni_stato_asta(driver):
    """
    Ritorna un dizionario:
    {
        'giocatore_asta': 'NOME',
        'squadre': [
            {'id': 0, 'nome': '0', ...},
            {'id': 1, 'nome': '1', ...}
        ]
    }
    """
    stato = {
        "giocatore_asta": None,
        "squadre": []
    }

    # 1. Trova Giocatore in Asta
    try:
        selettore = ".MuiTypography-root.MuiTypography-h4.MuiTypography-alignLeft"
        elem = driver.find_element(By.CSS_SELECTOR, selettore)
        stato["giocatore_asta"] = elem.text.strip().upper()
    except:
        stato["giocatore_asta"] = "NESSUNO"

    # 2. Scansiona Squadre
    cards = driver.find_elements(By.CSS_SELECTOR, "div.divHover")

    idx_counter = 0  # Contatore per assegnare ID numerico e il nuovo NOME

    for card in cards:
        try:
            # Controllo validità card (verifichiamo che la card abbia l'elemento del nome)
            try:
                # Estraiamo il nome originale solo per assicurarci che il blocco sia valido,
                # ma non lo salviamo più nella variabile nome_sq
                card.find_element(By.CSS_SELECTOR, "p.MuiTypography-body2").text.strip()
            except:
                continue  # Se non ha il nodo del nome, ignoriamo la card

            # Crediti
            try:
                crediti_txt = card.find_element(By.TAG_NAME, "h5").text
                crediti_int = int(crediti_txt.lower().replace("cr", "").strip())
            except:
                continue

            # Rosa
            rosa = []
            righe = card.find_elements(By.CLASS_NAME, "playerRow")
            for riga in righe:
                try:
                    raw_name = riga.find_element(By.CSS_SELECTOR, "span.MuiTypography-alignLeft").text
                    rosa.append(raw_name.strip().upper())
                except:
                    continue

            # Aggiungiamo alla lista assegnando l'indice come nome
            stato["squadre"].append({
                "id": idx_counter,
                "nome": str(idx_counter), # Modifica applicata: il nome diventa "0", "1", "2"...
                "crediti": crediti_int,
                "rosa_nomi": rosa
            })

            idx_counter += 1

        except:
            continue

    return stato