"""
EUR/USD Strategia 4H + 1H
App minimalista per telefono — aggiornamento automatico ogni 30 minuti
"""

import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import numpy as np
import warnings
import time
from datetime import datetime, timedelta

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="EUR/USD",
    page_icon="💱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg:      #080c10;
    --surface: #0f1419;
    --surf2:   #161d26;
    --border:  #1e2a38;
    --buy:     #00d4a0;
    --sell:    #ff4757;
    --wait:    #ffc107;
    --neutro:  #546e7a;
    --text:    #cdd9e5;
    --muted:   #546e7a;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, .stApp { background: var(--bg) !important; color: var(--text); }

/* Nascondi elementi Streamlit inutili su mobile */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

.block-container {
    padding: 0 !important;
    max-width: 480px !important;
    margin: 0 auto !important;
}

/* Font */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Titolo */
.app-header {
    text-align: center;
    padding: 28px 20px 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
}
.app-header .pair {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    letter-spacing: 4px;
    color: var(--text);
    line-height: 1;
}
.app-header .price {
    font-family: 'DM Mono', monospace;
    font-size: 1.5rem;
    color: var(--text);
    margin-top: 6px;
}
.app-header .subtitle {
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 4px;
}

/* Card segnale principale */
.signal-card {
    margin: 20px 16px;
    border-radius: 16px;
    padding: 28px 20px;
    text-align: center;
    border: 1.5px solid;
    position: relative;
    overflow: hidden;
}
.signal-card::before {
    content: '';
    position: absolute;
    top: -60px; left: 50%;
    transform: translateX(-50%);
    width: 200px; height: 200px;
    border-radius: 50%;
    filter: blur(60px);
    opacity: 0.15;
    pointer-events: none;
}
.card-buy   { background: #001f17; border-color: var(--buy); }
.card-buy::before { background: var(--buy); }
.card-sell  { background: #1f0008; border-color: var(--sell); }
.card-sell::before { background: var(--sell); }
.card-wait  { background: #1a1500; border-color: var(--wait); }
.card-wait::before { background: var(--wait); }
.card-neutro { background: var(--surface); border-color: var(--border); }

.signal-emoji { font-size: 3rem; line-height: 1; margin-bottom: 10px; }
.signal-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    letter-spacing: 3px;
    line-height: 1;
}
.signal-sub {
    font-size: 0.85rem;
    color: var(--muted);
    margin-top: 8px;
    line-height: 1.4;
}

/* Timeframe cards */
.tf-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 0 16px 16px;
}
.tf-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.tf-label {
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.tf-verdict {
    font-family: 'DM Mono', monospace;
    font-size: 1rem;
    font-weight: 500;
}
.tf-details {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 4px;
    font-family: 'DM Mono', monospace;
}
.tf-bar-bg {
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    margin-top: 8px;
    overflow: hidden;
}
.tf-bar-fill { height: 100%; border-radius: 2px; }

/* Dettagli operativi */
.ops-box {
    margin: 0 16px 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
}
.ops-title {
    font-size: 0.7rem;
    color: var(--muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.ops-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.88rem;
}
.ops-row:last-child { border-bottom: none; }
.ops-key { color: var(--muted); }
.ops-val { font-family: 'DM Mono', monospace; font-weight: 500; }

/* Footer */
.app-footer {
    text-align: center;
    padding: 16px;
    font-size: 0.72rem;
    color: var(--muted);
    border-top: 1px solid var(--border);
    margin-top: 8px;
}

/* Bottone aggiorna */
.stButton > button {
    width: 100%;
    background: var(--surf2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 10px !important;
    margin: 0 16px;
    transition: all 0.2s;
}
.stButton > button:hover {
    border-color: var(--buy) !important;
    color: var(--buy) !important;
}

/* Countdown */
.countdown {
    text-align: center;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    color: var(--muted);
    padding: 8px;
}

/* Spinner override */
.stSpinner > div { border-top-color: var(--buy) !important; }

/* Animazione pulse per segnale attivo */
@keyframes pulse-buy  { 0%,100%{box-shadow:0 0 0 0 rgba(0,212,160,.3)} 50%{box-shadow:0 0 0 12px rgba(0,212,160,0)} }
@keyframes pulse-sell { 0%,100%{box-shadow:0 0 0 0 rgba(255,71,87,.3)}  50%{box-shadow:0 0 0 12px rgba(255,71,87,0)} }
.card-buy  { animation: pulse-buy  2.5s ease-in-out infinite; }
.card-sell { animation: pulse-sell 2.5s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  LOGICA ANALISI
#  Allineata al programma locale (trend_analyzer.py):
#  - "4H" usa period="5d" interval="1h"  (come il locale)
#  - "1H" usa period="1d" interval="5m"  (come il locale)
# ══════════════════════════════════════════════════════════════════════════════

def analizza(periodo: str, intervallo: str) -> dict:
    try:
        # Prima scarica senza intervallo (come fa il locale)
        ticker = yf.Ticker("EURUSD=X")
        df = ticker.history(period=periodo)
        if df.empty:
            return {"errore": "Nessun dato"}

        # Poi ri-scarica con l'intervallo corretto (identico alla logica locale)
        if periodo == "5d":
            df = ticker.history(period=periodo, interval="1h")   # locale usa 1h per "4H"
        elif periodo == "1d":
            df = ticker.history(period=periodo, interval="5m")   # locale usa 5m per "1H"

        if df.empty:
            return {"errore": "Nessun dato dopo intervallo"}

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
        if rsi < 30 or rsi > 70:
            pass  # ipervenduto/ipercomprato: neutro
        elif rsi > 50: segnali_rialzo += 1
        else: segnali_ribasso += 1

    if not np.isnan(macd) and not np.isnan(signal):
        if macd > signal: segnali_rialzo += 1
        else: segnali_ribasso += 1

    if w200 and not np.isnan(ma200):
        if prezzo > ma200: segnali_rialzo += 1
        else: segnali_ribasso += 1

    totale    = segnali_rialzo + segnali_ribasso
    punteggio = segnali_rialzo / totale if totale > 0 else 0.5

    if punteggio >= 0.7:   verdetto = "TREND IN CRESCITA"
    elif punteggio >= 0.5: verdetto = "TREND POSITIVO"
    elif punteggio >= 0.3: verdetto = "TREND NEGATIVO"
    else:                  verdetto = "TREND IN CALO"

    return {
        "prezzo":          prezzo,
        "punteggio":       round(punteggio * 100, 1),
        "verdetto":        verdetto,
        "rsi":             rsi,
        "ma20":            ma20,
        "segnali_rialzo":  segnali_rialzo,
        "segnali_ribasso": segnali_ribasso,
    }


def calcola_segnale(p4h: float, p1h: float) -> tuple:
    if   p4h >= 60 and p1h >= 55: return "BUY",          "🟢", "card-buy",    "#00d4a0"
    elif p4h <= 40 and p1h <= 45: return "SELL",         "🔴", "card-sell",   "#ff4757"
    elif p4h >= 60:               return "ATTENDI BUY",  "🟡", "card-wait",   "#ffc107"
    elif p4h <= 40:               return "ATTENDI SELL", "🟡", "card-wait",   "#ffc107"
    else:                         return "NEUTRO",        "⏸️", "card-neutro", "#546e7a"


def descrizione_segnale(segnale: str, p4h: float, p1h: float) -> str:
    if segnale == "BUY":
        return "4H e 1H allineati al rialzo → Entra LONG"
    elif segnale == "SELL":
        return "4H e 1H allineati al ribasso → Entra SHORT"
    elif segnale == "ATTENDI BUY":
        return f"Trend 4H rialzista ({p4h}%) ma 1H non ancora pronto ({p1h}%) — aspetta conferma"
    elif segnale == "ATTENDI SELL":
        return f"Trend 4H ribassista ({p4h}%) ma 1H non ancora pronto ({p1h}%) — aspetta conferma"
    else:
        return "Segnali non allineati — rimani fuori dal mercato"


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

if "dati" not in st.session_state:
    st.session_state["dati"] = None
if "ultimo_aggiornamento" not in st.session_state:
    st.session_state["ultimo_aggiornamento"] = None
if "ultimo_segnale" not in st.session_state:
    st.session_state["ultimo_segnale"] = None
if "timer_attivo" not in st.session_state:
    st.session_state["timer_attivo"] = True

INTERVALLO_MINUTI = 30


def carica_dati():
    r4h = analizza("5d", "1h")   # locale: period=5d → interval=1h
    r1h = analizza("1d", "5m")   # locale: period=1d → interval=5m
    if "errore" not in r4h and "errore" not in r1h:
        st.session_state["dati"] = (r4h, r1h)
        st.session_state["ultimo_aggiornamento"] = datetime.now()
    return r4h, r1h


# Carica dati al primo avvio o dopo aggiornamento manuale
if st.session_state["dati"] is None:
    with st.spinner("⏳ Caricamento dati EUR/USD..."):
        carica_dati()
    st.rerun()

# Auto-refresh ogni 30 minuti (solo se timer attivo)
if st.session_state["timer_attivo"] and st.session_state["ultimo_aggiornamento"]:
    secondi_passati = (datetime.now() - st.session_state["ultimo_aggiornamento"]).total_seconds()
    if secondi_passati >= INTERVALLO_MINUTI * 60:
        with st.spinner("Aggiornamento automatico..."):
            carica_dati()


# ══════════════════════════════════════════════════════════════════════════════
#  RENDERING
# ══════════════════════════════════════════════════════════════════════════════

r4h, r1h = st.session_state["dati"]

if "errore" in r4h or "errore" in r1h:
    st.error("❌ Errore nel recupero dati. Riprova.")
    if st.button("🔄 Riprova"):
        st.session_state["dati"] = None
        st.rerun()
    st.stop()

p4h    = r4h["punteggio"]
p1h    = r1h["punteggio"]
prezzo = r1h["prezzo"]

segnale, emoji, card_class, colore = calcola_segnale(p4h, p1h)
desc = descrizione_segnale(segnale, p4h, p1h)

# Calcola livelli operativi
ma20 = r1h["ma20"]
if not np.isnan(ma20) and ma20 > 0:
    sl_buy  = round(min(prezzo - 0.0030, ma20 * 0.998), 5)
    sl_sell = round(max(prezzo + 0.0030, ma20 * 1.002), 5)
else:
    sl_buy  = round(prezzo - 0.0030, 5)
    sl_sell = round(prezzo + 0.0030, 5)

t1_buy  = round(prezzo + 0.0020, 5)
t2_buy  = round(prezzo + 0.0040, 5)
t1_sell = round(prezzo - 0.0020, 5)
t2_sell = round(prezzo - 0.0040, 5)

ora_agg = st.session_state["ultimo_aggiornamento"].strftime("%H:%M") if st.session_state["ultimo_aggiornamento"] else "—"

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
    <div class="pair">EUR / USD</div>
    <div class="price">{prezzo:.5f}</div>
    <div class="subtitle">Strategia 4H + 1H</div>
</div>
""", unsafe_allow_html=True)

# ── Segnale principale ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="signal-card {card_class}">
    <div class="signal-emoji">{emoji}</div>
    <div class="signal-label" style="color:{colore};">{segnale}</div>
    <div class="signal-sub">{desc}</div>
</div>
""", unsafe_allow_html=True)

# ── Cards 4H e 1H ─────────────────────────────────────────────────────────────
def colore_tf(p):
    if p >= 55: return "#00d4a0"
    elif p <= 40: return "#ff4757"
    else: return "#ffc107"

def label_tf(p):
    if p >= 60: return "RIALZISTA"
    elif p >= 55: return "POSITIVO"
    elif p >= 45: return "NEUTRO"
    elif p >= 40: return "NEGATIVO"
    else: return "RIBASSISTA"

rsi4h_s = f"{r4h['rsi']:.1f}" if not np.isnan(r4h['rsi']) else "—"
rsi1h_s = f"{r1h['rsi']:.1f}" if not np.isnan(r1h['rsi']) else "—"

col_4h = colore_tf(p4h)
col_1h = colore_tf(p1h)

st.markdown(f"""
<div class="tf-grid">
    <div class="tf-card">
        <div class="tf-label">4 ORE — Trend</div>
        <div class="tf-verdict" style="color:{col_4h};">{label_tf(p4h)}</div>
        <div class="tf-details">RSI {rsi4h_s} &nbsp;|&nbsp; {p4h}%</div>
        <div class="tf-bar-bg">
            <div class="tf-bar-fill" style="width:{p4h}%;background:{col_4h};"></div>
        </div>
    </div>
    <div class="tf-card">
        <div class="tf-label">1 ORA — Entrata</div>
        <div class="tf-verdict" style="color:{col_1h};">{label_tf(p1h)}</div>
        <div class="tf-details">RSI {rsi1h_s} &nbsp;|&nbsp; {p1h}%</div>
        <div class="tf-bar-bg">
            <div class="tf-bar-fill" style="width:{p1h}%;background:{col_1h};"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Dettagli operativi ─────────────────────────────────────────────────────────
if segnale == "BUY":
    st.markdown(f"""
    <div class="ops-box">
        <div class="ops-title">📋 Dettagli operazione BUY</div>
        <div class="ops-row"><span class="ops-key">Ingresso</span><span class="ops-val" style="color:#00d4a0;">{prezzo:.5f}</span></div>
        <div class="ops-row"><span class="ops-key">Stop Loss</span><span class="ops-val" style="color:#ff4757;">{sl_buy:.5f} &nbsp;(-{round((prezzo-sl_buy)*10000):.0f} pip)</span></div>
        <div class="ops-row"><span class="ops-key">Target 1</span><span class="ops-val" style="color:#00d4a0;">{t1_buy:.5f} &nbsp;(+{round((t1_buy-prezzo)*10000):.0f} pip)</span></div>
        <div class="ops-row"><span class="ops-key">Target 2</span><span class="ops-val" style="color:#00d4a0;">{t2_buy:.5f} &nbsp;(+{round((t2_buy-prezzo)*10000):.0f} pip)</span></div>
        <div class="ops-row"><span class="ops-key">Rischio max</span><span class="ops-val">2% del capitale</span></div>
    </div>
    """, unsafe_allow_html=True)

elif segnale == "SELL":
    st.markdown(f"""
    <div class="ops-box">
        <div class="ops-title">📋 Dettagli operazione SELL</div>
        <div class="ops-row"><span class="ops-key">Ingresso</span><span class="ops-val" style="color:#ff4757;">{prezzo:.5f}</span></div>
        <div class="ops-row"><span class="ops-key">Stop Loss</span><span class="ops-val" style="color:#ff4757;">{sl_sell:.5f} &nbsp;(+{round((sl_sell-prezzo)*10000):.0f} pip)</span></div>
        <div class="ops-row"><span class="ops-key">Target 1</span><span class="ops-val" style="color:#00d4a0;">{t1_sell:.5f} &nbsp;(-{round((prezzo-t1_sell)*10000):.0f} pip)</span></div>
        <div class="ops-row"><span class="ops-key">Target 2</span><span class="ops-val" style="color:#00d4a0;">{t2_sell:.5f} &nbsp;(-{round((prezzo-t2_sell)*10000):.0f} pip)</span></div>
        <div class="ops-row"><span class="ops-key">Rischio max</span><span class="ops-val">2% del capitale</span></div>
    </div>
    """, unsafe_allow_html=True)

elif segnale in ("ATTENDI BUY", "ATTENDI SELL"):
    direzione = "BUY" if segnale == "ATTENDI BUY" else "SELL"
    soglia    = "1H superi 55%" if direzione == "BUY" else "1H scenda sotto 45%"
    st.markdown(f"""
    <div class="ops-box">
        <div class="ops-title">⏳ In attesa di conferma</div>
        <div class="ops-row"><span class="ops-key">Direzione attesa</span><span class="ops-val" style="color:#ffc107;">{direzione}</span></div>
        <div class="ops-row"><span class="ops-key">Condizione</span><span class="ops-val">{soglia}</span></div>
        <div class="ops-row"><span class="ops-key">1H attuale</span><span class="ops-val">{p1h}%</span></div>
        <div class="ops-row"><span class="ops-key">Rianalizza tra</span><span class="ops-val">30–60 minuti</span></div>
    </div>
    """, unsafe_allow_html=True)

# ── Timer + bottoni ───────────────────────────────────────────────────────────
timer_attivo = st.session_state["timer_attivo"]

if timer_attivo and st.session_state["ultimo_aggiornamento"]:
    prossimo_dt  = st.session_state["ultimo_aggiornamento"] + timedelta(minutes=INTERVALLO_MINUTI)
    prossimo_ora = prossimo_dt.strftime("%H:%M")
    stato_label  = "AUTO-REFRESH ATTIVO"
    stato_colore = "#00d4a0"
    testo_colore = "#cdd9e5"
else:
    prossimo_ora = "--:--"
    stato_label  = "AUTO-REFRESH IN PAUSA"
    stato_colore = "#ff4757"
    testo_colore = "#546e7a"

st.markdown(f"""
<div style="margin: 8px 16px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 20px; text-align: center;">
    <div style="font-size: 0.7rem; color: {stato_colore}; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px;">
        {'⏱️' if timer_attivo else '⏸️'} &nbsp; {stato_label}
    </div>
    <div style="font-family: 'Bebas Neue', sans-serif; font-size: 3.4rem; letter-spacing: 8px; color: {testo_colore}; line-height: 1;">
        {prossimo_ora}
    </div>
    <div style="font-size: 0.72rem; color: #546e7a; margin-top: 6px;">
        Prossimo aggiornamento dati
    </div>
</div>
""", unsafe_allow_html=True)

# Bottoni
c1, c2, c3 = st.columns(3)
with c1:
    label_btn = "⏹ STOP" if timer_attivo else "▶ START"
    if st.button(label_btn, use_container_width=True, key="btn_timer"):
        st.session_state["timer_attivo"] = not timer_attivo
        st.rerun()
with c2:
    if st.button("🔁 RESET", use_container_width=True, key="btn_reset"):
        st.session_state["timer_attivo"] = True
        st.session_state["dati"] = None
        st.session_state["ultimo_aggiornamento"] = None
        st.rerun()
with c3:
    if st.button("🔄 ORA", use_container_width=True, key="btn_aggiorna"):
        loading = st.empty()
        loading.markdown("""
        <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(8,12,16,0.95);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:9999;">
            <div style="width:56px;height:56px;border:3px solid #1e2a38;border-top:3px solid #00d4a0;border-radius:50%;animation:spin 0.8s linear infinite;"></div>
            <div style="margin-top:20px;font-family:'DM Mono',monospace;font-size:0.9rem;color:#00d4a0;letter-spacing:2px;">AGGIORNAMENTO...</div>
            <div style="margin-top:8px;font-size:0.75rem;color:#546e7a;">Recupero dati da Yahoo Finance</div>
            <style>@keyframes spin{{to{{transform:rotate(360deg)}}}}</style>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(2)
        loading.empty()
        st.session_state["dati"] = None
        st.session_state["ultimo_aggiornamento"] = None
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-footer">
    Aggiornato alle {ora_agg} &nbsp;·&nbsp; Auto-refresh ogni {INTERVALLO_MINUTI} min &nbsp;·&nbsp; Dati: Yahoo Finance
</div>
""", unsafe_allow_html=True)
