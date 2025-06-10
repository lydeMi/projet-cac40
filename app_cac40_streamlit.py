import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from get_cac40_tickers import get_cac40_tickers # Importe votre script local
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# --- Configuration de la page ---
st.set_page_config(
    page_title="CAC40 Tracker Pro",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈"
)

# --- CSS Personnalisé avancé ---
st.markdown("""
    <style>
    /* Masquer les éléments Streamlit par défaut */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Importation des polices Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Variables CSS pour cohérence */
    :root {
        --primary-color: #2563eb;
        --secondary-color: #1e40af;
        --success-color: #059669;
        --warning-color: #d97706;
        --error-color: #dc2626;
        --background-color: #f8fafc;
        --card-background: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border-color: #e2e8f0;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    /* Style global */
    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: var(--background-color);
        color: var(--text-primary);
    }

    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.025em;
        margin-bottom: 1rem;
    }

    h1 {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
    }

    /* Conteneurs de métriques */
    .metric-container {
        background: var(--card-background);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
        text-align: center;
        transition: all 0.2s ease;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 500;
    }

    /* Indicateurs de statut */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem 0.25rem 0.25rem 0;
        gap: 0.5rem;
    }

    .status-success {
        background-color: rgba(5, 150, 105, 0.1);
        color: var(--success-color);
        border: 1px solid rgba(5, 150, 105, 0.2);
    }

    .status-warning {
        background-color: rgba(217, 119, 6, 0.1);
        color: var(--warning-color);
        border: 1px solid rgba(217, 119, 6, 0.2);
    }

    .status-error {
        background-color: rgba(220, 38, 38, 0.1);
        color: var(--error-color);
        border: 1px solid rgba(220, 38, 38, 0.2);
    }

    /* Onglets améliorés */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 2rem;
        border-bottom: 2px solid var(--border-color);
        padding: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        padding: 0 24px;
        border-radius: 8px 8px 0 0;
        background-color: transparent;
        color: var(--text-secondary);
        font-weight: 500;
        border: none;
        border-bottom: 3px solid transparent;
        transition: all 0.2s ease;
        font-size: 1rem;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(37, 99, 235, 0.05);
        color: var(--primary-color);
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--card-background);
        color: var(--primary-color);
        border-bottom: 3px solid var(--primary-color);
        font-weight: 600;
        box-shadow: var(--shadow);
    }

    /* Boutons améliorés */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 16px -4px rgba(37, 99, 235, 0.3);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Conteneurs personnalisés */
    .custom-container {
        background: var(--card-background);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
    }

    .info-card {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.05), rgba(30, 64, 175, 0.05));
        border: 1px solid rgba(37, 99, 235, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Indicateurs de qualité des données */
    .data-quality-excellent { color: var(--success-color); font-weight: 700; }
    .data-quality-good { color: #16a34a; font-weight: 600; }
    .data-quality-medium { color: var(--warning-color); font-weight: 600; }
    .data-quality-poor { color: var(--error-color); font-weight: 600; }

    /* Sidebar personnalisée */
    .css-1d391kg {
        background-color: var(--card-background);
        border-right: 1px solid var(--border-color);
    }

    /* Selectbox et Multiselect */
    .stSelectbox > div > div > div, .stMultiSelect > div > div > div {
        border-radius: 8px;
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }

    .stSelectbox > div > div > div:focus-within, .stMultiSelect > div > div > div:focus-within {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    /* Animation de chargement */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    .loading-pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        border-radius: 4px;
    }

    /* Alertes personnalisées */
    .stAlert > div {
        border-radius: 8px;
        border: 1px solid;
        font-weight: 500;
    }

    /* DataFrames */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
    }

    /* Text inputs */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- Fonctions Utilitaires ---
def calculate_data_quality(df):
    """Calcule la qualité des données basée sur la complétude et la fraîcheur"""
    if df.empty:
        return 0, "Aucune donnée", "data-quality-poor"
    
    # Calcul de la complétude
    total_cells = len(df) * len(df.columns)
    missing_cells = df.isnull().sum().sum()
    completeness = ((total_cells - missing_cells) / total_cells) * 100
    
    # Classification de la qualité
    if completeness >= 98:
        return completeness, "Excellente", "data-quality-excellent"
    elif completeness >= 90:
        return completeness, "Bonne", "data-quality-good"
    elif completeness >= 70:
        return completeness, "Moyenne", "data-quality-medium"
    else:
        return completeness, "Faible", "data-quality-poor"

def format_number(num, prefix="", suffix=""):
    """Formate les grands nombres avec des suffixes appropriés"""
    if pd.isna(num) or num is None:
        return "N/A"
    
    if abs(num) >= 1e12: # Trillions
        return f"{prefix}{num/1e12:.2f}T{suffix}"
    elif abs(num) >= 1e9: # Billions
        return f"{prefix}{num/1e9:.2f}Md{suffix}"
    elif abs(num) >= 1e6: # Millions
        return f"{prefix}{num/1e6:.2f}M{suffix}"
    elif abs(num) >= 1e3: # Thousands
        return f"{prefix}{num/1e3:.2f}K{suffix}"
    else:
        return f"{prefix}{num:.2f}{suffix}"

def format_percentage(value, decimals=2):
    """Formate un pourcentage avec couleur"""
    if pd.isna(value):
        return "N/A"
    
    color = "green" if value >= 0 else "red"
    sign = "+" if value >= 0 else ""
    return f"<span style='color: {color}; font-weight: 600;'>{sign}{value:.{decimals}f}%</span>"

def get_ticker_data_enhanced(ticker_symbol, period):
    """Collecte de données améliorée avec gestion d'erreurs et informations supplémentaires"""
    try:
        # Mapping des intervalles optimaux
        interval_mapping = {
            "1d": "2m", "5d": "5m", "1mo": "30m", 
            "3mo": "1h", "6mo": "1d", "1y": "1d",
            "2y": "1wk", "5y": "1wk", "10y": "1mo", 
            "ytd": "1d", "max": "1mo"
        }
        interval_val = interval_mapping.get(period, "1d")
        
        # Création de l'objet ticker
        ticker = yf.Ticker(ticker_symbol)
        
        # Téléchargement des données historiques
        data = ticker.history(period=period, interval=interval_val, auto_adjust=True, prepost=True)
        
        if not data.empty:
            # Reset de l'index pour avoir Datetime comme colonne
            data = data.reset_index()
            # Renommer la colonne 'Datetime' si elle existe, sinon 'Date'
            if 'Datetime' in data.columns:
                data.rename(columns={'Datetime': 'Date'}, inplace=True)
            data['Ticker'] = ticker_symbol
            
            # Tentative de récupération des informations de l'entreprise
            try:
                info = ticker.info
                company_name = info.get('longName', info.get('shortName', ticker_symbol))
                sector = info.get('sector', 'Non spécifié')
                market_cap = info.get('marketCap', None)
                currency = info.get('currency', 'EUR')
                
                # Ajout des informations au DataFrame
                data['Company_Name'] = company_name
                data['Sector'] = sector
                data['Market_Cap'] = market_cap
                data['Currency'] = currency
                
            except Exception as info_error:
                # Valeurs par défaut en cas d'erreur
                data['Company_Name'] = ticker_symbol
                data['Sector'] = 'Non spécifié'
                data['Market_Cap'] = None
                data['Currency'] = 'EUR'
            
            # Ajout d'indicateurs techniques
            data = add_technical_indicators(data)
            
            return ticker_symbol, data, None
            
    except Exception as e:
        return ticker_symbol, pd.DataFrame(), str(e)

def add_technical_indicators(df):
    """Ajoute des indicateurs techniques au DataFrame"""
    if df.empty or len(df) < 2:
        return df
    
    try:
        # Moyennes mobiles
        if len(df) >= 10:
            df['MA_10'] = df['Close'].rolling(window=10, min_periods=1).mean()
        if len(df) >= 20:
            df['MA_20'] = df['Close'].rolling(window=20, min_periods=1).mean()
        if len(df) >= 50:
            df['MA_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
        
        # RSI (Relative Strength Index)
        if len(df) >= 14:
            delta = df['Close'].diff()
            # Pour éviter la division par zéro dans le cas où loss est 0
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            
            # Gestion de la division par zéro pour RS
            rs = np.where(loss == 0, np.inf, gain / loss)
            df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        if len(df) >= 26:
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Bandes de Bollinger
        if len(df) >= 20:
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            
    except Exception as e:
        st.warning(f"Erreur lors du calcul des indicateurs techniques: {e}")
        # S'assurer que les colonnes sont créées même en cas d'erreur pour éviter des KeyError plus tard
        for col in ['MA_10', 'MA_20', 'MA_50', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Histogram', 'BB_Middle', 'BB_Upper', 'BB_Lower']:
            if col not in df.columns:
                df[col] = np.nan
    
    return df

def collect_data_parallel(tickers_to_collect, period, max_workers=5):
    """Collecte les données en parallèle pour améliorer les performances"""
    collected_data = {}
    errors = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumission de tous les jobs
        future_to_ticker = {
            executor.submit(get_ticker_data_enhanced, ticker, period): ticker 
            for ticker in tickers_to_collect
        }
        
        # Récupération des résultats
        for future in as_completed(future_to_ticker):
            ticker_symbol, data, error = future.result()
            
            if error:
                errors.append((ticker_symbol, error))
            elif not data.empty:
                collected_data[ticker_symbol] = data
            else:
                errors.append((ticker_symbol, "Aucune donnée disponible"))
    
    return collected_data, errors

# --- Application Principale ---
st.title("📈 CAC 40 Tracker Pro")
st.markdown("*Suivi avancé et analyse en temps réel des valeurs du CAC 40*")

# --- Sidebar pour les contrôles ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Actualisation des tickers CAC 40
    if st.button("🔄 Actualiser CAC 40", use_container_width=True):
        with st.spinner("Actualisation en cours..."):
            try:
                st.session_state['tickers_dict'] = get_cac40_tickers()
                st.success("✅ Liste CAC 40 actualisée !")
            except Exception as e:
                st.error(f"❌ Erreur lors de l'actualisation: {e}")
    
    # Initialisation des tickers
    if 'tickers_dict' not in st.session_state:
        try:
            st.session_state['tickers_dict'] = get_cac40_tickers()
        except Exception as e:
            st.error(f"Erreur lors du chargement des tickers: {e}")
            st.session_state['tickers_dict'] = {}
    
    tickers_dict = st.session_state.get('tickers_dict', {})
    
    if tickers_dict:
        st.success(f"✅ {len(tickers_dict)} entreprises chargées")
    else:
        st.warning("⚠️ Aucune entreprise chargée")
    
    st.markdown("---")
    
    # Sélection de la période
    st.subheader("📅 Période d'Analyse")
    period_options = {
        "1 jour": "1d", "5 jours": "5d", "1 mois": "1mo", 
        "3 mois": "3mo", "6 mois": "6mo", "1 an": "1y",
        "2 ans": "2y", "5 ans": "5y", "Maximum": "max"
    }
    selected_period_label = st.selectbox("Sélectionnez la période:", list(period_options.keys()), index=2)
    selected_period = period_options[selected_period_label]
    
    st.markdown("---")
    
    # Sélection des entreprises avec recherche et filtre par secteur
    st.subheader("🏢 Sélection des Entreprises")
    
    if tickers_dict:
        # Récupérer tous les secteurs disponibles (hypothèse : si get_cac40_tickers ou la première collecte fournit le secteur)
        # Pour une meilleure robustesse, cette partie pourrait être pré-collectée une fois.
        all_sectors = []
        if 'collected_data' in st.session_state and st.session_state['collected_data']:
            for df_val in st.session_state['collected_data'].values():
                if 'Sector' in df_val.columns and not df_val.empty:
                    all_sectors.append(df_val['Sector'].iloc[0])
        all_sectors = sorted(list(set(all_sectors)))
        
        selected_sectors = st.multiselect(
            "Filtrer par secteur:",
            ['Tous'] + all_sectors,
            default=['Tous']
        )

        search_term = st.text_input("🔍 Rechercher", placeholder="Tapez le nom d'une entreprise...")
        
        all_companies_names = list(tickers_dict.keys())
        filtered_companies_by_search = [name for name in all_companies_names if search_term.lower() in name.lower()]

        # Filtrer davantage par secteur si "Tous" n'est pas sélectionné
        if 'Tous' not in selected_sectors and all_sectors:
            companies_in_selected_sectors = []
            if 'collected_data' in st.session_state and st.session_state['collected_data']:
                for company_name, ticker_symbol in tickers_dict.items():
                    if ticker_symbol in st.session_state['collected_data']:
                        df_info = st.session_state['collected_data'][ticker_symbol]
                        if not df_info.empty and 'Sector' in df_info.columns and df_info['Sector'].iloc[0] in selected_sectors:
                            companies_in_selected_sectors.append(company_name)
            
            # Intersection des deux filtres (recherche et secteur)
            filtered_companies = list(set(filtered_companies_by_search) & set(companies_in_selected_sectors))
        else:
            filtered_companies = filtered_companies_by_search

        # Pré-sélection par défaut si aucune n'est sélectionnée et filtre actif
        default_selection = []
        if not st.session_state.get('initial_company_selection_done', False) or not selected_companies:
            # Avoid re-selecting defaults if already selected by user
            if filtered_companies:
                default_selection = filtered_companies[:5] # Select first 5 filtered companies by default
                st.session_state['initial_company_selection_done'] = True

        selected_companies = st.multiselect(
            "Entreprises à analyser:",
            filtered_companies,
            default=default_selection,
            help=f"{len(filtered_companies)} entreprises disponibles après filtre"
        )
        
        # Affichage du nombre sélectionné
        if selected_companies:
            st.info(f"📊 {len(selected_companies)} entreprise(s) sélectionnée(s)")
        else:
            st.warning("⚠️ Aucune entreprise sélectionnée")
    else:
        st.error("❌ Impossible de charger la liste des entreprises")
        selected_companies = []
    
    st.markdown("---")
    
    # Paramètres de collecte
    st.subheader("⚡ Paramètres de Collecte")
    max_workers = st.slider(
        "Threads parallèles:", 
        min_value=1, 
        max_value=10, 
        value=5,
        help="Plus de threads = collecte plus rapide (mais plus de charge sur l'API)"
    )
    
    # Options avancées
    with st.expander("🔧 Options Avancées"):
        include_indicators = st.checkbox("Inclure les indicateurs techniques", value=True)
        auto_refresh = st.checkbox("Actualisation automatique (5 min)", value=False)
        if auto_refresh:
            st.info("🔄 L'actualisation automatique est activée")

# --- Onglets principaux ---
tab1, tab2, tab3 = st.tabs(["📊 Analyse Temps Réel", "📈 Vue d'Ensemble CAC 40", "🔬 Analyse Technique Détaillée"])

# --- Onglet 1: Analyse Temps Réel ---
with tab1:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("📊 Analyse en Temps Réel")
        st.markdown(f"*Données pour la période: **{selected_period_label}** • Indicateurs techniques: {'✅' if include_indicators else '❌'}*")
    
    with col2:
        # Bouton de collecte principal
        collect_button = st.button(
            "🚀 Lancer l'Analyse", 
            use_container_width=True, 
            type="primary",
            disabled=not selected_companies
        )
    
    # Gestion de la collecte des données
    if collect_button:
        if not selected_companies:
            st.error("⚠️ Veuillez sélectionner au moins une entreprise")
        else:
            # Préparation de la collecte
            tickers_to_collect = [tickers_dict[name] for name in selected_companies if name in tickers_dict]
            
            # Interface de progression
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with progress_placeholder.container():
                st.info(f"🔄 Démarrage de la collecte pour {len(tickers_to_collect)} valeurs...")
                progress_bar = st.progress(0)
            
            # Collecte parallèle des données
            start_time = time.time()
            
            try:
                with status_placeholder.container():
                    st.info("📡 Collecte des données en cours...")
                
                collected_data, collection_errors = collect_data_parallel(
                    tickers_to_collect, 
                    selected_period, 
                    max_workers
                )
                
                collection_time = time.time() - start_time
                progress_bar.progress(1.0)
                
                # Stockage des résultats dans la session
                st.session_state['collected_data'] = collected_data
                st.session_state['collection_errors'] = collection_errors
                st.session_state['collection_time'] = collection_time
                st.session_state['collection_timestamp'] = datetime.now()
                
                # Nettoyage de l'interface
                progress_placeholder.empty()
                
                # Message de succès avec statistiques
                if collected_data:
                    total_rows = sum(len(df) for df in collected_data.values())
                    success_rate = (len(collected_data) / len(tickers_to_collect)) * 100
                    
                    status_placeholder.success(
                        f"✅ Collecte terminée: {len(collected_data)}/{len(tickers_to_collect)} valeurs "
                        f"({success_rate:.1f}% succès) • {total_rows:,} points de données • "
                        f"Temps: {collection_time:.1f}s"
                    )
                    
                    # Affichage des erreurs s'il y en a
                    if collection_errors:
                        with st.expander(f"⚠️ Erreurs de collecte ({len(collection_errors)})"):
                            for ticker, error in collection_errors:
                                company_name = [k for k, v in tickers_dict.items() if v == ticker]
                                display_name = company_name[0] if company_name else ticker
                                st.warning(f"**{display_name} ({ticker})**: {error}")
                else:
                    status_placeholder.error("❌ Aucune donnée collectée. Vérifiez votre connexion internet.")
                    
            except Exception as e:
                progress_placeholder.empty()
                status_placeholder.error(f"❌ Erreur lors de la collecte: {e}")
    
    # Affichage des données collectées
    if 'collected_data' in st.session_state and st.session_state['collected_data']:
        st.markdown("---")
        
        collected_data = st.session_state['collected_data']
        collection_time = st.session_state.get('collection_time', 0)
        collection_timestamp = st.session_state.get('collection_timestamp', datetime.now())
        
        # Métriques de résumé
        st.subheader("📊 Résumé de la Collecte")
        
        # Calcul des statistiques globales
        total_rows = sum(len(df) for df in collected_data.values())
        quality_scores = [calculate_data_quality(df)[0] for df in collected_data.values()]
        avg_quality = np.mean(quality_scores) if quality_scores else 0
        
        # Affichage des métriques en colonnes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{len(collected_data)}</div>
                    <div class="metric-label">Valeurs Collectées</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{total_rows:,}</div>
                    <div class="metric-label">Points de Données</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            quality_class = ("excellent" if avg_quality >= 95 else 
                             "good" if avg_quality >= 80 else 
                             "medium" if avg_quality >= 60 else "poor")
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value data-quality-{quality_class}">{avg_quality:.1f}%</div>
                    <div class="metric-label">Qualité Moyenne</div>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{collection_time:.1f}s</div>
                    <div class="metric-label">Temps de Collecte</div>
                </div>
            """, unsafe_allow_html=True)
            
        # Informations sur la dernière mise à jour
        st.markdown(f"""
            <div class="info-card">
                <p><strong>📅 Dernière mise à jour:</strong> {collection_timestamp.strftime('%d/%m/%Y à %H:%M:%S')}</p>
                <p><strong>⏱️ Période analysée:</strong> {selected_period_label} • <strong>🔧 Threads utilisés:</strong> {max_workers}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Section de visualisation avancée
        st.subheader("📈 Visualisation Interactive")
        
        # Sélection de la valeur à analyser
        ticker_names = {v: k for k, v in tickers_dict.items()}
        available_tickers = list(collected_data.keys())
        display_names = [ticker_names.get(t, t) for t in available_tickers]
        
        col1_viz, col2_viz = st.columns([2, 1])
        with col1_viz:
            selected_display = st.selectbox(
                "Sélectionner une valeur pour l'analyse détaillée:", 
                display_names, 
                key="viz_select"
            )
        
        with col2_viz:
            chart_type = st.selectbox(
                "Type de graphique:",
                ["Chandelier + Volume", "Prix + Indicateurs", "Comparaison Multiple"],
                key="chart_type_select"
            )
        
        selected_ticker = tickers_dict.get(selected_display, selected_display)

        # --- Plotting Logic for tab1 ---
        if selected_ticker and selected_ticker in collected_data:
            df_single = collected_data[selected_ticker]
            company_name = df_single['Company_Name'].iloc[0] if 'Company_Name' in df_single.columns and not df_single.empty else selected_display

            if chart_type == "Chandelier + Volume":
                st.subheader(f"🕯️ Chandelier et Volume pour {company_name}")
                if not df_single.empty:
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                        vertical_spacing=0.1,
                                        row_heights=[0.7, 0.3])
                    fig.add_trace(go.Candlestick(x=df_single['Date'],
                                                 open=df_single['Open'],
                                                 high=df_single['High'],
                                                 low=df_single['Low'],
                                                 close=df_single['Close'],
                                                 name='Candlestick'), row=1, col=1)
                    if include_indicators:
                        if 'MA_10' in df_single.columns and not df_single['MA_10'].isnull().all():
                            fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['MA_10'], mode='lines', name='MA 10', line=dict(color='orange', width=1)), row=1, col=1)
                        if 'MA_20' in df_single.columns and not df_single['MA_20'].isnull().all():
                            fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['MA_20'], mode='lines', name='MA 20', line=dict(color='purple', width=1)), row=1, col=1)
                        if 'MA_50' in df_single.columns and not df_single['MA_50'].isnull().all():
                            fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['MA_50'], mode='lines', name='MA 50', line=dict(color='red', width=1.5)), row=1, col=1)
                        if 'BB_Upper' in df_single.columns and 'BB_Lower' in df_single.columns and not df_single['BB_Upper'].isnull().all():
                             fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['BB_Upper'], mode='lines', name='BB Upper', line=dict(color='blue', width=1, dash='dot')), row=1, col=1)
                             fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['BB_Lower'], mode='lines', name='BB Lower', line=dict(color='blue', width=1, dash='dot')), row=1, col=1)


                    fig.add_trace(go.Bar(x=df_single['Date'], y=df_single['Volume'], name='Volume', marker_color='rgba(0,100,200,0.8)'), row=2, col=1)
                    fig.update_layout(xaxis_rangeslider_visible=False, title_text=f"Cours et Volume - {company_name}", height=600)
                    fig.update_yaxes(title_text="Cours", row=1, col=1)
                    fig.update_yaxes(title_text="Volume", row=2, col=1)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Pas de données disponibles pour le graphique en chandelier.")

            elif chart_type == "Prix + Indicateurs":
                st.subheader(f"📈 Prix et Indicateurs Techniques pour {company_name}")
                if not df_single.empty and include_indicators:
                    plot_rows_indicators = 1 # Start with Close price
                    if 'RSI' in df_single.columns and not df_single['RSI'].isnull().all(): plot_rows_indicators += 1
                    if 'MACD' in df_single.columns and not df_single['MACD'].isnull().all(): plot_rows_indicators += 1

                    fig = make_subplots(rows=plot_rows_indicators, cols=1, shared_xaxes=True,
                                        vertical_spacing=0.1,
                                        row_titles=["Prix de Clôture & Moyennes Mobiles", "RSI (Relative Strength Index)", "MACD (Moving Average Convergence Divergence)"][:plot_rows_indicators])
                    
                    current_row_indicator = 1
                    # Prix
                    fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['Close'], mode='lines', name='Prix Clôture', line=dict(color='blue')), row=current_row_indicator, col=1)
                    if 'MA_10' in df_single.columns and not df_single['MA_10'].isnull().all():
                        fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['MA_10'], mode='lines', name='MA 10', line=dict(color='orange')), row=current_row_indicator, col=1)
                    if 'MA_20' in df_single.columns and not df_single['MA_20'].isnull().all():
                        fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['MA_20'], mode='lines', name='MA 20', line=dict(color='purple')), row=current_row_indicator, col=1)
                    if 'MA_50' in df_single.columns and not df_single['MA_50'].isnull().all():
                        fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['MA_50'], mode='lines', name='MA 50', line=dict(color='red')), row=current_row_indicator, col=1)
                    if 'BB_Upper' in df_single.columns and 'BB_Lower' in df_single.columns and not df_single['BB_Upper'].isnull().all():
                         fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['BB_Upper'], mode='lines', name='BB Upper', line=dict(color='blue', dash='dot')), row=current_row_indicator, col=1)
                         fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['BB_Lower'], mode='lines', name='BB Lower', line=dict(color='blue', dash='dot')), row=current_row_indicator, col=1)
                    fig.update_yaxes(title_text="Prix", row=current_row_indicator, col=1)
                    current_row_indicator += 1

                    # RSI
                    if 'RSI' in df_single.columns and not df_single['RSI'].isnull().all():
                        fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['RSI'], mode='lines', name='RSI', line=dict(color='green')), row=current_row_indicator, col=1)
                        fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row_indicator, col=1, annotation_text="Surachat", annotation_position="top right")
                        fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row_indicator, col=1, annotation_text="Survente", annotation_position="bottom right")
                        fig.update_yaxes(title_text="RSI", row=current_row_indicator, col=1)
                        current_row_indicator += 1

                    # MACD
                    if 'MACD' in df_single.columns and 'MACD_Signal' in df_single.columns and 'MACD_Histogram' in df_single.columns and not df_single['MACD'].isnull().all():
                        fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['MACD'], mode='lines', name='MACD', line=dict(color='blue')), row=current_row_indicator, col=1)
                        fig.add_trace(go.Scatter(x=df_single['Date'], y=df_single['MACD_Signal'], mode='lines', name='Signal', line=dict(color='red')), row=current_row_indicator, col=1)
                        # Ensure marker_color logic is robust for empty or single-value histograms
                        marker_colors = ['green' if val >= 0 else 'red' for val in df_single['MACD_Histogram']] if not df_single['MACD_Histogram'].empty else []
                        fig.add_trace(go.Bar(x=df_single['Date'], y=df_single['MACD_Histogram'], name='Histogram', marker_color=marker_colors), row=current_row_indicator, col=1)
                        fig.update_yaxes(title_text="MACD", row=current_row_indicator, col=1)
                        current_row_indicator += 1
                        
                    fig.update_layout(xaxis_rangeslider_visible=False, title_text=f"Cours et Indicateurs Techniques - {company_name}", height=plot_rows_indicators * 250, showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Pas de données ou indicateurs techniques non inclus pour ce graphique.")
            elif chart_type == "Comparaison Multiple":
                st.subheader(f"📈 Comparaison de l'Évolution Normalisée")
                if collected_data:
                    comparison_df = pd.DataFrame()
                    for ticker_sym, df_comp in collected_data.items():
                        if not df_comp.empty and 'Close' in df_comp.columns:
                            # Normalisation pour comparer les évolutions
                            initial_price = df_comp['Close'].iloc[0]
                            if initial_price != 0:
                                # Ensure 'Date' column is used for index alignment
                                temp_series = (df_comp['Close'] / initial_price - 1) * 100
                                temp_series.index = df_comp['Date']
                                comparison_df[ticker_names.get(ticker_sym, ticker_sym)] = temp_series
                            else:
                                temp_series = pd.Series(0, index=df_comp['Date'])
                                comparison_df[ticker_names.get(ticker_sym, ticker_sym)] = temp_series

                    if not comparison_df.empty:
                        # Ensure 'Date' column is present for plotting
                        if 'Date' not in comparison_df.columns:
                            comparison_df = comparison_df.reset_index().rename(columns={'index': 'Date'})

                        fig = px.line(comparison_df, x='Date', y=[col for col in comparison_df.columns if col != 'Date'],
                                      title="Évolution Normalisée des Prix (%)",
                                      labels={'value': 'Changement (%)', 'variable': 'Entreprise'},
                                      line_shape='linear')
                        fig.update_layout(hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Pas assez de données pour la comparaison multiple.")
                else:
                    st.info("Veuillez collecter les données pour voir la comparaison.")
        else:
            if selected_companies: # Only show this if data collection is pending but companies are selected
                st.info("Cliquez sur '🚀 Lancer l'Analyse' pour afficher les graphiques.")
            else:
                st.info("Sélectionnez des entreprises dans la barre latérale pour commencer l'analyse.")


# --- Onglet 2: Vue d'Ensemble CAC 40 ---
with tab2:
    import plotly.express as px # Import here to avoid circular dependencies if get_cac40_tickers also used it

    st.header("🌍 Vue d'Ensemble du CAC 40")
    st.markdown("Aperçu des performances globales et des statistiques clés des entreprises sélectionnées.")

    if 'collected_data' in st.session_state and st.session_state['collected_data']:
        overview_data = []
        for ticker_sym, df_val in st.session_state['collected_data'].items():
            if not df_val.empty:
                latest_data = df_val.iloc[-1]
                first_data = df_val.iloc[0]

                company_name = df_val['Company_Name'].iloc[0] if 'Company_Name' in df_val.columns else ticker_names.get(ticker_sym, ticker_sym)
                sector = df_val['Sector'].iloc[0] if 'Sector' in df_val.columns else 'Non spécifié'
                market_cap = df_val['Market_Cap'].iloc[0] if 'Market_Cap' in df_val.columns else None
                currency = df_val['Currency'].iloc[0] if 'Currency' in df_val.columns else 'EUR'
                
                # Handling potential division by zero for price change
                price_change = latest_data['Close'] - first_data['Open'] if not pd.isna(latest_data['Close']) and not pd.isna(first_data['Open']) else np.nan
                percentage_change = (price_change / first_data['Open']) * 100 if first_data['Open'] != 0 and not pd.isna(first_data['Open']) else np.nan
                
                overview_data.append({
                    'Entreprise': company_name,
                    'Ticker': ticker_sym,
                    'Secteur': sector,
                    'Dernier Prix': latest_data['Close'] if 'Close' in latest_data else np.nan,
                    'Changement': price_change,
                    'Changement %': percentage_change,
                    'Volume Moyen': df_val['Volume'].mean() if 'Volume' in df_val.columns else np.nan,
                    'Capitalisation Boursière': market_cap,
                    'Devise': currency,
                    'Date Dernière Donnée': latest_data['Date'].strftime('%Y-%m-%d') if 'Date' in latest_data else 'N/A'
                })
        
        if overview_data:
            df_overview = pd.DataFrame(overview_data)
            
            # Formattage des colonnes numériques pour l'affichage
            df_overview['Dernier Prix'] = df_overview['Dernier Prix'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
            df_overview['Changement'] = df_overview['Changement'].apply(lambda x: f"{x:+.2f}" if pd.notna(x) else "N/A")
            df_overview['Changement %'] = df_overview['Changement %'].apply(lambda x: format_percentage(x))
            df_overview['Volume Moyen'] = df_overview['Volume Moyen'].apply(lambda x: format_number(x, suffix="") if pd.notna(x) else "N/A")
            
            # Special handling for Market_Cap as it depends on Currency
            df_overview['Capitalisation Boursière Display'] = df_overview.apply(
                lambda row: format_number(row['Capitalisation Boursière'], suffix=f" {row['Devise']}" if pd.notna(row['Capitalisation Boursière']) else ""), axis=1
            )
            
            st.subheader("Résumé des Performances")
            # Display DataFrame with HTML formatting for percentage
            # Select columns to display, hiding raw Market_Cap and Devise
            display_cols = [col for col in df_overview.columns if col not in ['Capitalisation Boursière', 'Devise']]
            st.dataframe(df_overview[display_cols].to_html(escape=False, index=False), use_container_width=True, height=500)
            
            st.markdown("---")
            
            # --- Visualisations globales ---
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("Distribution par Secteur")
                # Filter out 'Non spécifié' if it's the only value or too dominant
                sector_counts = df_overview['Secteur'].value_counts().reset_index()
                sector_counts.columns = ['Secteur', 'Nombre d\'entreprises']
                
                if not sector_counts.empty:
                    fig_sector_pie = px.pie(sector_counts, names='Secteur', values='Nombre d\'entreprises',
                                            title='Répartition des Entreprises par Secteur',
                                            hole=0.3)
                    st.plotly_chart(fig_sector_pie, use_container_width=True)
                else:
                    st.info("Pas de données de secteur disponibles pour le graphique.")


            with col_chart2:
                st.subheader("Capitalisation Boursière par Entreprise")
                # Need to convert back Market_Cap to numeric for plotting
                df_plot_mc = df_overview[df_overview['Capitalisation Boursière'].notna()].copy()
                if not df_plot_mc.empty:
                    # Convert to numeric, handle potential string suffixes if format_number was applied earlier
                    df_plot_mc['Capitalisation Boursière_num'] = df_plot_mc['Capitalisation Boursière'].astype(float) # Assuming it's still numeric before display formatting

                    # Filter out None/NaN values for plotting
                    df_plot_mc_filtered = df_plot_mc[df_plot_mc['Capitalisation Boursière_num'].notna()]
                    
                    if not df_plot_mc_filtered.empty:
                        fig_mc_bar = px.bar(df_plot_mc_filtered.sort_values('Capitalisation Boursière_num', ascending=False), 
                                            x='Entreprise', y='Capitalisation Boursière_num',
                                            title='Capitalisation Boursière (en Millions/Milliards)',
                                            labels={'Capitalisation Boursière_num': 'Capitalisation Boursière'},
                                            color='Secteur')
                        fig_mc_bar.update_yaxes(tickformat=".2s") # Format y-axis to show M, B for millions, billions
                        st.plotly_chart(fig_mc_bar, use_container_width=True)
                    else:
                        st.info("Pas de données de capitalisation boursière disponibles pour le graphique.")
                else:
                    st.info("Pas de données de capitalisation boursière disponibles pour le graphique.")
                
        else:
            st.info("Aucune donnée disponible pour la vue d'ensemble. Veuillez collecter les données d'abord.")
    else:
        st.info("Aucune donnée collectée pour le CAC 40. Lancez l'analyse dans l'onglet 'Analyse Temps Réel'.")


# --- Onglet 3: Analyse Technique Détaillée ---
with tab3:
    st.header("🔬 Analyse Technique Détaillée")
    st.markdown("Explorez les indicateurs techniques pour une valeur sélectionnée.")
    
    if 'collected_data' in st.session_state and st.session_state['collected_data']:
        # Reuse selection from tab1 or create a new one for clarity
        ticker_names = {v: k for k, v in tickers_dict.items()}
        available_tickers = list(st.session_state['collected_data'].keys())
        display_names = [ticker_names.get(t, t) for t in available_tickers]

        selected_display_tech = st.selectbox(
            "Sélectionner une valeur pour l'analyse technique:",
            display_names,
            key="tech_select_tab3" # Use a unique key
        )
        
        selected_ticker_tech = tickers_dict.get(selected_display_tech, selected_display_tech)
        
        if selected_ticker_tech and selected_ticker_tech in st.session_state['collected_data']:
            df_tech = st.session_state['collected_data'][selected_ticker_tech]
            company_name_tech = df_tech['Company_Name'].iloc[0] if 'Company_Name' in df_tech.columns and not df_tech.empty else selected_display_tech

            st.subheader(f"Indicateurs pour {company_name_tech}")

            if include_indicators: # Check if indicators were collected
                
                # Dynamically determine rows for subplots based on available indicators
                plot_rows_tech = 1 # Start with Close price
                row_titles_tech = ["Prix de Clôture & Moyennes Mobiles"]

                if 'RSI' in df_tech.columns and not df_tech['RSI'].isnull().all():
                    plot_rows_tech += 1
                    row_titles_tech.append("RSI (Relative Strength Index)")
                if 'MACD' in df_tech.columns and not df_tech['MACD'].isnull().all() and not df_tech['MACD_Signal'].isnull().all():
                    plot_rows_tech += 1
                    row_titles_tech.append("MACD (Moving Average Convergence Divergence)")
                
                if plot_rows_tech == 1: # Only price data, no indicators to plot
                    st.warning("Aucun indicateur technique disponible ou calculé pour cette période/donnée. Activez l'option 'Inclure les indicateurs techniques' dans la barre latérale.")
                else:
                    fig_tech = make_subplots(rows=plot_rows_tech, cols=1, shared_xaxes=True,
                                            vertical_spacing=0.1,
                                            row_titles=row_titles_tech)
                    
                    current_row_tech = 1
                    # --- Plot 1: Close Price & Moving Averages ---
                    fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['Close'], mode='lines', name='Prix Clôture', line=dict(color='blue')), row=current_row_tech, col=1)
                    if 'MA_10' in df_tech.columns and not df_tech['MA_10'].isnull().all(): fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['MA_10'], mode='lines', name='MA 10', line=dict(color='orange')), row=current_row_tech, col=1)
                    if 'MA_20' in df_tech.columns and not df_tech['MA_20'].isnull().all(): fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['MA_20'], mode='lines', name='MA 20', line=dict(color='purple')), row=current_row_tech, col=1)
                    if 'MA_50' in df_tech.columns and not df_tech['MA_50'].isnull().all(): fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['MA_50'], mode='lines', name='MA 50', line=dict(color='red')), row=current_row_tech, col=1)
                    if 'BB_Upper' in df_tech.columns and 'BB_Lower' in df_tech.columns and not df_tech['BB_Upper'].isnull().all():
                        fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['BB_Upper'], mode='lines', name='BB Upper', line=dict(color='blue', dash='dot')), row=current_row_tech, col=1)
                        fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['BB_Lower'], mode='lines', name='BB Lower', line=dict(color='blue', dash='dot')), row=current_row_tech, col=1)
                    fig_tech.update_yaxes(title_text="Prix", row=current_row_tech, col=1)
                    current_row_tech += 1

                    # --- Plot 2: RSI ---
                    if 'RSI' in df_tech.columns and not df_tech['RSI'].isnull().all():
                        fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['RSI'], mode='lines', name='RSI', line=dict(color='green')), row=current_row_tech, col=1)
                        fig_tech.add_hline(y=70, line_dash="dash", line_color="red", row=current_row_tech, col=1, annotation_text="Surachat", annotation_position="top right")
                        fig_tech.add_hline(y=30, line_dash="dash", line_color="green", row=current_row_tech, col=1, annotation_text="Survente", annotation_position="bottom right")
                        fig_tech.update_yaxes(title_text="RSI", row=current_row_tech, col=1)
                        current_row_tech += 1

                    # --- Plot 3: MACD ---
                    if 'MACD' in df_tech.columns and 'MACD_Signal' in df_tech.columns and 'MACD_Histogram' in df_tech.columns and not df_tech['MACD'].isnull().all():
                        fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['MACD'], mode='lines', name='MACD', line=dict(color='blue')), row=current_row_tech, col=1)
                        fig_tech.add_trace(go.Scatter(x=df_tech['Date'], y=df_tech['MACD_Signal'], mode='lines', name='Signal', line=dict(color='red')), row=current_row_tech, col=1)
                        marker_colors_hist = ['green' if val >= 0 else 'red' for val in df_tech['MACD_Histogram']] if not df_tech['MACD_Histogram'].empty else []
                        fig_tech.add_trace(go.Bar(x=df_tech['Date'], y=df_tech['MACD_Histogram'], name='Histogram', marker_color=marker_colors_hist), row=current_row_tech, col=1)
                        fig_tech.update_yaxes(title_text="MACD", row=current_row_tech, col=1)
                        current_row_tech += 1

                    fig_tech.update_layout(xaxis_rangeslider_visible=False, title_text=f"Analyse Technique pour {company_name_tech}", height=plot_rows_tech * 250, showlegend=True)
                    st.plotly_chart(fig_tech, use_container_width=True)
            else:
                st.info("Veuillez activer l'option 'Inclure les indicateurs techniques' dans la barre latérale pour voir cette analyse.")
        else:
            st.info("Sélectionnez une entreprise et assurez-vous d'avoir collecté les données pour voir l'analyse technique.")
    else:
        st.info("Veuillez collecter les données des entreprises dans l'onglet 'Analyse Temps Réel' pour activer cette section.")

# --- Auto-refresh logic ---
if auto_refresh:
    time.sleep(300) # Attendre 5 minutes (300 secondes)
    st.experimental_rerun()
