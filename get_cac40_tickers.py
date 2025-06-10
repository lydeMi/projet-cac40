import requests
from bs4 import BeautifulSoup
import yfinance as yf
import time
import streamlit as st

@st.cache_data(ttl=86400)
def get_cac40_tickers():
    # Nouvelle URL pour la composition du CAC 40 sur EasyBourse
    url = "https://www.easybourse.com/indice-composition/cac-40/FR0003500008-25"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10) # Ajout d'un timeout
        response.raise_for_status() # Lève une exception pour les codes d'état HTTP d'erreur
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération de la page web : {e}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    # La table sur EasyBourse a l'ID "table-composition"
    table = soup.find("table", {"id": "table-composition"})

    tickers_dict = {}
    if table:
        # Les lignes de données commencent après la première ligne (l'en-tête)
        rows = table.find_all("tr")[1:]

        for row in rows:
            # Les colonnes sont maintenant dans des <td>
            cols = row.find_all("td")
            if len(cols) >= 3: # On a besoin d'au moins 3 colonnes pour le nom et le symbole
                # Le nom de l'entreprise est généralement dans la deuxième colonne (index 1)
                # ou la première colonne textuelle significative.
                # Inspectez la page pour confirmer l'index exact si besoin.
                # Ici, je prends le texte de la 1ère colonne (index 0)
                name_element = cols[0].find('a') # Le nom est souvent dans un lien <a>
                if name_element:
                    name = name_element.get_text(strip=True)
                else:
                    name = cols[0].get_text(strip=True) # Fallback si pas de lien

                # Le symbole ou ticker est souvent dans la 3ème colonne (index 2)
                # On le prend directement car il est déjà formaté (e.g. ORA.PA)
                guess_ticker = cols[2].get_text(strip=True)

                if name and guess_ticker:
                    try:
                        # Une vérification supplémentaire avec yfinance est toujours une bonne idée,
                        # même si le ticker est déjà fourni par EasyBourse
                        info = yf.Ticker(guess_ticker).info
                        if "longName" in info:
                            # Utilisation du nom complet de Yahoo Finance pour plus de cohérence
                            tickers_dict[info["longName"]] = guess_ticker
                        else:
                            # Si longName n'est pas trouvé, on utilise le nom scrapé
                            tickers_dict[name] = guess_ticker
                    except Exception as e:
                        # st.warning(f"Impossible de valider {guess_ticker} pour {name} avec yfinance : {e}")
                        # Optionnel: si yfinance échoue, on peut quand même ajouter le ticker
                        # tickers_dict[name] = guess_ticker
                        pass # Ignore les tickers qui ne peuvent pas être validés par yfinance
                    time.sleep(0.5) # Délai pour éviter le blocage par yfinance
    else:
        st.error("Table de composition du CAC 40 introuvable sur la page EasyBourse. La structure du site a peut-être changé.")

    return tickers_dict
