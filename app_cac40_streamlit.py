import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from get_cac40_tickers import get_cac40_tickers
import plotly.graph_objects as go
import time

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
    tickers_symbols_to_collect = [tickers_dict[name] for name in selected] # Renommé pour clarté
    
    collected_dfs = [] # Liste pour stocker les DataFrames valides
    data_by_ticker = {} # Dictionnaire pour les DataFrames individuels pour les graphiques

    st.info(f"Début de la collecte pour {len(tickers_symbols_to_collect)} tickers...")
    
    for i, ticker_symbol in enumerate(tickers_symbols_to_collect):
        st.write(f"Collecte des données pour : **{ticker_symbol}** ({i+1}/{len(tickers_symbols_to_collect)})")
        try:
            # Assurez-vous que l'intervalle est correct (1m pour intraday)
            data = yf.download(ticker_symbol, period="1d", interval="1m", progress=False)

            if not data.empty:
                # Renommer la colonne d'index en 'Datetime' avant de la reset
                if 'Datetime' not in data.columns and data.index.name != 'Datetime':
                    data.index.name = 'Datetime' # S'assurer que l'index a un nom
                
                data = data.reset_index() # Transformer l'index (Datetime) en colonne
                data["Ticker"] = ticker_symbol # Ajouter la colonne Ticker
                
                # S'assurer que toutes les colonnes standard sont présentes et dans le bon ordre si nécessaire
                # Les colonnes de yfinance sont généralement 'Open', 'High', 'Low', 'Close', 'Volume'
                # et 'Adj Close' (que nous n'utilisons pas pour OHLC).
                # On peut sélectionner explicitement les colonnes désirées pour uniformiser
                required_cols = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']
                
                # Vérifier et ajouter les colonnes manquantes avec NaN si nécessaire (rare avec yfinance)
                for col in required_cols:
                    if col not in data.columns:
                        data[col] = pd.NA # Ou 0, ou np.nan
                        st.warning(f"La colonne '{col}' est manquante pour {ticker_symbol} et a été ajoutée avec des valeurs vides.")

                # S'assurer de l'ordre des colonnes et des types (optionnel mais robuste)
                data = data[required_cols]
                
                collected_dfs.append(data)
                data_by_ticker[ticker_symbol] = data # Stocker la copie pour le graphique
                st.success(f"{ticker_symbol} collecté avec succès.")
            else:
                st.warning(f"Aucune donnée récupérée pour {ticker_symbol}.")

        except Exception as e:
            st.error(f"Erreur lors de la collecte pour {ticker_symbol} : {e}")
            print(f"DEBUG_LOG: Erreur pour {ticker_symbol}: {e}")

        time.sleep(1) # Délai pour éviter le blocage par Yahoo Finance

    st.info(f"Fin de la collecte. Nombre de DataFrames collectés : {len(collected_dfs)}")
    
    if collected_dfs:
        # Concaténation des DataFrames collectés verticalement
        df = pd.concat(collected_dfs, ignore_index=True) # ignore_index=True réinitialise l'index global
        
        st.session_state['full_df'] = df
        st.session_state['data_by_ticker'] = data_by_ticker # Assurez-vous que c'est le dictionnaire des DF individuels

        st.write("--- Résumé des données agrégées ---")
        st.write(f"Nombre total de lignes dans le DataFrame final : {len(df)}")
        st.write("Distribution des tickers dans le DataFrame final :")
        st.dataframe(df['Ticker'].value_counts())
        st.write("Aperçu des premières lignes du DataFrame final :")

        st.dataframe(df.head(20)) # Affiche plus de lignes pour mieux voir

        # Reste du code pour les graphiques et l'export CSV (inchangé)
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

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "💾 Télécharger CSV",
            csv,
            f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            key="main_csv_download"
        )
    else:
        st.warning("Aucune donnée récupérée pour les entreprises sélectionnées.")

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
