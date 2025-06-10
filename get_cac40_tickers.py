import requests
from bs4 import BeautifulSoup
import yfinance as yf
import time
import streamlit as st

@st.cache_data(ttl=86400)
def get_cac40_tickers():
    # Nouvelle URL pour la composition du CAC 40 sur Investing.com
    url = "https://fr.investing.com/indices/france-40-components"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"} # Un User-Agent plus complet peut aider

    try:
        response = requests.get(url, headers=headers, timeout=15) # Augmente le timeout
        response.raise_for_status() # Lève une exception pour les codes d'état HTTP d'erreur
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération de la page Investing.com : {e}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    # La table des composants du CAC 40 sur Investing.com a la classe 'freeze-column-td' ou se trouve dans un div particulier.
    # Il faut trouver la bonne table. En inspectant, elle se trouve souvent à l'intérieur d'un div avec l'ID 'recentFinancialReport'
    # ou une structure similaire. La table elle-même a souvent la classe 'datatable_body___sKx7g'.
    # Faisons simple et cherchons une table avec une classe qui contient 'datatable' et vérifions son contenu.
    
    # Tentons de trouver la table qui contient les données des composants
    # L'ID 'recentFinancialReport' ou une classe comme 'js-top-stocks-table' sont des cibles potentielles.
    # Après inspection des résultats de recherche, une classe 'datatable_body__xxxx' semble être utilisée pour le corps des tableaux
    # ou une classe 'datatable'.
    
    # On va chercher la table par son ID 'recentFinancialReport', puis le tableau à l'intérieur
    # Ou plus directement par une classe souvent utilisée pour les tableaux de données: 'datatable' ou 'stock_screener_body__...'.
    
    # Testons avec une classe générique de table pour les données
    table = soup.find("table", {"class": "datatable_table__t_r_yP"}) # J'ai inspecté la page et c'est une classe générique pour le tableau.
                                                                     # Cela peut changer souvent.

    tickers_dict = {}
    if table:
        # Les lignes de données commencent après l'en-tête, souvent la deuxième ligne
        rows = table.find_all("tr")[1:] # On saute l'en-tête si présent

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2: # On a besoin d'au moins 2 colonnes pour le nom et le ticker
                # Le nom de l'entreprise est généralement dans la première colonne (index 0)
                # Le symbole (ticker) est généralement dans la deuxième colonne (index 1)
                
                # Le texte du nom de l'entreprise est souvent dans un <a> à l'intérieur du <td>
                name_element = cols[0].find('a')
                if name_element:
                    name = name_element.get_text(strip=True)
                else:
                    name = cols[0].get_text(strip=True) # Fallback

                # Le ticker est souvent dans la deuxième colonne, directement en texte ou dans un span
                ticker_element = cols[1]
                guess_ticker = ticker_element.get_text(strip=True)

                if name and guess_ticker:
                    # Pour Investing.com, les tickers sont parfois sans le suffixe ".PA".
                    # On va essayer d'ajouter le suffixe ".PA" pour les tickers qui n'en ont pas
                    # et qui ne sont pas déjà des formats connus (comme pour les USA: MSFT, etc.)
                    if not guess_ticker.endswith(".PA") and not "." in guess_ticker:
                        guess_ticker_with_pa = guess_ticker + ".PA"
                    else:
                        guess_ticker_with_pa = guess_ticker # Utilise le ticker tel quel s'il a déjà un suffixe ou un point

                    try:
                        # On essaie le ticker avec .PA d'abord
                        info = yf.Ticker(guess_ticker_with_pa).info
                        if "longName" in info:
                            tickers_dict[info["longName"]] = guess_ticker_with_pa
                        else:
                            # Si .PA ne donne rien, on essaie le ticker original
                            info = yf.Ticker(guess_ticker).info
                            if "longName" in info:
                                tickers_dict[info["longName"]] = guess_ticker
                            else:
                                # Si aucune des tentatives ne marche, on l'ajoute avec le nom trouvé
                                tickers_dict[name] = guess_ticker
                    except Exception as e:
                        # Si yfinance échoue, on peut choisir d'ajouter le nom et le ticker trouvé ou l'ignorer
                        # Pour ne pas bloquer l'appli, on peut l'ajouter tel quel même sans validation yfinance
                        # st.warning(f"Impossible de valider {guess_ticker} pour {name} avec yfinance : {e}")
                        if guess_ticker: # Ajouter seulement si un ticker a été trouvé
                            tickers_dict[name] = guess_ticker
                        pass # Ignore les tickers qui ne peuvent pas être validés par yfinance
                    time.sleep(0.5) # Délai pour éviter le blocage par yfinance
    else:
        st.error("Table de composition du CAC 40 introuvable sur la page Investing.com. La structure du site a peut-être changé.")

    return tickers_dict
