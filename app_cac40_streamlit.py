import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from get_cac40_tickers import get_cac40_tickers
import plotly.graph_objects as go
import time
import numpy as np # Pour gérer les NaN

st.set_page_config(page_title="CAC40 Intraday Viewer", layout="wide")
st.title("Suivi en temps réel – CAC 40")

# --- Gestion de la liste des tickers CAC 40 ---
# Rafraîchir la liste dynamique des tickers
if st.button("Rafraîchir la liste CAC 40", key="refresh_tickers_button"):
    st.session_state['tickers_dict'] = get_cac40_tickers()

# Charger depuis cache/session ou initialiser si c'est la première exécution
# Cette ligne est exécutée à chaque rerun de l'app
tickers_dict = st.session_state.get('tickers_dict', get_cac40_tickers())

# Sélection interactive des entreprises à surveiller
selected_companies = st.multiselect(
    "Sélectionne les entreprises à surveiller :",
    list(tickers_dict.keys()),
    default=list(tickers_dict.keys())[:5], # Pré-sélectionne les 5 premières par défaut
    key="multiselect_companies"
)

# --- Bouton pour lancer la collecte des données ---
if st.button("Lancer la collecte des données", key="launch_collection_button"):
    # Obtenir les symboles des tickers à partir des noms sélectionnés
    tickers_symbols_to_collect = [tickers_dict[name] for name in selected_companies]
    
    collected_dfs = [] # Liste pour stocker les DataFrames individuels valides et standardisés
    data_by_ticker = {} # Dictionnaire pour stocker les DataFrames individuels (pour les graphiques séparés)

    st.info(f"Début de la collecte pour {len(tickers_symbols_to_collect)} tickers...")
    print(f"DEBUG_LOG: Début de la collecte pour {len(tickers_symbols_to_collect)} tickers.")

    # Définir les colonnes attendues dans le DataFrame final après le traitement
    # L'ordre est important pour pd.concat si on ne spécifie pas les colonnes à chaque fois (ce qu'on fait ici)
    EXPECTED_COLUMNS = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Ticker']

    # Boucle de collecte pour chaque ticker sélectionné
    for i, ticker_symbol in enumerate(tickers_symbols_to_collect):
        # Tente de retrouver le nom de l'entreprise pour un affichage plus convivial
        company_name = [name for name, symbol in tickers_dict.items() if symbol == ticker_symbol]
        company_display_name = company_name[0] if company_name else ticker_symbol # Utilise le symbole si le nom n'est pas trouvé
        
        st.write(f"Collecte des données pour : **{company_display_name} ({ticker_symbol})** ({i+1}/{len(tickers_symbols_to_collect)})")
        print(f"DEBUG_LOG: Tentative de collecte pour {ticker_symbol} (étape {i+1}/{len(tickers_symbols_to_collect)}).")

        try:
            # Télécharger les données intraday (période "1d", intervalle "1m")
            # FutureWarning: YF.download() has changed argument auto_adjust default to True
            # -> Cette warning est normale et n'est pas un problème.
            data = yf.download(ticker_symbol, period="1d", interval="1m", progress=False)

            if not data.empty:
                # Étape 1: Transformer l'index (qui est la date/heure) en une colonne nommée 'Datetime'
                data = data.reset_index()
                
                # Étape 2: Ajouter la colonne 'Ticker' pour identifier l'entreprise
                data["Ticker"] = ticker_symbol
                
                # Étape 3: Normaliser les noms de colonnes pour qu'ils correspondent à EXPECTED_COLUMNS
                # yfinance retourne souvent 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'
                # Assurez-vous que les premières lettres sont en majuscule, sauf 'Datetime' et 'Ticker'
                new_columns = []
                for col in data.columns:
                    if col not in ['Datetime', 'Ticker']:
                        new_columns.append(col.capitalize())
                    else:
                        new_columns.append(col)
                data.columns = new_columns

                # Étape 4: Créer un DataFrame vide avec la structure EXACTE des colonnes attendues
                processed_data = pd.DataFrame(columns=EXPECTED_COLUMNS)
                
                # Étape 5: Remplir le nouveau DataFrame avec les données et gérer les colonnes manquantes
                for col in EXPECTED_COLUMNS:
                    if col in data.columns:
                        processed_data[col] = data[col]
                    else:
                        # Si une colonne attendue manque (peu probable avec yfinance), ajoutez-la avec NaN
                        processed_data[col] = np.nan 
                        st.warning(f"La colonne '{col}' est manquante pour {ticker_symbol} et a été ajoutée avec des valeurs vides.")

                # Étape 6: S'assurer que le DataFrame final a bien l'ordre des colonnes défini
                processed_data = processed_data[EXPECTED_COLUMNS]
                
                # Étape 7: Ajouter le DataFrame traité à la liste pour la concaténation
                collected_dfs.append(processed_data)
                # Stocker également une copie pour les graphiques individuels si l'utilisateur veut sélectionner
                data_by_ticker[ticker_symbol] = processed_data 

                st.success(f"{company_display_name} ({ticker_symbol}) collecté avec succès. {len(processed_data)} lignes.")
                print(f"DEBUG_LOG: {ticker_symbol} - Données récupérées, {len(processed_data)} lignes.")
            else:
                st.warning(f"Aucune donnée récupérée pour {company_display_name} ({ticker_symbol}). Le DataFrame est vide.")
                print(f"DEBUG_LOG: DataFrame vide pour {ticker_symbol} après yf.download.")

        except Exception as e:
            st.error(f"Erreur lors de la collecte pour {company_display_name} ({ticker_symbol}) : {e}")
            print(f"DEBUG_LOG: Erreur pour {ticker_symbol}: {e}")

        # Ajout d'un délai pour éviter le rate limiting de Yahoo Finance
        time.sleep(1) # Délai de 1 seconde entre chaque requête.

    st.info(f"Fin de la collecte. Nombre de DataFrames valides collectés : {len(collected_dfs)}")
    print(f"DEBUG_LOG: Fin de la boucle de collecte. {len(collected_dfs)} DataFrames validés.")

    # --- Concaténation des DataFrames ---
    if collected_dfs:
        # pd.concat combine les DataFrames. axis=0 est la valeur par défaut pour une concaténation verticale.
        # ignore_index=True réinitialise l'index du DataFrame final (de 0 à N-1)
        # pour éviter les index dupliqués des DataFrames sources.
        df_final = pd.concat(collected_dfs, ignore_index=True)
        
        st.session_state['full_df'] = df_final # Sauvegarder le DataFrame combiné en session
        st.session_state['data_by_ticker'] = data_by_ticker # Sauvegarder les DataFrames individuels en session

        st.write("--- Résumé des données agrégées ---")
        st.write(f"Nombre total de lignes dans le DataFrame final : {len(df_final)}")
        st.write("Distribution des tickers dans le DataFrame final :")
        # Affiche le nombre de lignes pour chaque ticker dans le DataFrame final
        st.dataframe(df_final['Ticker'].value_counts()) 
        st.write("Aperçu des premières lignes du DataFrame final :")

        # Affiche les 20 premières lignes du DataFrame final pour vérifier la concaténation verticale
        st.dataframe(df_final.head(20)) 

        # --- Section Graphiques Détaillés ---
        st.subheader("Graphiques Intraday Détaillés")
        if data_by_ticker:
            # Préparer les options pour le selectbox (nom de l'entreprise)
            ticker_display_names_map = {v: k for k, v in tickers_dict.items()}
            plot_selection_options = sorted([ticker_display_names_map.get(s, s) for s in data_by_ticker.keys()])

            selected_plot_name = st.selectbox(
                "Sélectionne l'entreprise pour le graphique :",
                plot_selection_options,
                key="main_plot_select"
            )
            # Retrouver le symbole du ticker à partir du nom sélectionné pour récupérer le bon DataFrame
            ticker_to_plot_symbol = tickers_dict.get(selected_plot_name, selected_plot_name) # Fallback si le nom ne matche pas un symbole

            chart_df = data_by_ticker.get(ticker_to_plot_symbol)

            if chart_df is not None and not chart_df.empty:
                # Création du graphique en chandeliers avec Plotly
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
                    xaxis_rangeslider_visible=False # Cache le range slider pour un affichage plus clair
                )
                st.plotly_chart(fig, use_container_width=True, key="main_candlestick_chart")
            else:
                st.warning(f"Impossible d'afficher le graphique pour {selected_plot_name}. Données manquantes ou vides.")
        else:
            st.warning("Aucune donnée disponible pour les graphiques après la collecte.")

        # --- Bouton d'Export CSV ---
        csv = df_final.to_csv(index=False).encode("utf-8")
        st.download_button(
            "💾 Télécharger CSV",
            csv,
            f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            key="main_csv_download"
        )
    else:
        st.warning("Aucune donnée du CAC 40 n'a pu être récupérée pour les entreprises sélectionnées.")

# --- Section pour l'affichage des données en cache (si déjà collectées) ---
# Ceci permet d'interagir avec les graphiques et le CSV sans relancer la collecte à chaque fois
if 'full_df' in st.session_state and 'data_by_ticker' in st.session_state:
    st.subheader("Graphiques Intraday Détaillés (Données en cache)")
    data_by_ticker_cached = st.session_state['data_by_ticker'] 
    
    if data_by_ticker_cached:
        ticker_display_names_map = {v: k for k, v in tickers_dict.items()}
        plot_selection_options_cached = sorted([ticker_display_names_map.get(s, s) for s in data_by_ticker_cached.keys()])

        selected_plot_name_cached = st.selectbox(
            "Sélectionne l'entreprise pour le graphique (Données en cache) :",
            plot_selection_options_cached,
            key="cached_plot_select"
        )
        ticker_to_plot_symbol_cached = tickers_dict.get(selected_plot_name_cached, selected_plot_name_cached)

        chart_df_cached = data_by_ticker_cached.get(ticker_to_plot_symbol_cached)

        if chart_df_cached is not None and not chart_df_cached.empty:
            fig_cached = go.Figure(data=[go.Candlestick(
                x=chart_df_cached['Datetime'],
                open=chart_df_cached['Open'],
                high=chart_df_cached['High'],
                low=chart_df_cached['Low'],
                close=chart_df_cached['Close'],
                name='Prix'
            )])
            fig_cached.update_layout(
                title=f"Cours Intraday en Chandeliers de {selected_plot_name_cached} ({ticker_to_plot_symbol_cached})",
                xaxis_title="Heure",
                yaxis_title="Prix",
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig_cached, use_container_width=True, key="cached_candlestick_chart")
        else:
            st.warning(f"Impossible d'afficher le graphique pour {selected_plot_name_cached}. Données manquantes ou vides.")
    else:
        st.warning("Aucune donnée disponible en cache pour les graphiques.")

    csv_cached = st.session_state['full_df'].to_csv(index=False).encode("utf-8")
    st.download_button(
        "💾 Télécharger CSV (Données en cache)",
        csv_cached,
        f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}_cached.csv",
        key="cached_csv_download"
    )
