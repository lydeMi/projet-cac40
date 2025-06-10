import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from get_cac40_tickers import get_cac40_tickers
import plotly.graph_objects as go
import time # Import time pour le sleep

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
    default=list(tickers_dict.keys())[:5],
    key="multiselect_companies"
)

# Lancer la collecte
if st.button("Lancer la collecte des données", key="launch_collection_button"):
    tickers = [tickers_dict[name] for name in selected]
    df_all = []
    data_by_ticker = {}

    st.info(f"Début de la collecte pour {len(tickers)} tickers...") # Debug
    for i, ticker_symbol in enumerate(tickers):
        st.write(f"Collecte des données pour : **{ticker_symbol}** ({i+1}/{len(tickers)})") # Affiche dans l'interface
        try:
            data = yf.download(ticker_symbol, period="1d", interval="1m", progress=False)

            # --- DEBUT DEBUGGING ---
            if data.empty:
                st.warning(f"DEBUG: DataFrame vide pour {ticker_symbol} après yf.download.")
                print(f"DEBUG_LOG: DataFrame vide pour {ticker_symbol} après yf.download.")
            else:
                print(f"DEBUG_LOG: {ticker_symbol} - Données récupérées, {len(data)} lignes.")
            # --- FIN DEBUGGING ---

            if not data.empty:
                data["Ticker"] = ticker_symbol
                data.reset_index(inplace=True)
                df_all.append(data)
                data_by_ticker[ticker_symbol] = data
                st.success(f"{ticker_symbol} collecté avec succès.")
            else:
                st.warning(f"Aucune donnée récupérée pour {ticker_symbol}.")

        except Exception as e:
            st.error(f"Erreur lors de la collecte pour {ticker_symbol} : {e}")
            print(f"DEBUG_LOG: Erreur pour {ticker_symbol}: {e}") # Log de l'erreur

        # Ajout d'un petit délai entre les requêtes pour éviter le rate limiting de Yahoo Finance
        time.sleep(1) # Délai de 1 seconde entre chaque requête. Vous pouvez ajuster si nécessaire.

    st.info(f"Fin de la collecte. Nombre de DataFrames collectés : {len(df_all)}") # Debug
    if df_all:
        df = pd.concat(df_all)
        st.session_state['full_df'] = df
        st.session_state['data_by_ticker'] = data_by_ticker

        # --- DEBUT DEBUGGING ---
        st.write("--- Résumé des données agrégées ---")
        st.write(f"Nombre total de lignes dans le DataFrame final : {len(df)}")
        st.write("Distribution des tickers dans le DataFrame final :")
        st.dataframe(df['Ticker'].value_counts()) # Montre combien de lignes pour chaque ticker
        st.write("Aperçu des premières lignes du DataFrame final :")
        # --- FIN DEBUGGING ---

        st.dataframe(df.head(10)) # Affiche plus de lignes pour voir si d'autres tickers apparaissent au début

        # Graphique d'un ticker (section modifiée)
        st.subheader("Graphiques Intraday Détaillés")
        if data_by_ticker:
            ticker_to_plot_name = st.selectbox(
                "Sélectionne l'entreprise pour le graphique :",
                list(data_by_ticker.keys()),
                key="main_plot_select"
            )
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
                st.plotly_chart(fig, use_container_width=True, key="main_candlestick_chart")
            else:
                st.warning(f"Impossible d'afficher le graphique pour {ticker_to_plot_name}. Données manquantes.")
        else:
            st.warning("Aucune donnée disponible pour les graphiques.")

        # Export CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "💾 Télécharger CSV",
            csv,
            f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            key="main_csv_download"
        )
    else:
        st.warning("Aucune donnée récupérée pour les entreprises sélectionnées.")

# Permettre l'affichage du graphique et l'export CSV après le premier clic
# si les données sont déjà en session (utile si l'utilisateur change de sélection de graphique sans relancer la collecte)
if 'full_df' in st.session_state and 'data_by_ticker' in st.session_state:
    st.subheader("Graphiques Intraday Détaillés (Données en cache)")
    data_by_ticker = st.session_state['data_by_ticker']
    if data_by_ticker:
        ticker_to_plot_name = st.selectbox(
            "Sélectionne l'entreprise pour le graphique (Données en cache) :",
            list(data_by_ticker.keys()),
            key="cached_plot_select"
        )
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
            st.plotly_chart(fig, use_container_width=True, key="cached_candlestick_chart")
        else:
            st.warning(f"Impossible d'afficher le graphique pour {ticker_to_plot_name}. Données manquantes.")
    else:
        st.warning("Aucune donnée disponible en cache pour les graphiques.")

    csv = st.session_state['full_df'].to_csv(index=False).encode("utf-8")
    st.download_button(
        "💾 Télécharger CSV (Données en cache)",
        csv,
        f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}_cached.csv",
        key="cached_csv_download"
    )
