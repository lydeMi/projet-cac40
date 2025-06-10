import requests
from bs4 import BeautifulSoup
import yfinance as yf
import time
import streamlit as st

@st.cache_data(ttl=86400)
def get_cac40_tickers():
    url = "https://www.zonebourse.com/indice/CAC-40-4941/composition/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", {"class": "tablesorter"})

    tickers_dict = {}
    if table:
        rows = table.find_all("tr")[1:]

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                name = cols[0].get_text(strip=True)
                guess_ticker = name.split()[0][:4].upper() + ".PA"
                try:
                    info = yf.Ticker(guess_ticker).info
                    if "longName" in info:
                        tickers_dict[info["longName"]] = guess_ticker
                except:
                    continue
                time.sleep(0.5)
    return tickers_dict
