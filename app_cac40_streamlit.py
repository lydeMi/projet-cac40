import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from get_cac40_tickers import get_cac40_tickers
import plotly.graph_objects as go
from plotly.subplots import make_subplots # <-- NOUVEL IMPORT pour les sous-graphiques
import time
import numpy as np

st.set_page_config(page_title="CAC40 Viewer", layout="wide")
st.title("Application de Suivi Boursier - CAC 40")

# --- Gestion de la liste des tickers CAC 40 ---
if 'tickers_dict' not in st.session_state:
    st.session_state['tickers_dict'] = get_cac40_tickers()

if st.button("Rafraîchir la liste CAC 40", key="refresh_tickers_button"):
    st.session_state['tickers_dict'] = get_cac40_tickers()
    st.success("Liste du CAC 40 rafraîchie avec succès !")

tickers_dict = st.session_state.get('tickers_dict')

# --- Utilisation des onglets ---
tab1, tab2 = st.tabs(["Suivi en temps réel", "Visualisation du CAC 40"])

# --- Contenu du Premier Onglet : Suivi en temps réel ---
with tab1:
    st.header("Suivi en temps réel – Données Intraday")

    selected_companies = st.multiselect(
        "Sélectionne les entreprises à surveiller :",
        list(tickers_dict.keys()),
        default=list(tickers_dict.keys())[:5],
        key="multiselect_companies"
    )

    collection_status_placeholder = st.empty()

    if st.button("Lancer la collecte des données", key="launch_collection_button"):
        tickers_symbols_to_collect = [tickers_dict[name] for name in selected_companies]
        
        collected_dfs = [] 
        data_by_ticker = {} 

        collection_status_placeholder.info(f"Début de la collecte pour {len(tickers_symbols_to_collect)} tickers...")
        print(f"DEBUG_LOG: Début de la collecte pour {len(tickers_symbols_to_collect)} tickers.")

        EXPECTED_COLUMNS = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']

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

                        with st.expander(f"Détails de {company_display_name} ({ticker_symbol})"):
                            st.success(f"{company_display_name} ({ticker_symbol}) collecté avec succès. {len(processed_data)} lignes.")
                            st.dataframe(processed_data.head())
                        print(f"DEBUG_LOG: {ticker_symbol} - Données récupérées, {len(processed_data)} lignes.")
                    else:
                        st.warning(f"Aucune donnée récupérée pour {company_display_name} ({ticker_symbol}). Le DataFrame est vide.")
                        print(f"DEBUG_LOG: DataFrame vide pour {ticker_symbol} après yf.download.")

                except Exception as e:
                    st.error(f"Erreur lors de la collecte pour {company_display_name} ({ticker_symbol}) : {e}")
                    print(f"DEBUG_LOG: Erreur pour {ticker_symbol}: {e}")

                time.sleep(1)

        collection_status_placeholder.empty()
        st.info(f"Fin de la collecte. {len(collected_dfs)} DataFrames valides collectés.")
        print(f"DEBUG_LOG: Fin de la boucle de collecte. {len(collected_dfs)} DataFrames validés.")

        if collected_dfs:
            df_final = pd.concat(collected_dfs, ignore_index=True)
            st.session_state['full_df'] = df_final 
            st.session_state['data_by_ticker'] = data_by_ticker 
            st.success("Données du CAC 40 chargées et agrégées avec succès !")
        else:
            st.session_state['full_df'] = pd.DataFrame() 
            st.session_state['data_by_ticker'] = {}
            st.warning("Aucune donnée du CAC 40 n'a pu être récupérée pour les entreprises sélectionnées. Vérifiez les tickers ou réessayez plus tard.")

    # --- Section d'affichage des données agrégées (toujours visible si données présentes) ---
    if 'full_df' in st.session_state and not st.session_state['full_df'].empty:
        st.markdown("---")
        st.subheader("Résumé des données agrégées")
        st.write(f"Nombre total de lignes dans le DataFrame final : **{len(st.session_state['full_df'])}**")
        st.write("Distribution des tickers dans le DataFrame final :")
        st.dataframe(st.session_state['full_df']['Ticker'].value_counts().reset_index().rename(columns={'index': 'Ticker', 'Ticker': 'Nombre de Lignes'}))
        
        with st.expander("Aperçu des premières lignes du DataFrame final"):
            st.dataframe(st.session_state['full_df'].head(20)) 

        # --- Section Graphiques Détaillés (avec VOLUME) ---
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
                # --- DÉBUT DE LA MODIFICATION POUR GRAPHIQUES PRIX + VOLUME ---
                # Crée une figure avec deux sous-graphiques: un pour les chandeliers, un pour le volume
                # rows=2, cols=1: 2 lignes, 1 colonne
                # shared_xaxes=True: Les deux graphiques partageront le même axe des X (le temps)
                # vertical_spacing: Ajuste l'espace vertical entre les sous-graphiques
                # row_heights: Définit la hauteur relative de chaque sous-graphique (ex: prix 3x plus grand que volume)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.03, row_heights=[0.7, 0.3])

                # Ajoute le graphique en chandeliers sur le premier sous-graphique (row=1)
                fig.add_trace(go.Candlestick(
                    x=chart_df['Datetime'],
                    open=chart_df['Open'],
                    high=chart_df['High'],
                    low=chart_df['Low'],
                    close=chart_df['Close'],
                    name='Prix'
                ), row=1, col=1)

                # Ajoute le graphique de volume sur le second sous-graphique (row=2)
                fig.add_trace(go.Bar(
                    x=chart_df['Datetime'],
                    y=chart_df['Volume'],
                    name='Volume',
                    marker_color='blue' # Couleur pour le volume
                ), row=2, col=1)

                # Met à jour la mise en page des titres et axes
                fig.update_layout(
                    title_text=f"Cours Intraday en Chandeliers et Volume de {selected_plot_name} ({ticker_to_plot_symbol})",
                    xaxis_rangeslider_visible=False, # Cache le range slider par défaut
                    height=600 # Ajuste la hauteur de la figure pour mieux voir les deux graphiques
                )

                # Met à jour les axes Y pour les titres
                fig.update_yaxes(title_text="Prix", row=1, col=1)
                fig.update_yaxes(title_text="Volume", row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True, key="main_candlestick_chart")
                # --- FIN DE LA MODIFICATION POUR GRAPHIQUES PRIX + VOLUME ---
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
        st.info("Cliquez sur 'Lancer la collecte des données' pour afficher les informations du CAC 40.")


# --- Contenu du Deuxième Onglet : Visualisation du CAC 40 ---
with tab2:
    st.header("Visualisation Complète du CAC 40")
    st.write("Voici la liste complète des entreprises du CAC 40 actuellement suivie, avec leurs symboles boursiers.")

    if tickers_dict:
        df_cac40_list = pd.DataFrame(tickers_dict.items(), columns=["Nom de l'entreprise", "Symbole (Ticker)"])
        df_cac40_list = df_cac40_list.sort_values("Nom de l'entreprise").reset_index(drop=True)
        
        st.dataframe(df_cac40_list, use_container_width=True)

        st.markdown("---")
        st.subheader("Accès aux données récentes du CAC 40")
        
        # --- DÉBUT DE L'AJOUT DU GRAPHIQUE D'INDICE CAC 40 ---
        st.info("Vous pouvez visualiser le cours intraday de l'indice CAC 40 (`^FCHI`) ci-dessous.")
        if st.button("Afficher le graphique de l'indice CAC 40", key="show_cac40_index_chart"):
            with st.spinner("Récupération des données de l'indice CAC 40..."):
                try:
                    # Collecter l'indice CAC 40 (^FCHI)
                    # Utilisation d'un intervalle de 1 minute pour les données intraday
                    index_data = yf.download('^FCHI', period="1d", interval="1m", progress=False)
                    
                    if not index_data.empty:
                        fig_index = go.Figure(data=[go.Candlestick(
                            x=index_data.index, # L'index est déjà la date/heure pour l'indice
                            open=index_data['Open'],
                            high=index_data['High'],
                            low=index_data['Low'],
                            close=index_data['Close'],
                            name='CAC 40 Index'
                        )])
                        fig_index.update_layout(
                            title="Cours Intraday de l'indice CAC 40 (^FCHI)",
                            xaxis_title="Heure",
                            yaxis_title="Points",
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig_index, use_container_width=True, key="cac40_index_chart")
                    else:
                        st.warning("Impossible de récupérer les données de l'indice CAC 40 (^FCHI). Le DataFrame est vide.")
                except Exception as e:
                    st.error(f"Erreur lors de la collecte de l'indice CAC 40 : {e}")
        # --- FIN DE L'AJOUT DU GRAPHIQUE D'INDICE CAC 40 ---

        st.write("Pour le moment, vous pouvez collecter les dernières données de chaque entreprise en sélectionnant l'onglet 'Suivi en temps réel'.")
        
        csv_cac40_list = df_cac40_list.to_csv(index=False).encode("utf-8")
        st.download_button(
            "💾 Télécharger la liste complète du CAC 40 (CSV)",
            csv_cac40_list,
            f"cac40_liste_{datetime.now().strftime('%Y%m%d')}.csv",
            key="download_cac40_list"
        )
    else:
        st.warning("La liste des tickers du CAC 40 n'a pas pu être chargée. Veuillez rafraîchir la page ou vérifier la connexion.")
