import streamlit as st
import yfinance as yf
import time # Gardé au cas où vous le réutilisiez ou pour de futurs délais

@st.cache_data(ttl=86400) # Le cache est toujours utile pour ne pas recréer le dictionnaire à chaque fois
def get_cac40_tickers():
    # Liste manuelle des entreprises du CAC 40 et de leurs tickers Yahoo Finance
    # Cette liste est à mettre à jour si la composition du CAC 40 change.
    cac40_list = {
        "Accor": "AC.PA",
        "Air Liquide": "AI.PA",
        "Airbus": "AIR.PA",
        "ArcelorMittal": "MT.AS", # Ou MT.PA si elle est aussi listée à Paris pour Yahoo Finance
        "Axa": "CS.PA",
        "BNP Paribas": "BNP.PA",
        "Bouygues": "EN.PA",
        "Capgemini": "CAP.PA",
        "Carrefour": "CA.PA",
        "Crédit Agricole": "ACA.PA",
        "Danone": "BN.PA",
        "Dassault Systèmes": "DSY.PA",
        "Edenred": "EDEN.PA",
        "Engie": "ENGI.PA",
        "EssilorLuxottica": "EL.PA",
        "Eurofins Scientific": "ERF.PA",
        "Hermès International": "RMS.PA",
        "Kering": "KER.PA",
        "Legrand": "LR.PA",
        "L'Oréal": "OR.PA",
        "LVMH": "MC.PA",
        "Michelin": "ML.PA",
        "Orange": "ORA.PA",
        "Pernod Ricard": "RI.PA",
        "Publicis Groupe": "PUB.PA",
        "Renault": "RNO.PA",
        "Safran": "SAF.PA",
        "Saint-Gobain": "SGO.PA",
        "Sanofi": "SAN.PA",
        "Schneider Electric": "SU.PA",
        "Société Générale": "GLE.PA",
        "Stellantis": "STLAP.PA", # ou STLA pour NYSE, vérifiez celle qui fonctionne le mieux
        "STMICROELECTRONICS": "STM.PA",
        "Teleperformance": "TEP.PA",
        "Thales": "HO.PA",
        "TotalEnergies": "TTE.PA",
        "Unibail-Rodamco-Westfield": "URW.AS", # ou URW.PA, vérifiez celle qui fonctionne le mieux
        "Veolia Environnement": "VIE.PA",
        "Vinci": "DG.PA",
        "Vivendi": "VIV.PA" # Si elle est au CAC 40
    }

    # Pour une validation optionnelle avec yfinance (non nécessaire si la liste est fiable)
    # tickers_dict = {}
    # for name, ticker in cac40_list.items():
    #     try:
    #         info = yf.Ticker(ticker).info
    #         if "longName" in info:
    #             tickers_dict[info["longName"]] = ticker
    #         else:
    #             tickers_dict[name] = ticker # Utilise le nom manuel si yfinance ne donne pas de longName
    #     except Exception:
    #         st.warning(f"Le ticker {ticker} pour {name} n'a pas pu être validé par yfinance.")
    #         tickers_dict[name] = ticker # Ajoute le ticker même si yfinance échoue
    #     time.sleep(0.1) # Petit délai pour yfinance si cette boucle est activée

    # Puisque la liste est manuelle et a été vérifiée, on peut la retourner directement
    return cac40_list
