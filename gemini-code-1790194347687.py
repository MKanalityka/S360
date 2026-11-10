"""Spółdzielnia360 · Executive Edition — motyw jasny/ciemny i analiza oszczędności.

Instalacja: pip install -r requirements.txt
Uruchomienie: streamlit run pob.py
Wymaga pliku data_model.py w tym samym katalogu.
WSZYSTKIE dane są fikcyjne, wyłącznie demonstracyjne.
"""
from __future__ import annotations

from io import BytesIO
import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_model import (
    AS_OF, DEMO_START, DEMO_END, CATEGORY_COLORS, CATEGORY_GROUPS,
    make_demo_data, period_filter, period_latest, pct_change, cost_anomalies,
    savings_opportunities,
)

st.set_page_config(
    page_title="Spółdzielnia360 | Panel zarządczy",
    page_icon="🏢", layout="wide", initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WYGLĄD · spójny system kolorystyczny (CSS bez dodatkowych bibliotek)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C = {
    "ink": "#182B46", "navy": "#11294B", "blue": "#3765EC",
    "teal": "#12A994", "purple": "#7B61D9", "amber": "#F29A4A",
    "red": "#E45D6A", "muted": "#697B91", "grid": "#E9EEF6",
    "soft": "#F6F9FD",
}

if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
DARK = bool(st.session_state["dark_mode"])
if DARK:
    # Podstawowe kolory wykresów dostosowują się do aktywnego motywu.
    C.update(ink="#EEF4FF", muted="#B9C8DF", grid="#2C3853", soft="#101B30",
             blue="#79A4FF", teal="#4EE1C2", purple="#B49AFF",
             amber="#FFBE72", red="#FF7F91")
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp {font-family:'DM Sans',system-ui,-apple-system,sans-serif;}
.stApp {background:linear-gradient(180deg,#EEF4FD 0%,#F9FBFF 45%,#F5F8FD 100%);color:#182B46;}
.block-container {max-width:1510px;padding-top:1.35rem;padding-bottom:3.3rem;}
[data-testid="stSidebar"] {background:linear-gradient(164deg,#122647 0%,#1A3E68 62%,#165963 100%);}
[data-testid="stSidebar"] * {color:#EAF5FF !important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {line-height:1.55;}
[data-testid="stSidebar"] hr {border-color:rgba(255,255,255,.20);}
[data-testid="stSidebar"] .stCaption {color:#C7D9E8 !important;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap:9px;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {
 padding:14px 12px!important;border:1px solid rgba(255,255,255,.14);border-radius:13px;
 background:rgba(255,255,255,.045);cursor:pointer;transition:background .16s,border-color .16s;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {
 background:rgba(255,255,255,.14);border-color:rgba(255,255,255,.3);
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
 background:linear-gradient(100deg,rgba(73,120,238,.86),rgba(55,176,173,.35));
 border-color:rgba(188,235,255,.58);box-shadow:0 7px 20px rgba(4,21,55,.2);
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label p {font-weight:750;font-size:.92rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label [data-testid="stMarkdownContainer"] {margin-left:2px;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label [data-baseweb="radio"] {accent-color:#90EEE0;}
.sidebar-label {font-size:.75rem;letter-spacing:.16em;font-weight:800;color:#91ECDD;margin:18px 0 13px;}
.sidebar-brand {font-weight:800;font-size:1.44rem;letter-spacing:-.04em;color:white;line-height:1.1;}
.sidebar-brand span {color:#7CEBDC;}
.sidebar-mini {color:#C2D6E9;font-size:.77rem;margin-top:8px;line-height:1.5;}
.sidebar-note {border:1px solid rgba(191,235,247,.22);background:rgba(255,255,255,.06);
 border-radius:15px;padding:14px;color:#D5E8F7;font-size:.78rem;line-height:1.65;margin-top:18px;}
[data-testid="stPlotlyChart"] {border-radius:17px;background:white;border:1px solid #E7ECF4;
 box-shadow:0 5px 19px rgba(33,56,99,.045);padding:6px;}
[data-testid="stDataFrame"] {border-radius:15px;overflow:hidden;border:1px solid #E6EBF3;}
[data-testid="stDownloadButton"] button {border-radius:12px;background:#173F89;color:white;
 font-weight:700;border:none;}
[data-testid="stDownloadButton"] button:hover {background:#2B59AE;color:white;}
/* Hero jest prawdziwym kontenerem Streamlit — jego kolumny i filtry są wewnątrz gradientu. */
.st-key-hero_banner {position:relative;isolation:isolate;overflow:visible;border-radius:25px;
 padding:26px 30px 22px!important;background:linear-gradient(110deg,#102748 0%,#2450A2 52%,#6A52C3 100%);
 box-shadow:0 16px 40px rgba(27,52,125,.21);margin-bottom:19px;}
.st-key-hero_banner:before {content:'';position:absolute;pointer-events:none;z-index:-1;
 width:320px;height:320px;top:-210px;right:-100px;border-radius:50%;
 border:48px solid rgba(255,255,255,.065);}
.st-key-hero_banner:after {content:'';position:absolute;pointer-events:none;z-index:-1;
 width:340px;height:250px;bottom:-135px;right:15%;border-radius:50%;
 background:radial-gradient(circle,rgba(75,239,218,.19),transparent 70%);}
.hero-kicker {color:#92F2D9;font-size:.74rem;font-weight:800;letter-spacing:.18em;text-transform:uppercase;}
.hero-heading {color:white!important;font-size:clamp(1.8rem,3.3vw,2.55rem);font-weight:800;
 letter-spacing:-.045em;line-height:1.14;margin:6px 0 7px;}
.hero-heading em {color:#A0F8E0;font-style:normal;}
.hero-description {color:#E2EBFF;font-size:.88rem;line-height:1.55;margin:0 0 5px;}
.hero-filters {color:#ACF4E0;font-size:.72rem;letter-spacing:.15em;font-weight:800;
 margin:13px 0 -3px;text-transform:uppercase;}
.hero-foot {display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;}
.hero-badge {background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.2);
 border-radius:100px;font-size:.73rem;font-weight:650;color:#F5FAFF;padding:6px 12px;}
.st-key-hero_banner [data-testid="stWidgetLabel"] p,
.st-key-hero_banner label[data-testid="stWidgetLabel"] {color:#F0F6FF!important;font-weight:700!important;}
.st-key-hero_banner [data-testid="stMarkdownContainer"] label {color:white;}
.st-key-hero_banner [data-baseweb="select"] > div {background:rgba(255,255,255,.97);border:1px solid #D5E5FA;
 border-radius:11px;color:#21395A;min-height:43px;}
.st-key-hero_banner [data-baseweb="select"] * {color:#203450!important;}
.st-key-hero_banner [data-testid="stSelectSlider"] {padding-top:5px;}
.st-key-hero_banner [data-testid="stSelectSlider"] [data-baseweb="slider"] {margin-top:9px;}
.st-key-hero_banner [data-testid="stSelectSlider"] [data-baseweb="slider"] * {color:white!important;}
.st-key-hero_banner [data-testid="stSelectSlider"] [data-testid="stTickBar"] {color:#DDEEFF!important;}
.st-key-hero_banner [data-testid="stWidgetInstructions"] {color:#D0E0FF;}
.st-key-hero_banner [data-testid="stRadio"] p {color:#EEF5FF!important;font-weight:700;}
.st-key-hero_banner [data-testid="stRadio"] [role="radiogroup"] {gap:20px;}
.st-key-hero_banner [data-testid="stRadio"] [data-baseweb="radio"] {accent-color:#69E8D4;}
.scope-card {position:relative;min-height:145px;padding:19px 20px;border-radius:19px;
 background:white;border:1px solid #DFE8F4;box-shadow:0 5px 24px rgba(27,52,104,.06);
 overflow:hidden;margin-bottom:9px;}
.scope-card:before {content:'';position:absolute;inset:0 auto auto 0;width:100%;height:4px;
 background:var(--accent);}
.scope-card.feature {background:linear-gradient(130deg,#204DA5 0%,#5366E1 100%);
 border-color:transparent;box-shadow:0 15px 29px rgba(43,75,183,.20);}
.scope-icon {position:absolute;right:16px;top:15px;font-size:1.55rem;opacity:.77;}
.scope-label {color:#697D96;font-size:.78rem;font-weight:800;letter-spacing:.01em;}
.scope-number {font-size:clamp(2rem,3vw,2.95rem);line-height:1.15;color:#172E52;
 font-weight:800;letter-spacing:-.055em;margin:9px 0 5px;white-space:nowrap;}
.scope-foot {color:#7889A1;font-size:.75rem;line-height:1.38;}
.scope-card.feature .scope-label,.scope-card.feature .scope-number {color:white;}
.scope-card.feature .scope-foot {color:#D5E4FF;}
.scope-card.feature .scope-icon {opacity:.72;}
.kpi {position:relative;overflow:hidden;padding:21px 22px 18px;border-radius:19px;background:white;
 border:1px solid #E5ECF5;box-shadow:0 5px 21px rgba(29,52,105,.047);min-height:156px;margin-bottom:8px;}
.kpi:before {content:'';position:absolute;left:0;top:0;height:4px;width:100%;background:var(--accent);}
.kpi .k-label {font-size:.8rem;font-weight:800;color:#738399;}
.kpi .k-value {font-weight:800;font-size:clamp(1.45rem,2.2vw,2.15rem);letter-spacing:-.04em;
 color:#162B49;margin:13px 0 9px;white-space:nowrap;}
.kpi .k-foot {font-size:.76rem;line-height:1.5;color:#7689A1;}
.kpi.prominent {background:linear-gradient(125deg,#153F83,#3C66D4);border-color:transparent;
 box-shadow:0 13px 30px rgba(41,83,180,.16);}
.kpi.prominent:before {background:rgba(255,255,255,.22);}
.kpi.prominent .k-label,.kpi.prominent .k-value {color:white;}
.kpi.prominent .k-foot {color:#E0EAFF;}
.kpi.prominent.negative {background:linear-gradient(122deg,#9D384F,#D65B6E);}
.kpi.prominent.positive {background:linear-gradient(122deg,#0B6B69,#1DB7A0);}
.status-line {font-size:.78rem;color:#62748A;margin:2px 0 16px;}
.status-line b {color:#253A57;}
.view-title {margin:4px 0 9px;font-size:1.2rem;font-weight:850;letter-spacing:-.025em;color:#18325B;}
.section-title {font-size:1.19rem;font-weight:800;color:#1A2F51;letter-spacing:-.02em;margin:8px 0 4px;}
.section-sub {font-size:.87rem;color:#71849A;line-height:1.5;margin:0 0 12px;}
.insight {border-radius:15px;padding:15px 18px;background:linear-gradient(95deg,#E8FAF4,#F0F6FF);
 border:1px solid #D9EDE9;color:#244B67;font-size:.88rem;line-height:1.65;margin:10px 0 15px;}
.insight.warn {background:linear-gradient(95deg,#FFF1E9,#FFF9F2);border-color:#F4DFD3;color:#73533D;}
.insight strong {color:#143F65;}
.explain {font-size:.82rem;line-height:1.64;color:#667990;background:#F2F6FC;border:1px solid #E4ECF8;
 border-radius:13px;padding:11px 15px;margin-top:9px;margin-bottom:21px;}
.explain b {color:#24496C;}
.risk-grid {display:flex;flex-direction:column;gap:9px;margin:5px 0 18px;}
.risk {display:flex;align-items:flex-start;gap:11px;border-radius:13px;padding:12px 14px;
 background:white;border:1px solid #E4EAF4;}
.risk-dot {width:9px;height:9px;border-radius:50%;margin-top:6px;flex-shrink:0;}
.risk-content {font-size:.84rem;color:#5E7188;line-height:1.55;}
.risk-content b {color:#253D5B;}
.demo-foot {color:#8394A6;font-size:.79rem;border-top:1px solid #DDE6F0;margin-top:32px;padding-top:14px;}
@media (max-width:900px) {
 .st-key-hero_banner{padding:21px 17px!important;border-radius:19px;}
 .block-container{padding-left:1rem;padding-right:1rem;}
 .scope-card{min-height:122px}.scope-number{font-size:2.1rem;}
 .kpi{min-height:130px;padding:17px}.kpi .k-value{font-size:1.56rem;}
}
</style>
"""

# Elementy wspólne: identyczna szerokość przycisków i animacja otwierania.
EXTRA_CSS = """
<style>
/* Nawigacja nie jest już radiem z nierównymi etykietami, lecz menu kafelkowym. */
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
 width:100%;display:flex;flex-direction:column;align-items:stretch;gap:9px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
 display:flex;align-items:center;box-sizing:border-box;width:100%;min-height:54px;
 padding:13px 15px!important;gap:0;justify-content:flex-start;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label [data-baseweb="radio"] {
 flex:0 0 0;max-width:0;opacity:0;overflow:hidden;margin:0!important;padding:0!important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label [data-testid="stMarkdownContainer"] {
 margin:0!important;padding:0!important;flex:1;min-width:0;text-align:left;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label p {
 margin:0!important;line-height:1.45;font-size:.9rem!important;
}
[data-testid="stSidebar"] .stButton button {width:100%;min-height:38px;border-radius:11px;}
[data-testid="stSidebar"] [data-testid="stToggle"] label {display:flex;justify-content:space-between;}
.st-key-savings_settings {border:1px solid rgba(108,144,189,.25);border-radius:16px;
 padding:13px 18px!important;background:rgba(75,125,205,.055);margin:5px 0 18px;}
.savings-hero {border:1px solid rgba(28,172,147,.22);background:linear-gradient(110deg,#E5F8F5,#E8EFFF);
 border-radius:17px;padding:18px 20px;margin:10px 0 16px;color:#24516B;line-height:1.65;}
.savings-hero b {color:#173F67;}
.savings-warning {font-size:.83rem;line-height:1.65;opacity:.86;}
.intro-overlay {position:fixed;inset:0;z-index:999999;display:flex;align-items:center;
 justify-content:center;overflow:hidden;pointer-events:none;
 background:radial-gradient(ellipse at 45% 23%,#294FA0 0%,#101F42 57%,#091328 100%);
 animation:intro-hide .65s ease 2.85s forwards;}
.intro-content {position:relative;width:min(760px,94vw);height:400px;text-align:center;color:white;}
.intro-heading {position:absolute;top:20px;left:0;right:0;font-size:clamp(2rem,5vw,3.45rem);
 font-weight:850;letter-spacing:-.05em;animation:intro-text .7s .15s backwards;}
.intro-heading span {color:#55E6C6;}
.intro-subtitle {position:absolute;top:100px;left:0;right:0;color:#CAE0FF;font-size:.98rem;
 font-weight:550;animation:intro-text .8s .55s backwards;}
.intro-city {position:absolute;left:4%;right:4%;bottom:28px;height:215px;
 display:flex;gap:13px;align-items:flex-end;justify-content:center;}
.intro-building {flex:1;max-width:98px;height:var(--height);border:1px solid rgba(149,224,255,.45);
 border-radius:7px 7px 0 0;position:relative;transform-origin:bottom center;
 background:linear-gradient(158deg,#407EC4 0%,#204D8B 55%,#142E61 100%);
 box-shadow:0 4px 45px rgba(89,166,244,.12),inset 6px 0 rgba(255,255,255,.08);
 animation:intro-rise .8s cubic-bezier(.18,.84,.25,1.08) var(--delay) both;}
.intro-building:before {content:'';position:absolute;inset:15px 11px 12px;
 background-image:repeating-linear-gradient(90deg,transparent 0 13px,rgba(103,220,241,.77) 13px 20px,transparent 20px 29px),
 repeating-linear-gradient(0deg,transparent 0 18px,rgba(255,221,130,.42) 18px 25px,transparent 25px 36px);
 background-blend-mode:screen;opacity:.68;animation:intro-lights .7s 1.3s backwards;}
.intro-building:after {content:'';position:absolute;bottom:0;left:-6px;right:-6px;
 height:4px;background:#63D9E4;box-shadow:0 0 17px #59E5DF;}
.intro-glow {position:absolute;bottom:5px;left:12%;right:12%;height:22px;
 border-radius:50%;filter:blur(22px);background:rgba(48,213,201,.37);}
.intro-caption {position:absolute;bottom:0;left:0;right:0;color:#A9CBE7;font-size:.82rem;
 letter-spacing:.17em;text-transform:uppercase;animation:intro-text .7s 1.6s backwards;}
@keyframes intro-rise {from{transform:scaleY(.07) translateY(20px);opacity:.15}to{transform:scaleY(1);opacity:1}}
@keyframes intro-text {from{transform:translateY(13px);opacity:0}to{transform:translateY(0);opacity:1}}
@keyframes intro-lights {from{opacity:0}to{opacity:.68}}
@keyframes intro-hide {to{opacity:0;visibility:hidden}}
@media(max-width:700px){.intro-content{height:325px}.intro-city{height:175px;gap:7px;bottom:35px}
 .intro-subtitle{top:88px;font-size:.86rem}.intro-building:before{inset:12px 6px}}
@media(prefers-reduced-motion:reduce){.intro-overlay{animation:intro-hide .15s .3s forwards}
 .intro-building,.intro-heading,.intro-subtitle,.intro-caption{animation:none!important}}
</style>
"""

DARK_CSS = """
<style>
/* Ciemny motyw także dla własnych komponentów HTML, kontrolek i Plotly. */
.stApp {background:linear-gradient(160deg,#0B1425 0%,#111F37 49%,#0C1529 100%)!important;
 color:#EAF2FF!important;}
[data-testid="stSidebar"]{background:linear-gradient(165deg,#091326 0%,#172643 62%,#103F49 100%)!important;}
.scope-card,.kpi,.risk,[data-testid="stPlotlyChart"] {
 background:#15243D!important;border-color:#30435F!important;
 box-shadow:0 8px 24px rgba(0,0,0,.16)!important;}
.scope-card.feature {background:linear-gradient(125deg,#224B9E,#6B4DC1)!important;}
.scope-label,.kpi .k-label {color:#B6C9E4!important;}
.scope-number,.kpi .k-value {color:#F2F7FF!important;}
.scope-foot,.kpi .k-foot,.risk-content,.status-line,.demo-foot,
.section-sub,.savings-warning {color:#B5C8DE!important;}
.scope-card.feature .scope-label,.scope-card.feature .scope-number,
.kpi.prominent .k-label,.kpi.prominent .k-value {color:white!important;}
.scope-card.feature .scope-foot,.kpi.prominent .k-foot {color:#DCE7FF!important;}
.kpi.prominent {background:linear-gradient(125deg,#234C95,#445FD1)!important;}
.kpi.prominent.positive{background:linear-gradient(125deg,#0A6661,#168F85)!important;}
.kpi.prominent.negative{background:linear-gradient(125deg,#81334D,#B94A69)!important;}
.view-title,.section-title,.status-line b,.risk-content b,.explain b,.insight strong{
 color:#F2F6FF!important;}
.explain {background:#162742!important;border-color:#314562!important;color:#C0D2EB!important;}
.insight{background:linear-gradient(95deg,#173C3A,#1C3152)!important;
 border-color:#2D6A63!important;color:#D3EDEB!important;}
.insight.warn{background:linear-gradient(95deg,#4A302D,#302A38)!important;
 border-color:#704A45!important;color:#FFE2D6!important;}
.savings-hero{background:linear-gradient(100deg,#133B3A,#1B3058)!important;
 border-color:#2C776F!important;color:#CDEBE8!important;}
.savings-hero b{color:#E8FBF6!important;}
.st-key-savings_settings{background:rgba(70,117,181,.12)!important;border-color:#344967!important;}
[data-testid="stDataFrame"]{border-color:#30425F!important;}
[data-testid="stExpander"]{border-color:#354763!important;background:#15243C!important;border-radius:14px;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] p{color:#E2EAF7!important;}
[data-testid="stWidgetLabel"] p {color:#D6E3F5!important;}
[data-testid="stDownloadButton"] button{background:#365FAD!important;color:white!important;}
[data-testid="stDownloadButton"] button:hover{background:#4876D1!important;}
[data-testid="stRadio"] div[role="radiogroup"] label {color:#E4EEFF;}
[data-testid="stSelectbox"] div[data-baseweb="select"]>div,
[data-testid="stMultiSelect"] div[data-baseweb="select"]>div {background:#1D2E4B;color:#E8F1FF;border-color:#3B5377;}
[data-testid="stSelectbox"] div[data-baseweb="select"] span,
[data-testid="stMultiSelect"] div[data-baseweb="select"] span {color:#E8F1FF;}
.st-key-hero_banner [data-baseweb="select"]>div{background:#EFF5FF!important;}
.demo-foot{border-top-color:#32445D!important;}
</style>
"""

st.markdown(CSS + EXTRA_CSS + (DARK_CSS if DARK else ""), unsafe_allow_html=True)

# Jednorazowa animacja pierwszego wejścia; nie odtwarza się przy filtrowaniu.
if not st.session_state.get("intro_seen", False):
    blocks = [("57%", ".10s"), ("83%", ".22s"), ("72%", ".37s"),
              ("100%", ".51s"), ("64%", ".68s"), ("88%", ".83s"),
              ("54%", "1.00s")]
    skyline = "".join(
        f'<div class="intro-building" style="--height:{h};--delay:{d}"></div>'
        for h, d in blocks
    )
    st.markdown(
        '<div class="intro-overlay" role="img" aria-label="Animowane budynki witają użytkownika">'
        '<div class="intro-content"><div class="intro-heading">Spółdzielnia<span>360</span></div>'
        '<div class="intro-subtitle">Nowoczesne zarządzanie nieruchomościami i kosztami</div>'
        f'<div class="intro-city"><div class="intro-glow"></div>{skyline}</div>'
        '<div class="intro-caption">Executive Intelligence</div></div></div>',
        unsafe_allow_html=True,
    )
    st.session_state["intro_seen"] = True


def fmt(value: float, dec: int = 0) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", " ")


def money(value: float, compact: bool = True) -> str:
    sign = "−" if value < 0 else ""
    value = abs(float(value))
    if compact and value >= 1_000_000:
        return f"{sign}{fmt(value / 1_000_000, 2)} mln zł"
    if compact and value >= 10_000:
        return f"{sign}{fmt(value / 1_000, 1)} tys. zł"
    return f"{sign}{fmt(value)} zł"


def pp(value: float | None, digits: int = 1) -> str:
    return "brak danych" if value is None or pd.isna(value) else f"{fmt(value, digits)}%"


def safe(value: object) -> str:
    return html.escape(str(value))


def kpi(label: str, value: str, foot: str, accent: str = "blue",
        prominent: bool = False) -> None:
    variant = (" prominent negative" if accent == "red" else
               " prominent positive" if accent == "teal" else " prominent") if prominent else ""
    st.markdown(
        f'<div class="kpi{variant}" style="--accent:{C[accent]}">'
        f'<div class="k-label">{safe(label)}</div>'
        f'<div class="k-value">{safe(value)}</div>'
        f'<div class="k-foot">{safe(foot)}</div></div>',
        unsafe_allow_html=True,
    )


def scope_tile(label: str, value: str, foot: str, icon: str,
               accent: str = "blue", feature: bool = False) -> None:
    kind = " feature" if feature else ""
    st.markdown(
        f'<div class="scope-card{kind}" style="--accent:{C[accent]}">'
        f'<div class="scope-icon">{safe(icon)}</div>'
        f'<div class="scope-label">{safe(label)}</div>'
        f'<div class="scope-number">{safe(value)}</div>'
        f'<div class="scope-foot">{safe(foot)}</div></div>',
        unsafe_allow_html=True,
    )


def section(name: str, sub: str = "") -> None:
    st.markdown(f'<div class="section-title">{safe(name)}</div>'
                f'<div class="section-sub">{safe(sub)}</div>', unsafe_allow_html=True)


def explain(text: str) -> None:
    st.markdown(f'<div class="explain"><b>Jak to czytać:</b> {safe(text)}</div>',
                unsafe_allow_html=True)


def insight(text: str, warning: bool = False) -> None:
    css = "insight warn" if warning else "insight"
    st.markdown(f'<div class="{css}">{safe(text)}</div>', unsafe_allow_html=True)


def risk_list(items: list[tuple[str, str, str]]) -> None:
    parts = ['<div class="risk-grid">']
    for title, description, color in items:
        parts.append(f'<div class="risk"><span class="risk-dot" style="background:{C[color]}"></span>'
                     f'<div class="risk-content"><b>{safe(title)}</b> — {safe(description)}</div></div>')
    parts.append('</div>')
    st.markdown(''.join(parts), unsafe_allow_html=True)


def style_plot(fig: go.Figure, height: int = 326, legend: bool = True) -> go.Figure:
    fig.update_layout(
        template="plotly_dark" if DARK else "plotly_white", height=height,
        margin=dict(l=17, r=19, t=30, b=37),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, Arial, sans-serif", color=C["ink"], size=12),
        legend=dict(orientation="h", y=1.16, x=0, title_text=""), showlegend=legend,
        hoverlabel=dict(bgcolor="#20324F" if DARK else "white",
                        font_color="#F1F7FF" if DARK else "#182B46", font_size=12),
    )
    fig.update_xaxes(showgrid=False, showline=False, tickfont=dict(color=C["muted"]))
    fig.update_yaxes(gridcolor=C["grid"], zerolinecolor=C["grid"], tickfont=dict(color=C["muted"]))
    return fig


def show(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, key=key,
                    config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def monthly(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    return df.groupby("month", as_index=False)[fields].sum().sort_values("month")


def export_excel(costs: pd.DataFrame, arrears: pd.DataFrame,
                 funds: pd.DataFrame, projects: pd.DataFrame) -> bytes:
    """Raport odzwierciedla filtry okresu i budynków (projekty są migawką demo)."""
    bymonth = monthly(costs, ["plan", "actual"])
    bymonth["roznica"] = bymonth["actual"] - bymonth["plan"]
    bycat = costs.groupby("category", as_index=False)[["plan", "actual"]].sum()
    bycat["roznica"] = bycat["actual"] - bycat["plan"]
    debts = monthly(arrears, ["charges", "payments", "arrears_total"])
    reserve = monthly(funds, ["inflow", "outflow", "closing"])
    tabs = {
        "Koszty_miesieczne": bymonth,
        "Kategorie": bycat,
        "Naleznosci": debts,
        "Fundusz_remontowy": reserve,
        "Remonty_DEMO": projects[["building", "scope", "status", "budget", "spent"]],
    }
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl", datetime_format="YYYY-MM-DD") as writer:
        for tab, frame in tabs.items():
            frame.to_excel(writer, sheet_name=tab, index=False)
            ws = writer.sheets[tab]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            from openpyxl.styles import Font, PatternFill
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="234E9C")
            for col in ws.columns:
                letter = col[0].column_letter
                longest = max((len(str(cell.value)) for cell in list(col)[:90]
                               if cell.value is not None), default=11)
                ws.column_dimensions[letter].width = min(max(longest + 3, 14), 32)
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def data() -> dict[str, pd.DataFrame]:
    return make_demo_data()


D = data()
B = D["buildings"]
ALL = D["costs"]
MONTHS = sorted(pd.to_datetime(ALL["month"].unique()))
NAME = B.set_index("building_id")["building"].to_dict()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NAWIGACJA — wyłącznie w pasku bocznym
# FILTRY — wszystkie wewnątrz głównego banera
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VIEWS = [
    "🏠  Pulpit prezesa",
    "📈  Koszty i oszczędności",
    "💳  Finanse i należności",
    "🛠️  Remonty i ryzyka",
]
with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">🏢 Spółdzielnia<span>360</span></div>'
        '<div class="sidebar-mini">EXECUTIVE · PANEL ZARZĄDCZY</div>'
        '<div class="sidebar-label">NAWIGACJA</div>', unsafe_allow_html=True,
    )
    NAV = st.radio("Wybierz widok", VIEWS, key="sidebar_nav", label_visibility="collapsed")
    st.markdown("---")
    st.toggle("🌙 Tryb ciemny", key="dark_mode",
              help="Przełącza kolory całego kokpitu, także wykresów.")
    if st.button("↻ Odtwórz powitanie", key="replay_intro", use_container_width=True):
        st.session_state["intro_seen"] = False
        st.rerun()
    st.markdown(
        '<div class="sidebar-note">'
        '◉ <b>4 widoki zarządcze</b><br>'
        'Filtry okresu i budynków są dostępne w banerze u góry.<br><br>'
        '✦ Wszystkie kwoty i adresy są demonstracyjne.'
        '</div>', unsafe_allow_html=True,
    )

with st.container(key="hero_banner"):
    st.markdown(
        '<div class="hero-kicker">CENTRUM DECYZJI · SPÓŁDZIELNIA MIESZKANIOWA</div>'
        '<div class="hero-heading">Spółdzielnia<em>360</em> / Executive</div>'
        '<div class="hero-description">Jedno miejsce do nadzoru nad budynkami, finansami '
        'i remontami. Wybierz zakres analizy poniżej.</div>'
        '<div class="hero-filters">FILTRY ANALIZY</div>', unsafe_allow_html=True,
    )
    if NAV == VIEWS[1]:
        f_period, f_estate, f_buildings, f_cost_group = st.columns(
            [1.55, 0.90, 1.20, 1.05], gap="medium")
    else:
        f_period, f_estate, f_buildings = st.columns(
            [1.65, 0.95, 1.35], gap="medium")
    with f_period:
        start, end = st.select_slider(
            "Okres analizy", options=MONTHS, value=(MONTHS[-12], MONTHS[-1]),
            format_func=lambda x: pd.Timestamp(x).strftime("%m.%Y"),
            key="banner_period", help="Domyślnie 12 ostatnich dostępnych miesięcy.",
        )
    with f_estate:
        chosen_estate = st.selectbox(
            "Osiedle", ["Wszystkie osiedla"] + sorted(B["estate"].unique().tolist()),
            key="banner_estate",
        )
    matching = B if chosen_estate == "Wszystkie osiedla" else B[B["estate"] == chosen_estate]
    allowable = matching["building_id"].tolist()
    with f_buildings:
        # Brak zaznaczenia oznacza wszystkie budynki danego osiedla;
        # nie wyświetlamy 24 domyślnych tagów, które zasłoniłyby baner.
        picked = st.multiselect(
            "Budynki", allowable, default=[],
            key="banner_buildings", format_func=lambda x: f"{x} · {NAME[x]}",
            placeholder="Wszystkie budynki",
            help="Pozostaw puste, aby uwzględnić wszystkie budynki wybranego osiedla.",
        )
    ids = [x for x in picked if x in allowable] if picked else allowable
    if NAV == VIEWS[1]:
        with f_cost_group:
            sel_group = st.selectbox(
                "Grupa kosztów",
                ["Wszystkie", "Media", "Eksploatacja", "Administracja", "Pozostałe"],
                key="banner_monitor_group",
            )
        # Wybór trybu również znajduje się w banerze, nie w treści strony.
        cost_mode = st.radio(
            "Tryb analizy", ["📊 Analiza kosztów", "🔎 Szukanie oszczędności"],
            horizontal=True, key="cost_mode",
        )
    st.markdown(
        '<div class="hero-foot">'
        f'<span class="hero-badge">📅 {start:%m.%Y} – {end:%m.%Y}</span>'
        f'<span class="hero-badge">🏢 {len(ids)} z {len(B)} budynków</span>'
        '<span class="hero-badge">✦ DANE DEMONSTRACYJNE</span>'
        '</div>', unsafe_allow_html=True,
    )

if not ids:
    st.info("Nie znaleziono budynków spełniających ustawione filtry.")
    st.stop()

selected_B = B[B["building_id"].isin(ids)]
COST = period_filter(D["costs"], start, end, ids)
AR = period_filter(D["receivables"], start, end, ids)
FUND = period_filter(D["funds"], start, end, ids)
LAST_AR = period_latest(D["receivables"], end, ids)
LAST_FUND = period_latest(D["funds"], end, ids)
PROJECT = D["projects"].loc[D["projects"]["building_id"].isin(ids)].copy()
CHECKS = D["inspections"].loc[D["inspections"]["building_id"].isin(ids)].copy()
area = float(selected_B["area_m2"].sum())
units = int(selected_B["units"].sum())
months = len(pd.date_range(start, end, freq="MS"))
ACT = float(COST["actual"].sum())
PLAN = float(COST["plan"].sum())
DIFF = ACT - PLAN
DEBT = float(LAST_AR["arrears_total"].sum())
RESERVE = float(LAST_FUND["closing"].sum())
OVERDUE = int((CHECKS["status"] == "Po terminie").sum())
ANOMALIES = cost_anomalies(D["costs"], ids, end, 20, 1000)

# Wskaźniki skali nadzorowanego zasobu są widoczne na KAŻDYM widoku.
coverage = st.columns([1.15, 1, 1, 1], gap="medium")
with coverage[0]:
    scope_tile("BUDYNKI POD NADZOREM", str(len(ids)),
               f"Objęte analizą · {len(B)} w bazie", "🏢", "blue", feature=True)
with coverage[1]:
    scope_tile("LOKALE MIESZKALNE", fmt(units),
               "Łącznie w wybranych budynkach", "🔑", "teal")
with coverage[2]:
    scope_tile("POWIERZCHNIA", f"{fmt(area / 1_000, 1)} tys.",
               "m² powierzchni zasobu", "📐", "purple")
with coverage[3]:
    scope_tile("OSIEDLA W NADZORZE", str(selected_B["estate"].nunique()),
               f"Spośród {B['estate'].nunique()} osiedli w bazie", "🧭", "amber")

st.markdown(
    f'<div class="status-line">Widok: <b>{safe(NAV)}</b> &nbsp;·&nbsp; '
    f'Analiza: <b>{start:%m.%Y} – {end:%m.%Y}</b> &nbsp;·&nbsp; '
    f'Status przeglądów na <b>{AS_OF:%d.%m.%Y}</b></div>',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANALIZATOR OSZCZĘDNOŚCI (podwidok Monitoringu kosztów; 4 główne widoki)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def render_savings() -> None:
    section("Wyszukiwarka potencjalnych oszczędności",
            "Wykrywa kosztowne odchylenia względem mediany budynków porównawczych. "
            "To lista obszarów do audytu — nie obietnica oszczędności.")
    st.markdown(
        '<div class="savings-hero"><b>🔎 Gdzie warto szukać?</b> '
        'Porównujemy koszty tej samej kategorii i tych samych miesięcy na 1 m². '
        'Wyniki są przeliczane na 12 miesięcy, a suwak określa przyjęty procent możliwej '
        'redukcji nadwyżki. Dane syntetyczne — żadna kwota nie jest potwierdzoną oszczędnością.'
        '</div>', unsafe_allow_html=True,
    )
    with st.container(key="savings_settings"):
        st.markdown("**Parametry scenariusza — możesz je zmieniać**")
        s1, s2 = st.columns(2, gap="large")
        with s1:
            share = st.slider("Zakładany udział nadwyżki możliwy do ograniczenia",
                              min_value=10, max_value=70, value=35, step=5,
                              format="%d%%", key="savings_share",
                              help="Przykładowe założenie, nie oszczędność potwierdzona audytem.")
        with s2:
            gap = st.slider("Minimalny koszt powyżej mediany porównawczej",
                           min_value=5, max_value=40, value=15, step=5,
                           format="%d%%", key="savings_gap")
    opps = savings_opportunities(D["costs"], B, ids, start, end,
                                 recoverable_share=share / 100,
                                 min_gap_pct=gap)
    if sel_group != "Wszystkie":
        opps = opps.loc[opps["group"] == sel_group].copy()
    estimate = float(opps["potential_year"].sum()) if not opps.empty else 0.0
    if months < 6:
        st.warning("Wybrano mniej niż 6 miesięcy. Roczne przeliczenie jest bardzo "
                   "wrażliwe na sezonowość. Do oceny kosztów ogrzewania wybierz najlepiej pełne 12 miesięcy.")
    if opps.empty:
        st.info("Przy wybranym progu i filtrach nie znaleziono kategorii "
                "o kosztach wyraźnie powyżej mediany. Spróbuj obniżyć próg lub wybrać więcej budynków.")
        with st.expander("Jak działa wyszukiwarka?"):
            st.markdown("Wykorzystuje koszty na m²/miesiąc z tego samego okresu, "
                        "benchmark medianowy i przyjęty procent odzyskiwalności. "
                        "Nie uwzględnia stanu instalacji, cen i taryf ani audytu technicznego.")
        return
    metrics = st.columns(4, gap="medium")
    with metrics[0]:
        kpi("Potencjał scenariuszowy / rok", money(estimate),
            "Hipoteza, nie gwarantowana oszczędność", "teal", prominent=True)
    with metrics[1]:
        kpi("Obszary do sprawdzenia", str(len(opps)),
            "Unikatowe kombinacje budynek–kategoria", "blue")
    with metrics[2]:
        kpi("Budynki z sygnałami", str(opps["building_id"].nunique()),
            f"Spośród {len(ids)} wybranych budynków", "purple")
    with metrics[3]:
        top = opps.iloc[0]
        kpi("Największy pojedynczy sygnał", money(float(top["potential_year"])),
            f"{top['building']} · {top['category']} / rok", "amber")

    sec1, sec2 = st.columns([1.4, 1], gap="large")
    with sec1:
        section("Ranking hipotez optymalizacji", "10 najsilniejszych sygnałów według rocznego scenariusza")
        rank = opps.head(10).copy().iloc[::-1]
        labels = rank["building"].astype(str) + " · " + rank["category"].astype(str)
        fig = go.Figure(go.Bar(
            y=labels, x=rank["potential_year"], orientation="h",
            marker=dict(color=C["teal"], opacity=.88),
            text=[money(x) for x in rank["potential_year"]], textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}<br>Scenariusz: %{x:,.0f} zł/rok<extra></extra>",
        ))
        fig.update_layout(margin=dict(l=14, r=95, t=28, b=35))
        show(style_plot(fig, max(340, 45 * len(rank)), False), "savings_rank")
        explain("Każdy słupek to budynek i kategoria. Kwota jest ograniczoną "
                "symulacją redukcji nadwyżki wobec mediany podobnych budynków; "
                "nie odejmuje kosztu wdrożenia ani inwestycji.")
    with sec2:
        section("Największe obszary do analizy", "Suma scenariusza w kategoriach — bez podwójnego liczenia")
        sums = (opps.groupby("category", as_index=False)["potential_year"].sum()
                .sort_values("potential_year", ascending=False).head(6))
        fig = go.Figure(go.Pie(
            labels=sums["category"], values=sums["potential_year"], hole=.65,
            marker_colors=[CATEGORY_COLORS.get(c, C["blue"]) for c in sums["category"]],
            textinfo="percent", hovertemplate="%{label}: %{value:,.0f} zł/rok<extra></extra>",
        ))
        fig.update_layout(annotations=[dict(text="SZANSE", x=.5, y=.5,
                                             showarrow=False,
                                             font=dict(color=C["ink"], size=15))])
        show(style_plot(fig, 345, False), "savings_categories")
        explain("Większy segment oznacza więcej sygnałów potencjalnego ograniczenia kosztów "
                "przy przyjętych założeniach. Nie oznacza, że kategoria jest źle zarządzana.")

    section("Plan weryfikacji — od czego zacząć?", "Najpierw audyt i faktury, dopiero potem decyzje o zmianach")
    recommended = []
    for row in opps.head(3).itertuples(index=False):
        recommended.append((
            f"{row.building} · {row.category} · {money(row.potential_year)} / rok",
            f"Odchylenie: +{fmt(row.gap_pct,1)}% względem benchmarku. {row.action}",
            "amber" if row.plan_delta_pct <= 0 else "red",
        ))
    risk_list(recommended)

    with st.expander("Tabela pełnych wyników i eksport CSV", expanded=False):
        view = opps[["building", "category", "group", "actual_per_m2_month",
                     "benchmark_per_m2_month", "gap_pct", "potential_year", "action"]].copy()
        view.columns = ["Budynek", "Kategoria", "Grupa", "Koszt zł/m²/mies.",
                        "Mediana zł/m²/mies.", "Odchylenie %", "Scenariusz zł/rok",
                        "Zalecane sprawdzenie"]
        st.dataframe(view.style.format({"Koszt zł/m²/mies.": "{:,.2f}",
                                       "Mediana zł/m²/mies.": "{:,.2f}",
                                       "Odchylenie %": "+{:,.1f}%",
                                       "Scenariusz zł/rok": "{:,.0f}"}),
                     hide_index=True, use_container_width=True)
        st.download_button("⬇ Pobierz listę możliwości (CSV)",
                           view.to_csv(index=False, sep=";").encode("utf-8-sig"),
                           "Spoldzielnia360_hipotezy_oszczednosci.csv",
                           mime="text/csv", use_container_width=True,
                           key="savings_csv")
    with st.expander("Metodologia i ograniczenia obliczeń"):
        st.markdown(
            "**Co porównujemy:** dla każdej kategorii wyliczamy miesięczny koszt zł/m² "
            "dla całego wybranego okresu. Punktem odniesienia jest mediana tej kategorii "
            "w całym demonstracyjnym zasobie; dla ogrzewania — przy dostatecznej liczbie "
            "obiektów — w grupie podobnego rocznika, a dla dźwigów tylko w budynkach z windą. "
            "Zestawienia nie obejmują podatków i obowiązkowych opłat.\n\n"
            "**Jak powstaje kwota:** szacowana nadwyżka ponad medianę × wybrany "
            "udział możliwej redukcji, maksymalnie 20% wydatku danej kategorii. "
            "Następnie przeliczamy to na 12 miesięcy. Wartości nie uwzględniają kosztów "
            "inwestycji, harmonogramów ani ewentualnych oszczędności już zrealizowanych.\n\n"
            "**Ograniczenia:** różnice mogą wynikać ze stanu budynków, liczby mieszkańców, "
            "innego zakresu usług, taryf, pogody i wieku instalacji. To **nie jest audyt "
            "energetyczny ani finansowy**. Niczego nie zmieniaj automatycznie na podstawie rankingu."
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1 · PREZES / BIEŻĄCA SYTUACJA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if NAV == VIEWS[0]:
    section("Sytuacja spółdzielni w 30 sekund",
            "Koszty odnoszą się do wybranego okresu; zaległości i fundusz to stany na koniec okresu.")
    cols = st.columns(4)
    with cols[0]:
        kpi("Wydatki w okresie", money(ACT), f"{fmt(ACT / area / months, 2)} zł/m² miesięcznie", "blue", prominent=True)
    with cols[1]:
        kpi("Realizacja planu", pp(100 * ACT / PLAN) if PLAN else "—",
            f"Odchylenie: {money(DIFF)}", "red" if DIFF > 0 else "teal", prominent=True)
    with cols[2]:
        kpi("Zaległości na koniec", money(DEBT), "Stan należności przeterminowanych", "amber")
    with cols[3]:
        kpi("Fundusz remontowy", money(RESERVE), "Saldo, nie wolne środki", "teal")

    if DIFF > 0:
        insight(f"Wydatki przekraczają plan o {money(DIFF)} ({pp(pct_change(ACT, PLAN))}). "
                "Sprawdź zakładkę Monitoring kosztów, aby ustalić, które kategorie odpowiadają za różnicę.", True)
    else:
        insight(f"Wydatki są niższe od planu o {money(abs(DIFF))}. "
                "To korzystne odchylenie, ale warto sprawdzić, czy nie wynika z opóźnionych faktur.")

    a, b = st.columns([1.55, 1])
    with a:
        section("Plan a wykonanie miesiąc po miesiącu", "Gdzie koszty zaczynają odbiegać od założeń?")
        trend = monthly(COST, ["actual", "plan"])
        f = go.Figure()
        f.add_trace(go.Scatter(x=trend["month"], y=trend["actual"],
                               name="Wykonanie", mode="lines+markers",
                               line=dict(color=C["blue"], width=3), marker=dict(size=6),
                               fill="tozeroy", fillcolor="rgba(55,101,236,.085)"))
        f.add_trace(go.Scatter(x=trend["month"], y=trend["plan"], name="Plan",
                               mode="lines", line=dict(color=C["amber"], width=2.5, dash="dot")))
        show(style_plot(f, 336), "board_trend")
        explain("Niebieska linia to rzeczywiste wydatki, pomarańczowa — plan. "
                "Utrzymująca się przewaga niebieskiej linii oznacza ryzyko przekroczenia budżetu.")
    with b:
        section("Na co wydajemy najwięcej?", "Udział głównych grup w kosztach całego okresu")
        groups = COST.groupby("group", as_index=False)["actual"].sum().sort_values("actual", ascending=False)
        colors = {"Media": C["blue"], "Eksploatacja": C["teal"],
                  "Administracja": C["purple"], "Pozostałe": C["amber"]}
        f = go.Figure(go.Pie(labels=groups["group"], values=groups["actual"],
                             hole=.68, marker_colors=[colors.get(x, C["blue"]) for x in groups["group"]],
                             textinfo="percent", textposition="outside",
                             hovertemplate="%{label}: %{value:,.0f} zł<extra></extra>"))
        f.update_layout(annotations=[dict(text="KOSZTY", x=.5, y=.5, showarrow=False,
                                          font=dict(size=17, color=C["ink"]))])
        show(style_plot(f, 336, False), "board_structure")
        top_group = str(groups.iloc[0]["group"])
        top_pct = 100 * groups.iloc[0]["actual"] / ACT if ACT else 0
        explain(f"Największy udział ma grupa „{top_group}” ({pp(top_pct)}). "
                "Od niej warto rozpocząć rozmowę o możliwych oszczędnościach.")

    section("3 sygnały do sprawdzenia", "Wskazówki do działania, nie automatyczne oceny pracy zarządu.")
    old = float(LAST_AR["over_90_days"].sum())
    signal = [
        ("Koszty ponad normę", f"{len(ANOMALIES)} kategorii i budynków z dużym wzrostem r/r "
         f"w {end:%m.%Y} (próg +20% i +1 000 zł).", "red" if len(ANOMALIES) else "teal"),
        ("Dług ponad 90 dni", f"{money(old)} — {pp(100 * old / DEBT if DEBT else 0)} wszystkich zaległości "
         "w ostatnim miesiącu analizy.", "amber"),
        ("Przeglądy techniczne", f"{OVERDUE} pozycji po terminie na {AS_OF:%d.%m.%Y}; "
         "szczegóły w zakładce Remonty i ryzyka.", "red" if OVERDUE else "teal"),
    ]
    risk_list(signal)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2 · MONITORING KOSZTÓW — ANALIZA PRZYCZYN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if NAV == VIEWS[1]:
    if cost_mode == "📊 Analiza kosztów":
        section("Monitoring kosztów", "Dla prezesa i księgowości: co drożeje, co przekracza plan i w którym budynku?")
        # Filtr grupy kosztowej jest na banerze u góry, obok okresu i budynków.
        subset = COST if sel_group == "Wszystkie" else COST.loc[COST["group"] == sel_group]
        base = float(subset["actual"].sum())
        planned = float(subset["plan"].sum())
        delta = base - planned
        t = st.columns(3)
        with t[0]:
            kpi("Koszt wybranej grupy", money(base), "Suma za zaznaczony okres", "blue")
        with t[1]:
            kpi("Różnica wobec planu", money(delta),
                f"{pp(pct_change(base, planned))} wobec planu", "red" if delta > 0 else "teal")
        with t[2]:
            kpi("Koszt na m² / miesiąc", f"{fmt(base / area / months, 2)} zł",
                "Do porównywania skali budynków", "purple")

        left, right = st.columns([1.4, 1])
        with left:
            section("Czy wydatki mieszczą się w budżecie?", "Suma miesięczna dla wybranej grupy")
            tr = monthly(subset, ["actual", "plan"])
            fig = go.Figure()
            fig.add_trace(go.Bar(x=tr["month"], y=tr["actual"], name="Wykonanie",
                                 marker_color=C["blue"], marker_line_width=0))
            fig.add_trace(go.Scatter(x=tr["month"], y=tr["plan"], name="Plan",
                                     mode="lines+markers", line=dict(color=C["amber"], width=3)))
            fig.update_layout(bargap=.39)
            show(style_plot(fig, 333), "cost_monthly")
            explain("Słupki przekraczające linię planu wskazują miesiące wymagające wyjaśnienia. "
                    "Samo przekroczenie nie przesądza o błędzie — możliwe są faktury sezonowe lub przeniesione wydatki.")
        with right:
            section("Najdroższe kategorie", "Sześć kategorii o największym udziale w wydatkach")
            ranks = (subset.groupby("category", as_index=False)["actual"].sum()
                     .nlargest(6, "actual").sort_values("actual"))
            fig = go.Figure(go.Bar(x=ranks["actual"], y=ranks["category"], orientation="h",
                                   marker=dict(color=[CATEGORY_COLORS.get(x, C["blue"]) for x in ranks["category"]]),
                                   text=[money(v) for v in ranks["actual"]], textposition="outside",
                                   cliponaxis=False))
            fig.update_layout(margin=dict(l=14, r=60, t=30, b=34))
            fig.update_xaxes(tickformat="~s")
            show(style_plot(fig, 333, False), "cost_categories")
            if not ranks.empty:
                explain(f"Największą pozycją jest „{ranks.iloc[-1]['category']}”. "
                        "Warto rozbić ją na budynki i sprawdzić faktury, taryfy oraz skalę zużycia.")

        section("Które budynki są najdroższe?", "TOP 8 według średniego miesięcznego kosztu na 1 m²")
        bybuilding = subset.groupby("building_id", as_index=False)["actual"].sum().merge(
            selected_B[["building_id", "building", "area_m2"]], on="building_id")
        bybuilding["per_m2"] = bybuilding["actual"] / bybuilding["area_m2"] / months
        bybuilding = bybuilding.nlargest(8, "per_m2").sort_values("per_m2")
        fig = go.Figure(go.Bar(x=bybuilding["per_m2"], y=bybuilding["building"],
                               orientation="h", marker=dict(color=C["teal"],
                               opacity=.86), text=[f"{fmt(x, 2)} zł" for x in bybuilding["per_m2"]],
                               textposition="outside", cliponaxis=False))
        fig.update_layout(margin=dict(l=16, r=70, t=19, b=35))
        show(style_plot(fig, 310, False), "cost_buildings")
        explain("Wskaźnik zł/m²/mies. ułatwia porównanie różnych wielkości budynków. "
                "Różnice mogą wynikać z wieku, technologii, liczby wind lub sposobu ogrzewania — ranking nie ocenia gospodarności.")

        section("Alerty kosztowe w ostatnim miesiącu", "Wzrost względem tego samego miesiąca poprzedniego roku")
        alerts = ANOMALIES if sel_group == "Wszystkie" else ANOMALIES.loc[
            ANOMALIES["category"].map(CATEGORY_GROUPS) == sel_group]
        if alerts.empty:
            st.success("Brak przekroczeń progów alertu dla tej grupy w ostatnim miesiącu.")
        else:
            alerttab = alerts.head(6).copy()
            alerttab["Budynek"] = alerttab["building_id"].map(NAME)
            alerttab = alerttab.rename(columns={"category": "Kategoria", "difference": "Wzrost (zł)",
                                                "yoy_pct": "Zmiana r/r (%)"})
            st.dataframe(alerttab[["Budynek", "Kategoria", "Wzrost (zł)", "Zmiana r/r (%)"]]
                         .style.format({"Wzrost (zł)": "{:,.0f}", "Zmiana r/r (%)": "{:.1f}%"}),
                         hide_index=True, use_container_width=True)
        explain("Alert powstaje, gdy w danym budynku i kategorii koszt wzrósł co najmniej o 20% "
                "i o 1 000 zł rok do roku. Dane są fikcyjne; alert wskazuje pozycję do weryfikacji faktur.")

    else:
        render_savings()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3 · KSIĘGOWY / PŁYNNOŚĆ I NALEŻNOŚCI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if NAV == VIEWS[2]:
    section("Finanse i należności", "Płynność, ściągalność opłat i środki na remonty w jednym miejscu.")
    charges = float(LAST_AR["charges"].sum())
    payments = float(LAST_AR["payments"].sum())
    longdebt = float(LAST_AR["over_90_days"].sum())
    inflows = float(FUND["inflow"].sum())
    outflows = float(FUND["outflow"].sum())
    a = st.columns(4)
    with a[0]:
        kpi("Ściągalność bieżących opłat", pp(100 * payments / charges if charges else 0),
            "Wpłaty / naliczenia w ostatnim miesiącu", "teal")
    with a[1]:
        kpi("Zaległości przeterminowane", money(DEBT), "Stan na koniec okresu", "amber")
    with a[2]:
        kpi("Fundusz remontowy", money(RESERVE), "Saldo na koniec okresu", "blue")
    with a[3]:
        kpi("Wypływy z funduszu", money(outflows), f"Wpływy w okresie: {money(inflows)}", "purple")

    l, r = st.columns(2)
    with l:
        section("Czy zaległości rosną?", "Saldo wszystkich zaległości na koniec kolejnych miesięcy")
        debtrend = monthly(AR, ["arrears_total"])
        fig = go.Figure(go.Scatter(x=debtrend["month"], y=debtrend["arrears_total"],
                                   mode="lines+markers", line=dict(color=C["red"], width=3),
                                   fill="tozeroy", fillcolor="rgba(228,93,106,.10)"))
        show(style_plot(fig, 320, False), "fin_debt")
        if len(debtrend) >= 2:
            change_debt = float(debtrend.iloc[-1]["arrears_total"] - debtrend.iloc[0]["arrears_total"])
            direction = "zwiększył" if change_debt > 0 else "zmniejszył"
            explain(f"W badanym okresie stan zaległości {direction} się o {money(abs(change_debt))} "
                    "między pierwszym a ostatnim miesiącem. Porównujemy stany, nie sumę kolejnych miesięcy.")
        else:
            explain("To stan należności na koniec jednego miesiąca, a nie nowy dług powstały tylko w tym miesiącu.")
    with r:
        section("Jak zmienia się fundusz?", "Łączne saldo funduszu remontowego na koniec miesięcy")
        fundtrend = monthly(FUND, ["closing"])
        fig = go.Figure(go.Scatter(x=fundtrend["month"], y=fundtrend["closing"],
                                   mode="lines+markers", line=dict(color=C["teal"], width=3),
                                   fill="tozeroy", fillcolor="rgba(18,169,148,.10)"))
        show(style_plot(fig, 320, False), "fin_fund")
        explain("Saldo pokazuje wartość na koniec danego miesiąca. Nie należy sumować sald "
                "z kolejnych miesięcy. Część środków może być przeznaczona na już zatwierdzone prace.")

    l, r = st.columns([1, 1.2])
    with l:
        section("Wiek zadłużenia", "Struktura zaległości na koniec okresu")
        ages = [float(LAST_AR["days_0_30"].sum()),
                float(LAST_AR["days_31_90"].sum()), longdebt]
        fig = go.Figure(go.Pie(labels=["0–30 dni", "31–90 dni", "Ponad 90 dni"], values=ages,
                               hole=.62, marker_colors=[C["teal"], C["amber"], C["red"]],
                               textinfo="percent", textposition="outside"))
        show(style_plot(fig, 304, False), "fin_aging")
        explain("Im większy udział zobowiązań starszych niż 90 dni, tym większa potrzeba "
                "indywidualnej analizy windykacji i uzgodnienia sald.")
    with r:
        section("Budynki z największymi zaległościami", "Pięć pozycji priorytetowych dla księgowości")
        debt_buildings = LAST_AR.merge(selected_B[["building_id", "building", "units"]], on="building_id")
        debt_buildings["Na lokal (zł)"] = debt_buildings["arrears_total"] / debt_buildings["units"]
        debt_buildings = debt_buildings.nlargest(5, "arrears_total")
        debt_buildings = debt_buildings.rename(columns={"building": "Budynek",
                    "arrears_total": "Zaległości (zł)", "over_90_days": "Ponad 90 dni (zł)"})
        st.dataframe(debt_buildings[["Budynek", "Zaległości (zł)", "Na lokal (zł)", "Ponad 90 dni (zł)"]]
                     .style.format({"Zaległości (zł)": "{:,.0f}", "Na lokal (zł)": "{:,.0f}",
                                    "Ponad 90 dni (zł)": "{:,.0f}"}),
                     hide_index=True, use_container_width=True)
        explain("Kwoty dotyczą całych budynków, nie poszczególnych mieszkańców. "
                "Wskaźnik na lokal pozwala porównywać obiekty o różnej liczbie mieszkań.")

    insight("Dane są zagregowane do budynków i nie zawierają danych osobowych. "
            "W rzeczywistej spółdzielni wymagane będą uprawnienia ról, bezpieczne importy i zasady ochrony danych.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4 · PREZES / REMONTY, KONTROLE, RAPORT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if NAV == VIEWS[3]:
    section("Remonty i ryzyka operacyjne",
            f"Statusy projektów i przeglądów są migawką danych demo na {AS_OF:%d.%m.%Y}, niezależną od filtra okresu kosztów.")
    ongoing = PROJECT[PROJECT["status"] == "W realizacji"]
    planned_projects = PROJECT[PROJECT["status"] == "Planowany"]
    lowfund = LAST_FUND.loc[LAST_FUND["closing"] < LAST_FUND["minimum_reserve"]]
    a = st.columns(4)
    with a[0]:
        kpi("Remonty w realizacji", str(len(ongoing)), f"Zaplanowane: {len(planned_projects)}", "blue")
    with a[1]:
        kpi("Budżet projektów", money(float(PROJECT["budget"].sum())),
            "Wszystkie projekty w wybranych budynkach", "purple")
    with a[2]:
        kpi("Przeglądy po terminie", str(OVERDUE), "Wymagają pilnego sprawdzenia", "red")
    with a[3]:
        kpi("Fundusze poniżej progu", str(len(lowfund)),
            "Liczba budynków poniżej umownej rezerwy", "amber")

    l, r = st.columns([1.28, 1])
    with l:
        section("Budżet remontów kontra wydatki", "Osiem największych projektów według budżetu")
        projects_top = PROJECT.nlargest(8, "budget").sort_values("budget")
        fig = go.Figure()
        fig.add_trace(go.Bar(y=projects_top["scope"] + " · " + projects_top["building"],
                             x=projects_top["budget"], name="Budżet", orientation="h",
                             marker_color="#C8D5F7"))
        fig.add_trace(go.Bar(y=projects_top["scope"] + " · " + projects_top["building"],
                             x=projects_top["spent"], name="Wydano", orientation="h",
                             marker_color=C["purple"]))
        fig.update_layout(barmode="group")
        show(style_plot(fig, 365), "renov_projects")
        explain("Budżet dotyczy całego projektu, a „wydano” to skumulowane wydatki ujęte "
                "w bazie do października 2026. Niska realizacja nie musi oznaczać opóźnienia.")
    with r:
        section("Stan przeglądów technicznych", "Liczba przeglądów w trzech grupach pilności")
        status_order = ["Po terminie", "Wkrótce", "Zaplanowany"]
        counts = CHECKS["status"].value_counts().reindex(status_order, fill_value=0)
        fig = go.Figure(go.Bar(x=counts.values, y=status_order, orientation="h",
                               marker_color=[C["red"], C["amber"], C["teal"]],
                               text=counts.values, textposition="outside"))
        fig.update_layout(yaxis=dict(categoryorder="array", categoryarray=list(reversed(status_order))))
        show(style_plot(fig, 365, False), "renov_checks")
        explain("Po terminie = data przeglądu już minęła; „Wkrótce” = do 60 dni. "
                "To wyłącznie scenariusz demo — w realnym systemie liczy się status wykonania i dokumentacja.")

    section("Najpilniejsze sprawy do decyzji", "Priorytety na posiedzenie zarządu")
    priorities = []
    if OVERDUE:
        priorities.append(("Przeglądy po terminie", f"{OVERDUE} pozycji wymaga sprawdzenia terminów i protokołów.", "red"))
    if len(lowfund):
        priorities.append(("Niedostateczna rezerwa", f"{len(lowfund)} budynków ma saldo funduszu poniżej progu porównawczego.", "amber"))
    overspent = PROJECT[(PROJECT["spent"] > PROJECT["budget"]) & (PROJECT["status"] != "Planowany")]
    if not overspent.empty:
        priorities.append(("Przekroczenie budżetu remontu", f"{len(overspent)} projektów przekroczyło limit kosztowy.", "red"))
    if not priorities:
        priorities = [("Bez pilnych sygnałów", "Nie wykryto przekroczeń według przyjętych progów.", "teal")]
    risk_list(priorities[:3])

    with st.expander("Pokaż szczegóły przeglądów i projektów"):
        st.markdown("**Najbliższe terminy i kontrole po terminie**")
        urgent = CHECKS[CHECKS["status"].isin(["Po terminie", "Wkrótce"])].sort_values("days_to_due").head(10)
        if urgent.empty:
            st.info("Brak pilnych przeglądów.")
        else:
            visible = urgent[["building", "inspection", "due_date", "status"]].rename(
                columns={"building": "Budynek", "inspection": "Przegląd",
                         "due_date": "Termin", "status": "Status"})
            st.dataframe(visible, hide_index=True, use_container_width=True)
        st.markdown("**Projekty aktywne lub planowane**")
        visible = PROJECT[PROJECT["status"] != "Zakończony"].head(12)[
            ["building", "scope", "status", "budget", "spent"]].rename(
            columns={"building": "Budynek", "scope": "Zakres", "status": "Status",
                     "budget": "Budżet (zł)", "spent": "Wydano (zł)"})
        st.dataframe(visible.style.format({"Budżet (zł)": "{:,.0f}", "Wydano (zł)": "{:,.0f}"}),
                     hide_index=True, use_container_width=True)

    section("Raport do zarządu", "Pobierz zestawienie Excel uwzględniające wybrane budynki i okres")
    report = export_excel(COST, AR, FUND, PROJECT)
    st.download_button("⬇ Pobierz raport Excel", data=report,
                       file_name=f"Spoldzielnia360_Raport_{end:%Y-%m}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True, key="executive_report")
    st.caption("Raport zawiera zagregowane koszty, należności, saldo funduszu i status remontów. "
               "Wszystkie wartości są demonstracyjne.")

st.markdown(
    '<div class="demo-foot">Spółdzielnia360 · Executive Edition · '
    'Dane syntetyczne 2024–2026 · Motyw jasny i ciemny · Cztery widoki · Bez danych osobowych · '
    'Wersja demonstracyjna do testowania koncepcji produktu, a nie do podejmowania realnych decyzji finansowych.</div>',
    unsafe_allow_html=True,
)
