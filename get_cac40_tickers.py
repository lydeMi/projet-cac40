import requests
from bs4 import BeautifulSoup
import yfinance as yf
import time
import streamlit as st

@st.cache_data(ttl=86400)
def get_cac40_tickers():
    # URL pour la composition du CAC 40 sur Investing.com
    url = "https://fr.investing.com/indices/france-40-components"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération de la page Investing.com : {e}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    # La table sur Investing.com n'a pas toujours une classe ou un ID stable,
    # mais elle a l'attribut 'role="grid"'. C'est ce qu'on va utiliser.
    table = soup.find("table", {"role": "grid"})

    tickers_dict = {}
    if table:
        # Les lignes de données sont dans le tbody, et on saute la première ligne (l'en-tête)
        rows = table.find("tbody").find_all("tr") if table.find("tbody") else []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2: # On a besoin d'au moins 2 colonnes pour le nom et le symbole
                # Le nom de l'entreprise est dans la première colonne (index 0)
                name = cols[0].get_text(strip=True)

                # Le symbole (ticker) est dans la deuxième colonne (index 1)
                # Il est au format "DD/MM |TICKER". On doit extraire le TICKER.
                ticker_raw = cols[1].get_text(strip=True)
                if '|' in ticker_raw:
                    guess_ticker = ticker_raw.split('|')[1].strip()
                else:
                    guess_ticker = ticker_raw.strip() # Fallback si le format change

                if name and guess_ticker:
                    # Pour Investing.com, les tickers sont parfois sans le suffixe ".PA".
                    # On va essayer d'ajouter le suffixe ".PA" si nécessaire.
                    final_ticker = ""
                    if not guess_ticker.endswith(".PA") and not "." in guess_ticker:
                        test_ticker_pa = guess_ticker + ".PA"
                    else:
                        test_ticker_pa = guess_ticker # Utilise le ticker tel quel

                    try:
                        # On essaie le ticker avec .PA d'abord
                        info = yf.Ticker(test_ticker_pa).info
                        if "longName" in info:
                            tickers_dict[info["longName"]] = test_ticker_pa
                            final_ticker = test_ticker_pa
                        else:
                            # Si .PA ne donne rien, on essaie le ticker original sans .PA
                            info = yf.Ticker(guess_ticker).info
                            if "longName" in info:
                                tickers_dict[info["longName"]] = guess_ticker
                                final_ticker = guess_ticker
                            else:
                                # Si aucune des tentatives ne marche, on l'ajoute avec le nom trouvé et le ticker original
                                if guess_ticker:
                                    tickers_dict[name] = guess_ticker
                                    final_ticker = guess_ticker
                    except Exception as e:
                        # Si yfinance échoue, on peut choisir d'ajouter le nom et le ticker trouvé ou l'ignorer
                        if guess_ticker:
                            tickers_dict[name] = guess_ticker # Ajoute le ticker trouvé même sans validation yfinance
                        # st.warning(f"Impossible de valider {guess_ticker} pour {name} avec yfinance : {e}")
                        pass # Ignore les tickers qui ne peuvent pas être validés par yfinance

                    if final_ticker: # Introduit un délai seulement si un ticker a été traité avec succès
                        time.sleep(0.5) # Délai pour éviter le blocage par yfinance
    else:
        st.error("Table de composition du CAC 40 introuvable sur la page Investing.com. La structure du site a peut-être changé (attribut 'role=\"grid\"' ou structure tbody/tr/td).")

    return tickers_dict
