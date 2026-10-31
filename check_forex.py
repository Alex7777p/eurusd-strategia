#!/usr/bin/env python3
"""
Controllo automatico Forex — EUR/USD e EUR/JPY
================================================
Gira da solo su GitHub Actions ogni 30 minuti (ai minuti 5 e 35).
Attivo SOLO da lunedi' a venerdi' (il weekend i mercati sono chiusi).

Invia su Telegram:
  • ☀️  BUONGIORNO alle 9:00  → riepilogo completo di entrambe le coppie
  • 🎯  OPERATIVO alle 15:00   → il "da farsi" nel cuore della sovrapposizione
                                 Londra-New York (il momento di massimo volume)
  • 🔔  CAMBIO SEGNALE         → se tra le 14:00 e le 18:00 (finestra operativa)
                                 EUR/USD o EUR/JPY cambia segnale

Quando viene avviato A MANO da GitHub ("Run workflow") invia sempre un
report di TEST, cosi' si puo' provare in qualsiasi momento, weekend compreso.

Logica di analisi IDENTICA all'app eurusd.py. Lo stato precedente e'
ricordato in stato_forex.json (cache di GitHub Actions). Credenziali Telegram
dalle "Secrets" di GitHub.
"""

import os
import json
import warnings
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import requests
import yfinance as yf

warnings.filterwarnings("ignore")

# ── Impostazioni orarie (ora italiana) ───────────────────────────────────────────
TZ_ITALIA = ZoneInfo("Europe/Rome")      # si adatta da solo a ora legale/solare

ORA_BUONGIORNO     = 9     # riepilogo del mattino
ORA_OPERATIVO      = 15    # messaggio "da farsi" (overlap Londra-NY, 14:00-17:30)
ORA_CAMBIO_INIZIO  = 14    # inizio finestra avvisi di cambiamento
ORA_CAMBIO_FINE    = 18    # fine   finestra avvisi di cambiamento (inclusa)

# Il bot "lavora" (aggiorna lo stato e puo' inviare) solo in questa fascia,
# nei giorni feriali. Fuori riposa.
ORA_ATTIVO_INIZIO  = 8
ORA_ATTIVO_FINE    = 23

STATO_FILE = "stato_forex.json"

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

COPPIE = {
    "EURUSD": {"simbolo": "EURUSD=X", "nome": "EUR/USD", "pip": 0.0001, "decimali": 5},
    "EURJPY": {"simbolo": "EURJPY=X", "nome": "EUR/JPY", "pip": 0.01,   "decimali": 3},
}


def ora_italiana():
    return datetime.now(tz=TZ_ITALIA)


# ── Memoria dello stato (file conservato nella cache) ────────────────────────────
def carica_stato() -> dict:
    try:
        with open(STATO_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def salva_stato(stato: dict):
    try:
        with open(STATO_FILE, "w") as f:
            json.dump(stato, f)
        print(f"Stato salvato: {stato}")
    except Exception as e:
        print(f"Errore salvataggio stato: {e}")


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


def analizza_coppia(key: str, cfg: dict) -> tuple:
    """Restituisce (segnale, testo_del_blocco)."""
    r4h = analizza(cfg["simbolo"], "5d", "4h")
    r1h = analizza(cfg["simbolo"], "1d", "1h")
    if "errore" in r4h or "errore" in r1h:
        return None, f"⚠️ <b>{cfg['nome']}</b> — dati non disponibili"

    p4h    = r4h["punteggio"]
    p1h    = r1h["punteggio"]
    prezzo = r1h["prezzo"]
    dec    = cfg["decimali"]
    pip    = cfg["pip"]

    segnale, emoji = calcola_segnale(p4h, p1h)
    sess = get_sessione(key)

    testo = (
        f"{emoji} <b>{cfg['nome']}</b> → <b>{segnale}</b>\n"
        f"   💰 {prezzo:.{dec}f}  |  4H {p4h}% · 1H {p1h}%\n"
        f"   🌍 {sess['stato']} — {sess['nome']}"
    )

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
        testo += (
            f"\n   🔔 <b>SEGNALE OPERATIVO</b>"
            f"\n   Ingresso {prezzo:.{dec}f} · SL {sl:.{dec}f}"
            f"\n   Target1 {t1:.{dec}f} · Target2 {t2:.{dec}f}"
            f"\n   ⚠️ Rischio max 2% del capitale"
        )
    return segnale, testo


def righe_cambi(cambi: list) -> str:
    """cambi = lista di (nome, vecchio_segnale_o_None, nuovo_segnale)."""
    righe = []
    for nome, vecchio, nuovo in cambi:
        if vecchio is None:
            righe.append(f"• {nome}: <b>{nuovo}</b>")
        else:
            righe.append(f"• {nome}: {vecchio} → <b>{nuovo}</b>")
    return "\n".join(righe)


def componi(intestazione: str, blocchi: dict, now) -> str:
    corpo = "\n\n".join(blocchi[k] for k in COPPIE)
    return (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{intestazione}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        + corpo
        + f"\n\n━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Controllo automatico · dati Yahoo Finance"
    )


def main():
    now = ora_italiana()
    hhmm = now.strftime("%H:%M")
    evento = os.environ.get("GITHUB_EVENT_NAME", "")
    is_test = (evento == "workflow_dispatch")   # avvio manuale da GitHub

    # Fuori dal test: niente weekend, niente orari morti
    if not is_test:
        if now.weekday() >= 5:   # 5 = sabato, 6 = domenica
            print(f"Weekend ({now.strftime('%A')}): mercati chiusi. Nessun invio.")
            return
        if not (ORA_ATTIVO_INIZIO <= now.hour <= ORA_ATTIVO_FINE):
            print(f"Ora {hhmm} fuori dalla fascia attiva. Nessun invio.")
            return

    # Calcolo i segnali e rilevo i cambiamenti
    stato_prec  = carica_stato()
    stato_nuovo = dict(stato_prec)
    blocchi = {}
    cambi   = []

    for key, cfg in COPPIE.items():
        seg, testo = analizza_coppia(key, cfg)
        blocchi[key] = testo
        if seg is None:
            continue
        if stato_prec.get(key) != seg:
            cambi.append((cfg["nome"], stato_prec.get(key), seg))
        stato_nuovo[key] = seg

    h = now.hour
    oggi = now.strftime("%Y-%m-%d")
    intest = None

    # I messaggi fissi (buongiorno, operativo) partono UNA sola volta al giorno:
    # con la cadenza di 30 min la stessa ora scatta due volte (es. 9:05 e 9:35),
    # quindi li marco per data cosi' il secondo passaggio non li ripete.
    if is_test:
        intest = f"🧪 <b>TEST — stato attuale</b> · {hhmm}"
    elif h == ORA_BUONGIORNO and stato_prec.get("data_buongiorno") != oggi:
        intest = f"☀️ <b>BUONGIORNO — Riepilogo</b> · {hhmm}"
        stato_nuovo["data_buongiorno"] = oggi
    elif h == ORA_OPERATIVO and stato_prec.get("data_operativo") != oggi:
        intest = f"🎯 <b>FINESTRA OPERATIVA (Londra–NY) — Il da farsi</b> · {hhmm}"
        stato_nuovo["data_operativo"] = oggi
    elif (ORA_CAMBIO_INIZIO <= h <= ORA_CAMBIO_FINE) and cambi:
        intest = f"🔔 <b>CAMBIO SEGNALE</b> · {hhmm}\n" + righe_cambi(cambi)

    if intest is not None:
        testo = componi(intest, blocchi, now)
        print(testo)
        invia_telegram(testo)
    else:
        print(f"Ora {hhmm}: nessun messaggio previsto (cambi: {cambi}).")

    # Aggiorno sempre la memoria (tranne nei test, per non sporcare la linea reale)
    if not is_test:
        salva_stato(stato_nuovo)


if __name__ == "__main__":
    main()
