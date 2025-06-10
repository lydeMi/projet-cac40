import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from get_cac40_tickers import get_cac40_tickers

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

    for ticker in tickers:
        try:
            data = yf.download(ticker, period="1d", interval="1m", progress=False)
            if not data.empty:
                data["Ticker"] = ticker
                data.reset_index(inplace=True)
                df_all.append(data)
                st.success(f"{ticker} collecté")
        except Exception as e:
            st.error(f"Erreur {ticker} : {e}")

    if df_all:
        df = pd.concat(df_all)
        st.dataframe(df.head())

        # Graphique d’un ticker
        ticker_plot = st.selectbox("Graphique pour :", tickers)
        chart_df = df[df["Ticker"] == ticker_plot]
        st.line_chart(chart_df.set_index("Datetime")["Close"])

        # Export CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("💾 Télécharger CSV", csv, f"cac40_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
    else:
        st.warning("Aucune donnée récupérée.")
