# CAC40 Tracker Pro

**CAC40 Tracker Pro** est une application Streamlit interactive et moderne permettant de suivre en temps réel l'évolution des entreprises du CAC 40, enrichie d'indicateurs techniques et d'une interface entièrement personnalisée.

![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)

---

## Fonctionnalités

-  Récupération dynamique de la liste officielle des entreprises du CAC 40 (scraping ZoneBourse)
-  Collecte intelligente des données via [yfinance](https://github.com/ranaroussi/yfinance)
-  Visualisation temps réel en chandeliers, lignes, volumes
-  Indicateurs techniques intégrés : RSI, MACD, moyennes mobiles, bandes de Bollinger
-  Tableau de bord complet avec statistiques, filtres avancés et résumé par secteur
-  Déployable sur [Streamlit Cloud](https://streamlit.io/cloud)


---

##  Installation

```bash
git clone https://github.com/ton-utilisateur/cac40-streamlit.git
cd cac40-streamlit
pip install -r requirements.txt
streamlit run app_cac40_streamlit.py
