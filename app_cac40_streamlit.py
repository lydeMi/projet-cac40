import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from get_cac40_tickers import get_cac40_tickers
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np

# --- Configuration de la page ---
st.set_page_config(page_title="CAC40 Viewer", layout="wide")

# --- CSS Personnalisé pour le design de l'interface ---
st.markdown("""
    <style>
    /* Masquer le menu hamburger, le pied de page et l'en-tête de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Importation d'une police Google Font (facultatif, mais recommandé pour un meilleur rendu) */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&display=swap');

    body {
        font-family: 'Roboto', sans-serif; /* Appliquer la police à tout le corps */
        background-color: #f0f2f6; /* Un gris très clair pour le fond */
        color: #333333; /* Couleur du texte principal */
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Lato', sans-serif; /* Une police différente pour les titres */
        color: #1a2e4d; /* Une couleur bleu foncé pour les titres */
        padding-top: 10px;
        padding-bottom: 5px;
    }

    /* Style du titre principal */
    .stApp > header {
        background-color: #f0f2f6; /* S'assurer que l'en-tête Streamlit (même s'il est masqué) n'interfère pas */
    }
    .css-18e3th9 { /* Cible le bloc principal de contenu */
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }

    /* Conteneurs et onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px; /* Espace entre les onglets */
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        height: 50px;
        width: 180px; /* Largeur des onglets */
        background-color: #e0e6ed; /* Couleur de fond des onglets inactifs */
        font-size: 1.1em;
        color: #555555;
        font-weight: bold;
        text-transform: uppercase;
        margin: 0;
        padding: 0 20px;
        border: 1px solid #c8d3e2;
        border-bottom: none; /* Pas de bordure en bas pour les onglets */
        transition: background-color 0.3s, color 0.3s;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #d1d9e2; /* Couleur au survol */
        color: #333333;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff; /* Fond de l'onglet actif */
        color: #007bff; /* Couleur du texte de l'onglet actif (bleu vif) */
        border-top: 3px solid #007bff; /* Bordure supérieure pour l'onglet actif */
        border-left: 1px solid #007bff;
        border-right: 1px solid #007bff;
        border-bottom: none;
    }

    /* Généraliser le style des blocs de contenu */
    .stContainer, .stExpander, .stAlert {
        background-color: #ffffff; /* Fond blanc pour les blocs de contenu */
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05); /* Ombre légère */
        padding: 20px;
        margin-bottom: 25px;
        border: 1px solid #e0e6ed; /* Bordure subtile */
    }

    /* Style des boutons */
    .stButton > button {
        background-color: #007bff; /* Bleu vif pour le bouton */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-size: 1em;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: background-color 0.3s, transform 0.2s;
    }
    .stButton > button:hover {
        background-color: #0056b3; /* Bleu plus foncé au survol */
        transform: translateY(-2px); /* Léger effet de soulèvement */
    }

    /* Multiselect et Selectbox */
    .stMultiSelect, .stSelectbox {
        margin-bottom: 15px;
    }
    .stMultiSelect > div > div > div > div, .stSelectbox > div > div > div {
        border-radius: 8px;
        border: 1px solid #c8d3e2;
        box-shadow: none; /* Enlever l'ombre par défaut */
    }

    /* Dataframe */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden; /* Assure que les coins arrondis fonctionnent avec le tableau */
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    /* Style pour les messages d'info/success/warning */
    .stAlert.info {
        background-color: #e6f7ff; /* Bleu très clair */
        color: #0056b3;
        border: 1px solid #91d5ff;
        border-radius: 8px;
    }
    .stAlert.success {
        background-color: #f6ffed; /* Vert très clair */
        color: #389e0d;
        border: 1px solid #b7eb8f;
        border-radius: 8px;
    }
    .stAlert.warning {
        background-color: #fffbe6; /* Jaune très clair */
        color: #d46b08;
        border: 1px solid #ffe58f;
        border-radius: 8px;
    }

    /* Progress bar (optionnel, si vous utilisez st.progress) */
    .stProgress > div > div > div > div {
        background-color: #007bff; /* Couleur de la barre de progression */
    }

    </style>
""", unsafe_allow_html=True)


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

    period_options = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    selected_period = st.selectbox("Période des données :", period_options, index=0, key="period_selectbox")

    selected_companies = st.multiselect(
        "Sélectionne les entreprises à surveiller :",
        list(tickers_dict.keys()),
        default=list(tickers_dict.keys())[:5],
        key="multiselect_companies"
    )

    collection_status_placeholder = st.empty()

    @st.cache_data(ttl=3600)
    def get_ticker_data(ticker_symbol, period):
        if period == "1d":
            interval_val = "1m"
        elif period == "5d":
            interval_val = "1m"
        elif period in ["1mo", "3mo"]:
            interval_val = "5m"
        elif period in ["6mo", "1y"]:
            interval_val = "1h"
        else:
            interval_val = "1d"
        
        data = yf.download(ticker_symbol, period=period, interval=interval_val, progress=False)
        return data

    if st.button("Lancer la collecte des données", key="launch_collection_button"):
        tickers_symbols_to_collect = [tickers_dict[name] for name in selected_companies]
        
        collected_dfs = [] 
        data_by_ticker = {} 

        collection_status_placeholder.info(f"Début de la collecte pour {len(tickers_symbols_to_collect)} tickers...")
        print(f"DEBUG_LOG: Début de la collecte pour {len(tickers_symbols_to_collect)} tickers.")

        EXPECTED_COLUMNS = ['Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']

        with st.spinner("Téléchargement des données en cours... Veuillez patienter."):
            for i, ticker_symbol in enumerate(tickers_symbols_to_collect):
                company_name = [name for name, symbol in tickers_dict.items() if symbol == ticker_symbol]
                company_display_name = company_name[0] if company_name else ticker_symbol
                
                st.write(f"Collecte des données pour : **{company_display_name} ({ticker_symbol})** ({i+1}/{len(tickers_symbols_to_collect)})")
                print(f"DEBUG_LOG: Tentative de collecte pour {ticker_symbol} (étape {i+1}/{len(tickers_symbols_to_collect)}).")

                try:
                    data = get_ticker_data(ticker_symbol, selected_period)

                    if not data.empty:
                        if 'Datetime' not in data.columns and isinstance(data.index, pd.DatetimeIndex):
                            data = data.reset_index()
                            data = data.rename(columns={'index': 'Datetime'})
                        
                        if 'Datetime' in data.columns and data['Datetime'].dtype == 'datetime64[ns, UTC]':
                            data['Datetime'] = data['Datetime'].dt.tz_localize(None)
                        
                        data["Ticker"] = ticker_symbol
                        
                        if isinstance(data.columns, pd.MultiIndex):
                            new_columns = []
                            for col_tuple in data.columns:
                                col_name = col_tuple[0] if isinstance(col_tuple, tuple) else col_tuple
                                new_columns.append(col_name.capitalize() if col_name != 'Datetime' else col_name)
                            data.columns = new_columns
                        else:
                            data.columns = [col.capitalize() if col != 'Datetime' else col for col in data.columns]
                        
                        processed_data_columns = ['Datetime'] + [col for col in EXPECTED_COLUMNS if col != 'Ticker'] + ['Ticker']
                        processed_data = pd.DataFrame(columns=processed_data_columns)
                        
                        for col in processed_data_columns:
                            if col in data.columns:
                                processed_data[col] = data[col]
                            else:
                                processed_data[col] = np.nan 
                                if col != 'Ticker':
                                    st.warning(f"La colonne '{col}' est manquante pour {ticker_symbol} et a été ajoutée avec des valeurs vides.")

                        processed_data = processed_data[processed_data_columns]

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

                time.sleep(0.5)

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

    if 'full_df' in st.session_state and not st.session_state['full_df'].empty:
        st.markdown("<hr style='border:1px solid #e0e6ed; margin-top:30px; margin-bottom:30px;'>", unsafe_allow_html=True)
        st.subheader("Résumé des données agrégées")
        st.write(f"Nombre total de lignes dans le DataFrame final : **{len(st.session_state['full_df'])}**")
        st.write("Distribution des tickers dans le DataFrame final :")
        st.dataframe(st.session_state['full_df']['Ticker'].value_counts().reset_index().rename(columns={'index': 'Ticker', 'Ticker': 'Nombre de Lignes'}))
        
        with st.expander("Aperçu des premières lignes du DataFrame final"):
            st.dataframe(st.session_state['full_df'].head(20)) 

        st.markdown("<hr style='border:1px solid #e0e6ed; margin-top:30px; margin-bottom:30px;'>", unsafe_allow_html=True)
        st.subheader("Graphiques Détaillés")
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
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.03, row_heights=[0.7, 0.3])

                fig.add_trace(go.Candlestick(
                    x=chart_df['Datetime'],
                    open=chart_df['Open'],
                    high=chart_df['High'],
                    low=chart_df['Low'],
                    close=chart_df['Close'],
                    name='Prix'
                ), row=1, col=1)

                fig.add_trace(go.Bar(
                    x=chart_df['Datetime'],
                    y=chart_df['Volume'],
                    name='Volume',
                    marker_color='blue'
                ), row=2, col=1)

                fig.update_layout(
                    title_text=f"Cours en Chandeliers et Volume de {selected_plot_name} ({ticker_to_plot_symbol}) - Période: {selected_period}",
                    xaxis_rangeslider_visible=False,
                    height=600
                )

                fig.update_yaxes(title_text="Prix", row=1, col=1)
                fig.update_yaxes(title_text="Volume", row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True, key="main_candlestick_chart")
            else:
                st.warning(f"Impossible d'afficher le graphique pour {selected_plot_name}. Données manquantes ou vides.")
        else:
            st.warning("Aucune donnée disponible pour les graphiques.")

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

        st.markdown("<hr style='border:1px solid #e0e6ed; margin-top:30px; margin-bottom:30px;'>", unsafe_allow_html=True)
        st.subheader("Accès aux données récentes de l'indice CAC 40")
        
        st.info("Vous pouvez visualiser le cours de l'indice CAC 40 (`^FCHI`) ci-dessous pour la période sélectionnée.")
        if st.button("Afficher le graphique de l'indice CAC 40", key="show_cac40_index_chart"):
            with st.spinner(f"Récupération des données de l'indice CAC 40 pour la période '{selected_period}'..."):
                try:
                    index_data = get_ticker_data('^FCHI', selected_period)
                    if not index_data.empty:
                        if 'Datetime' not in index_data.columns and isinstance(index_data.index, pd.DatetimeIndex):
                            index_data = index_data.reset_index()
                            index_data = index_data.rename(columns={'index': 'Datetime'})
                        
                        if 'Datetime' in index_data.columns and index_data['Datetime'].dtype == 'datetime64[ns, UTC]':
                            index_data['Datetime'] = index_data['Datetime'].dt.tz_localize(None)

                        fig_index = go.Figure(data=[go.Candlestick(
                            x=index_data['Datetime'],
                            open=index_data['Open'],
                            high=index_data['High'],
                            low=index_data['Low'],
                            close=index_data['Close'],
                            name='CAC 40 Index'
                        )])
                        fig_index.update_layout(
                            title=f"Cours de l'indice CAC 40 (^FCHI) - Période: {selected_period}",
                            xaxis_title="Date / Heure",
                            yaxis_title="Points",
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig_index, use_container_width=True, key="cac40_index_chart")
                    else:
                        st.warning("Impossible de récupérer les données de l'indice CAC 40 (^FCHI). Le DataFrame est vide. Cela peut être dû à un intervalle non disponible pour la période sélectionnée.")
                except Exception as e:
                    st.error(f"Erreur lors de la collecte de l'indice CAC 40 : {e}")

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
