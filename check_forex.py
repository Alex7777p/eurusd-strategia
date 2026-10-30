#!/usr/bin/env python3
"""
Controllo automatico Forex — EUR/USD e EUR/JPY
================================================
Gira da solo su GitHub Actions ogni 30 minuti.
A ogni esecuzione invia UN report su Telegram con il segnale corrente
di entrambe le coppie (BUY / SELL / ATTENDI / NEUTRO).

La logica di analisi e' IDENTICA a quella dell'app eurusd.py.
Le credenziali Telegram arrivano dalle "Secrets" di GitHub (variabili d'ambiente),
non sono scritte nel codice.
"""

import os
import warnings
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import requests
import yfinance as yf

warnings.filterwarnings("ignore")

# ── Impostazioni ───────────────────────────────────────────────────────────────
TZ_ITALIA = ZoneInfo("Europe/Rome")      # si adatta da solo a ora legale/solare

# Finestra oraria (ora italiana) in cui inviare i messaggi.
# Fuori da questa fascia il controllo NON invia nulla (per non disturbare di notte).
# Per avvisi 24 ore su 24 metti ORA_INIZIO = 0 e ORA_FINE = 24.
ORA_INIZIO = 7     # 07:00
ORA_FINE   = 23    # 23:00

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

COPPIE = {
    "EURUSD": {"simbolo": "EURUSD=X", "nome": "EUR/USD", "pip": 0.0001, "decimali": 5},
    "EURJPY": {"simbolo": "EURJPY=X", "nome": "EUR/JPY", "pip": 0.01,   "decimali": 3},
}


def ora_italiana():
    return datetime.now(tz=TZ_ITALIA)


# ── Telegram ─────────────────────────────────────────────────────────────────────
def invia_telegram(messaggio: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ATTENZIONE: TELEGRAM_TOKEN o TELEGRAM_CHAT_ID mancanti. Niente invio.")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": messaggio, "parse_mode": "HTML"},
            timeout=15,
        )
        print(f"Telegram risposta: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"Errore invio Telegram: {e}")
        return False


# ── Sessione di mercato ──────────────────────────────────────────────────────────
def get_sessione(coppia: str) -> dict:
    h = ora_italiana().hour + ora_italiana().minute / 60.0
    if coppia == "EURUSD":
        if 9.0 <= h < 14.0:
            return {"nome": "LONDRA", "stato": "🟢 APERTO"}
        elif 14.0 <= h < 17.5:
            return {"nome": "LONDRA + NEW YORK 🔥", "stato": "🟢 APERTO — momento migliore!"}
        elif 17.5 <= h < 22.0:
            return {"nome": "NEW YORK", "stato": "🟢 APERTO"}
        else:
            return {"nome": "FUORI SESSIONE", "stato": "🔴 CHIUSO"}
    elif coppia == "EURJPY":
        if 1.0 <= h < 9.0:
            return {"nome": "TOKYO", "stato": "🟢 APERTO"}
        elif 9.0 <= h < 9.5:
            return {"nome": "TOKYO + LONDRA 🔥", "stato": "🟢 APERTO — momento migliore!"}
        elif 9.5 <= h < 17.5:
            return {"nome": "LONDRA", "stato": "🟢 APERTO"}
        else:
            return {"nome": "FUORI SESSIONE", "stato": "🔴 CHIUSO"}
    return {"nome": "—", "stato": "—"}


# ── Analisi (identica all'app) ───────────────────────────────────────────────────
def analizza(simbolo: str, periodo: str, intervallo: str) -> dict:
    try:
        ticker = yf.Ticker(simbolo)
        df = ticker.history(period=periodo, interval=intervallo)
        if df.empty:
            return {"errore": "Nessun dato"}
    except Exception as e:
        return {"errore": str(e)}

    n = len(df)
    w20  = min(20,  n - 1) if n > 5  else None
    w50  = min(50,  n - 1) if n > 20 else None
    w200 = min(200, n - 1) if n > 60 else None

    df["MA20"]  = df["Close"].rolling(window=w20).mean()  if w20  else np.nan
    df["MA50"]  = df["Close"].rolling(window=w50).mean()  if w50  else np.nan
    df["MA200"] = df["Close"].rolling(window=w200).mean() if w200 else np.nan

    delta   = df["Close"].diff()
    rsi_win = min(14, n - 1)
    media_g = delta.clip(lower=0).rolling(window=rsi_win).mean()
    media_p = (-delta.clip(upper=0)).rolling(window=rsi_win).mean()
    df["RSI"] = 100 - (100 / (1 + media_g / (media_p + 1e-10)))

    s12 = min(12, max(2, n // 5))
    s26 = min(26, max(3, n // 3))
    s9  = min(9,  max(2, n // 7))
    df["MACD"]   = df["Close"].ewm(span=s12, adjust=False).mean() - df["Close"].ewm(span=s26, adjust=False).mean()
    df["Signal"] = df["MACD"].ewm(span=s9, adjust=False).mean()

    ultimo = df.iloc[-1]
    prezzo = float(ultimo["Close"])
    ma20   = float(ultimo["MA20"])  if w20  else float("nan")
    ma50   = float(ultimo["MA50"])  if w50  else float("nan")
    ma200  = float(ultimo["MA200"]) if w200 else float("nan")
    rsi    = float(ultimo["RSI"])
    macd   = float(ultimo["MACD"])
    signal = float(ultimo["Signal"])

    segnali_rialzo  = 0
    segnali_ribasso = 0

    if not np.isnan(ma20):
        if prezzo > ma20: segnali_rialzo += 1
        else: segnali_ribasso += 1
    if w50 and not np.isnan(ma50):
        if prezzo > ma50: segnali_rialzo += 1
        else: segnali_ribasso += 1
    if w50 and not np.isnan(ma50) and not np.isnan(ma20):
        if ma20 > ma50: segnali_rialzo += 1
        else: segnali_ribasso += 1
    if not np.isnan(rsi):
        if rsi > 50: segnali_rialzo += 1
        else: segnali_ribasso += 1
    if not np.isnan(macd) and not np.isnan(signal):
        if macd > signal: segnali_rialzo += 1
        else: segnali_ribasso += 1
    if w200 and not np.isnan(ma200):
        if prezzo > ma200: segnali_rialzo += 1
        else: segnali_ribasso += 1

    totale    = segnali_rialzo + segnali_ribasso
    punteggio = round((segnali_rialzo / totale) * 100, 1) if totale > 0 else 50.0

    return {"prezzo": prezzo, "punteggio": punteggio, "rsi": rsi, "ma20": ma20}


def calcola_segnale(p4h: float, p1h: float) -> tuple:
    if   p4h >= 60 and p1h >= 55: return "BUY",          "🟢"
    elif p4h <= 40 and p1h <= 45: return "SELL",         "🔴"
    elif p4h >= 60:               return "ATTENDI BUY",  "🟡"
    elif p4h <= 40:               return "ATTENDI SELL", "🟡"
    else:                         return "NEUTRO",       "⏸️"


# ── Costruzione del blocco messaggio per una coppia ──────────────────────────────
def blocco_coppia(key: str, cfg: dict) -> str:
    r4h = analizza(cfg["simbolo"], "5d", "4h")
    r1h = analizza(cfg["simbolo"], "1d", "1h")
    if "errore" in r4h or "errore" in r1h:
        return f"⚠️ <b>{cfg['nome']}</b> — dati non disponibili"

    p4h    = r4h["punteggio"]
    p1h    = r1h["punteggio"]
    prezzo = r1h["prezzo"]
    dec    = cfg["decimali"]
    pip    = cfg["pip"]

    segnale, emoji = calcola_segnale(p4h, p1h)
    sess = get_sessione(key)

    riga = (
        f"{emoji} <b>{cfg['nome']}</b> → <b>{segnale}</b>\n"
        f"   💰 {prezzo:.{dec}f}  |  4H {p4h}% · 1H {p1h}%\n"
        f"   🌍 {sess['stato']} — {sess['nome']}"
    )

    # Livelli operativi solo quando c'e' un segnale vero
    if segnale in ("BUY", "SELL"):
        ma20 = r1h["ma20"]
        if segnale == "BUY":
            if not np.isnan(ma20) and ma20 > 0:
                sl = round(min(prezzo - pip * 30, ma20 * 0.998), dec)
            else:
                sl = round(prezzo - pip * 30, dec)
            t1 = round(prezzo + pip * 20, dec)
            t2 = round(prezzo + pip * 40, dec)
        else:  # SELL
            if not np.isnan(ma20) and ma20 > 0:
                sl = round(max(prezzo + pip * 30, ma20 * 1.002), dec)
            else:
                sl = round(prezzo + pip * 30, dec)
            t1 = round(prezzo - pip * 20, dec)
            t2 = round(prezzo - pip * 40, dec)
        riga += (
            f"\n   🔔 <b>SEGNALE OPERATIVO</b>"
            f"\n   Ingresso {prezzo:.{dec}f} · SL {sl:.{dec}f}"
            f"\n   Target1 {t1:.{dec}f} · Target2 {t2:.{dec}f}"
            f"\n   ⚠️ Rischio max 2% del capitale"
        )
    return riga


def main():
    now = ora_italiana()

    # Rispetta la finestra oraria
    if not (ORA_INIZIO <= now.hour < ORA_FINE):
        print(f"Ora {now.strftime('%H:%M')} fuori dalla finestra {ORA_INIZIO}:00-{ORA_FINE}:00. Nessun invio.")
        return

    blocchi = [blocco_coppia(k, c) for k, c in COPPIE.items()]

    testo = (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>REPORT FOREX</b> · {now.strftime('%H:%M')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        + "\n\n".join(blocchi)
        + f"\n\n━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Controllo automatico · dati Yahoo Finance"
    )

    print(testo)
    invia_telegram(testo)


if __name__ == "__main__":
    main()
