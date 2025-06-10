import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from get_cac40_tickers import get_cac40_tickers
import plotly.graph_objects as go # Importez plotly

st.set_page_config(page_title="CAC40 Intraday Viewer", layout="wide")
st.title("Suivi en temps réel – CAC 40")

# Rafraîchir la liste dynamique des tickers
if st.button("Rafraîchir la liste CAC 40"):
    st.session_state['tickers_dict'] = get_cac40_tickers()

# Charger depuis cache/session
tickers_dict = st.session_state.get('tickers_dict', get_cac40_tickers())

# Sélection interactive
selected = st.multiselect(
    "Sélectionne les entreprises à surveiller :",
    list(tickers_dict.keys()),
    default=list(tickers_dict.keys())[:5]
)

# Lancer la collecte
if st.button("Lancer la collecte des données"):
    tickers = [tickers_dict[name] for name in selected]
    df_all = []

    # Utiliser un dictionnaire pour stocker les DataFrames par ticker
    data_by_ticker = {}

    for ticker_symbol in tickers: # Renommer pour éviter le conflit avec 'ticker_plot'
        try:
            # Obtenir les données sur une période plus longue pour un graphique plus parlant
            # 'period="1d", interval="1m"' est bon pour l'intraday, mais un historique est mieux pour un graphique complet.
            # Pour les graphiques intraday, assurez-vous que vous avez bien toutes les colonnes requises (Open, High, Low, Close).
            data = yf.download(ticker_symbol, period="1d", interval="1m", progress=False)

            if not data.empty:
                data["Ticker"] = ticker_symbol
                data.reset_index(inplace=True)
                df_all.append(data)
                data_by_ticker[ticker_symbol] = data # Stocker pour le graphique
                st.success(f"{ticker_symbol} collecté")
            else:
                st.warning(f"Aucune donnée récupérée pour {ticker_symbol}.")
        except Exception as e:
            st.error(f"Erreur {ticker_symbol} : {e}")

    if df_all:
        df = pd.concat(df_all)
        st.session_state['full_df'] = df # Sauvegarder le DataFrame complet en session
        st.session_state['data_by_ticker'] = data_by_ticker # Sauvegarder les données par ticker
        st.dataframe(df.head())

        # Graphique d'un ticker (section modifiée)
        st.subheader("Graphiques Intraday Détaillés")
        # Assurez-vous que data_by_ticker n'est pas vide pour le selectbox
        if data_by_ticker:
            ticker_to_plot_name = st.selectbox("Sélectionne l'entreprise pour le graphique :", list(data_by_ticker.keys()))
            chart_df = data_by_ticker.get(ticker_to_plot_name)

            if chart_df is not None and not chart_df.empty:
                # Créer le graphique en chandeliers avec Plotly
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_df['Datetime'],
                    open=chart_df['Open'],
                    high=chart_df['High'],
                    low=chart_df['Low'],
                    close=chart_df['Close'],
                    name='Prix'
                )])

                fig.update_layout(
                    title=f"Cours Intraday en Chandeliers de {ticker_to_plot_name}",
                    xaxis_title="Heure",
                    yaxis_title="Prix",
                    xaxis_rangeslider_visible=False # Cache le range slider en bas pour plus de clarté intraday
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Impossible d'afficher le graphique pour {ticker_to_plot_name}. Données manquantes.")
        else:
            st.warning("Aucune donnée disponible pour les graphiques.")

        # Export CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("💾 Télécharger CSV", csv, f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
    else:
        st.warning("Aucune donnée récupérée pour les entreprises sélectionnées.")

# Permettre l'affichage du graphique et l'export CSV après le premier clic
# si les données sont déjà en session (utile si l'utilisateur change de sélection de graphique sans relancer la collecte)
if 'full_df' in st.session_state and 'data_by_ticker' in st.session_state:
    st.subheader("Graphiques Intraday Détaillés (Données en cache)")
    data_by_ticker = st.session_state['data_by_ticker']
    if data_by_ticker:
        ticker_to_plot_name = st.selectbox("Sélectionne l'entreprise pour le graphique (Données en cache) :", list(data_by_ticker.keys()), key="cached_plot_select")
        chart_df = data_by_ticker.get(ticker_to_plot_name)

        if chart_df is not None and not chart_df.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=chart_df['Datetime'],
                open=chart_df['Open'],
                high=chart_df['High'],
                low=chart_df['Low'],
                close=chart_df['Close'],
                name='Prix'
            )])
            fig.update_layout(
                title=f"Cours Intraday en Chandeliers de {ticker_to_plot_name}",
                xaxis_title="Heure",
                yaxis_title="Prix",
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Impossible d'afficher le graphique pour {ticker_to_plot_name}. Données manquantes.")
    else:
        st.warning("Aucune donnée disponible en cache pour les graphiques.")

    csv = st.session_state['full_df'].to_csv(index=False).encode("utf-8")
    st.download_button("💾 Télécharger CSV (Données en cache)", csv, f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}_cached.csv", key="cached_csv_download")
