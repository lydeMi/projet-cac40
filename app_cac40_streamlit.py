import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from get_cac40_tickers import get_cac40_tickers
import plotly.graph_objects as go
import time
import numpy as np

st.set_page_config(page_title="CAC40 Intraday Viewer", layout="wide")
st.title("Suivi en temps réel – CAC 40")

# --- Gestion de la liste des tickers CAC 40 ---
# Initialiser tickers_dict en session_state si ce n'est pas déjà fait
if 'tickers_dict' not in st.session_state:
    st.session_state['tickers_dict'] = get_cac40_tickers()

if st.button("Rafraîchir la liste CAC 40", key="refresh_tickers_button"):
    st.session_state['tickers_dict'] = get_cac40_tickers()
    st.success("Liste du CAC 40 rafraîchie avec succès !") # Message de confirmation

tickers_dict = st.session_state.get('tickers_dict') # Toujours récupérer depuis session_state

# Sélection interactive des entreprises à surveiller
selected_companies = st.multiselect(
    "Sélectionne les entreprises à surveiller :",
    list(tickers_dict.keys()),
    default=list(tickers_dict.keys())[:5],
    key="multiselect_companies"
)

# --- Bouton pour lancer la collecte des données ---
# Utilisez st.empty() pour pouvoir effacer/remplacer des messages plus tard
collection_status_placeholder = st.empty()

if st.button("Lancer la collecte des données", key="launch_collection_button"):
    tickers_symbols_to_collect = [tickers_dict[name] for name in selected_companies]
    
    collected_dfs = [] 
    data_by_ticker = {} 

    collection_status_placeholder.info(f"Début de la collecte pour {len(tickers_symbols_to_collect)} tickers...")
    print(f"DEBUG_LOG: Début de la collecte pour {len(tickers_symbols_to_collect)} tickers.")

    EXPECTED_COLUMNS = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']

    # Utilisation de st.spinner pour une meilleure UX pendant le téléchargement
    with st.spinner("Téléchargement des données en cours... Veuillez patienter."):
        for i, ticker_symbol in enumerate(tickers_symbols_to_collect):
            company_name = [name for name, symbol in tickers_dict.items() if symbol == ticker_symbol]
            company_display_name = company_name[0] if company_name else ticker_symbol
            
            st.write(f"Collecte des données pour : **{company_display_name} ({ticker_symbol})** ({i+1}/{len(tickers_symbols_to_collect)})")
            print(f"DEBUG_LOG: Tentative de collecte pour {ticker_symbol} (étape {i+1}/{len(tickers_symbols_to_collect)}).")

            try:
                data = yf.download(ticker_symbol, period="1d", interval="1m", progress=False)

                if not data.empty:
                    data = data.reset_index()
                    data["Ticker"] = ticker_symbol
                    
                    # Normaliser les noms de colonnes. Gérer le MultiIndex de yfinance.
                    if isinstance(data.columns, pd.MultiIndex):
                        new_columns = []
                        for col_tuple in data.columns:
                            col_name = col_tuple[0] if isinstance(col_tuple, tuple) else col_tuple
                            new_columns.append(col_name.capitalize() if col_name != 'Datetime' else col_name)
                        data.columns = new_columns
                    else:
                        data.columns = [col.capitalize() if col != 'Datetime' else col for col in data.columns]

                    processed_data = pd.DataFrame(columns=EXPECTED_COLUMNS)
                    for col in EXPECTED_COLUMNS:
                        if col in data.columns:
                            processed_data[col] = data[col]
                        else:
                            processed_data[col] = np.nan 
                            st.warning(f"La colonne '{col}' est manquante pour {ticker_symbol} et a été ajoutée avec des valeurs vides.")

                    processed_data = processed_data[EXPECTED_COLUMNS]
                    
                    collected_dfs.append(processed_data)
                    data_by_ticker[ticker_symbol] = processed_data 

                    # Utilisez un st.expander pour les messages de succès détaillés si l'utilisateur veut les voir
                    with st.expander(f"Détails de {company_display_name} ({ticker_symbol})"):
                        st.success(f"{company_display_name} ({ticker_symbol}) collecté avec succès. {len(processed_data)} lignes.")
                        st.dataframe(processed_data.head()) # Afficher un aperçu du DF individuel
                    print(f"DEBUG_LOG: {ticker_symbol} - Données récupérées, {len(processed_data)} lignes.")
                else:
                    st.warning(f"Aucune donnée récupérée pour {company_display_name} ({ticker_symbol}). Le DataFrame est vide.")
                    print(f"DEBUG_LOG: DataFrame vide pour {ticker_symbol} après yf.download.")

            except Exception as e:
                st.error(f"Erreur lors de la collecte pour {company_display_name} ({ticker_symbol}) : {e}")
                print(f"DEBUG_LOG: Erreur pour {ticker_symbol}: {e}")

            time.sleep(1) # Délai pour éviter le rate limiting

    collection_status_placeholder.empty() # Efface le message "Début de la collecte..."
    st.info(f"Fin de la collecte. {len(collected_dfs)} DataFrames valides collectés.")
    print(f"DEBUG_LOG: Fin de la boucle de collecte. {len(collected_dfs)} DataFrames validés.")

    # Concaténation des DataFrames
    if collected_dfs:
        df_final = pd.concat(collected_dfs, ignore_index=True)
        st.session_state['full_df'] = df_final 
        st.session_state['data_by_ticker'] = data_by_ticker 
        st.success("Données du CAC 40 chargées et agrégées avec succès !")
    else:
        st.session_state['full_df'] = pd.DataFrame() # Assurez-vous qu'il y a un DF vide si rien n'est collecté
        st.session_state['data_by_ticker'] = {}
        st.warning("Aucune donnée du CAC 40 n'a pu être récupérée pour les entreprises sélectionnées. Vérifiez les tickers ou réessayez plus tard.")


# --- Section d'affichage des données agrégées (toujours visible si données présentes) ---
# Ce bloc s'exécute à chaque rerun. Il dépend de la présence de 'full_df' en session.
if 'full_df' in st.session_state and not st.session_state['full_df'].empty:
    st.markdown("---") # Séparateur visuel
    st.subheader("Résumé des données agrégées")
    st.write(f"Nombre total de lignes dans le DataFrame final : **{len(st.session_state['full_df'])}**")
    st.write("Distribution des tickers dans le DataFrame final :")
    st.dataframe(st.session_state['full_df']['Ticker'].value_counts().reset_index().rename(columns={'index': 'Ticker', 'Ticker': 'Nombre de Lignes'}))
    
    # Utilisation d'un expander pour l'aperçu du DataFrame, pour ne pas encombrer l'écran
    with st.expander("Aperçu des premières lignes du DataFrame final"):
        st.dataframe(st.session_state['full_df'].head(20)) 

    # --- Section Graphiques Détaillés ---
    st.subheader("Graphiques Intraday Détaillés")
    if st.session_state['data_by_ticker']:
        ticker_display_names_map = {v: k for k, v in tickers_dict.items()}
        plot_selection_options = sorted([ticker_display_names_map.get(s, s) for s in st.session_state['data_by_ticker'].keys()])

        selected_plot_name = st.selectbox(
            "Sélectionne l'entreprise pour le graphique :",
            plot_selection_options,
            key="main_plot_select"
        )
        ticker_to_plot_symbol = tickers_dict.get(selected_plot_name, selected_plot_name)
        
        chart_df = st.session_state['data_by_ticker'].get(ticker_to_plot_symbol)

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
                title=f"Cours Intraday en Chandeliers de {selected_plot_name} ({ticker_to_plot_symbol})",
                xaxis_title="Heure",
                yaxis_title="Prix",
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True, key="main_candlestick_chart")
        else:
            st.warning(f"Impossible d'afficher le graphique pour {selected_plot_name}. Données manquantes ou vides.")
    else:
        st.warning("Aucune donnée disponible pour les graphiques.")

    # --- Bouton d'Export CSV ---
    csv = st.session_state['full_df'].to_csv(index=False).encode("utf-8")
    st.download_button(
        "💾 Télécharger CSV",
        csv,
        f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        key="main_csv_download"
    )
else:
    # Message si aucune donnée n'a encore été chargée
    st.info("Cliquez sur 'Lancer la collecte des données' pour afficher les informations du CAC 40.")
