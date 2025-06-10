import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from get_cac40_tickers import get_cac40_tickers
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
    
    if abs(num) >= 1e9:
        return f"{prefix}{num/1e9:.2f}Md{suffix}"
    elif abs(num) >= 1e6:
        return f"{prefix}{num/1e6:.2f}M{suffix}"
    elif abs(num) >= 1e3:
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
    if len(df) < 2:
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
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        if len(df) >= 26:
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Bandes de Bollinger
        if len(df) >= 20:
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
    except Exception as e:
        st.warning(f"Erreur lors du calcul des indicateurs techniques: {e}")
    
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
    
    # Sélection des entreprises avec recherche
    st.subheader("🏢 Sélection des Entreprises")
    
    if tickers_dict:
        # Barre de recherche
        search_term = st.text_input("🔍 Rechercher", placeholder="Tapez le nom d'une entreprise...")
        
        # Filtre par secteur (si disponible dans les données)
        all_companies = list(tickers_dict.keys())
        
        # Filtrage basé sur la recherche
        if search_term:
            filtered_companies = [name for name in all_companies 
                                if search_term.lower() in name.lower()]
        else:
            filtered_companies = all_companies
        
        # Sélection multiple avec valeurs par défaut
        default_selection = filtered_companies[:5] if len(filtered_companies) >= 5 else filtered_companies
        selected_companies = st.multiselect(
            "Entreprises à analyser:",
            filtered_companies,
            default=default_selection,
            help=f"{len(filtered_companies)} entreprises disponibles"
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
tab1, tab2, tab3 = st.tabs(["📊 Analyse Temps Réel", "📈 Vue d'Ensemble CAC 40", "📋 Analyse Technique"])

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
            tickers_to_collect = [tickers_dict[name] for name in selected_companies]
            
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
        
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_display = st.selectbox(
                "Sélectionner une valeur pour l'analyse détaillée:", 
                display_names, 
                key="viz_select"
            )
        
        with col2:
            chart_type = st.selectbox(
                "Type de graphique:",
                ["Chandelier + Volume", "Prix + Indicateurs", "Comparaison Multiple"],
                key="chart_type_select"
            )
        
        selected_ticker = tickers_dict.get(selected_display, selected_display)
