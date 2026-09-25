import streamlit as st
import qrcode
from io import BytesIO
import re

# --- FUNKCIJE ---
def ocisti_racun(racun_str):
    samo_cifre = re.sub(r'\D', '', str(racun_str))
    if 5 < len(samo_cifre) < 18:
        kod_banke = samo_cifre[:3]
        kontrolni_broj = samo_cifre[-2:]
        partija_racuna = samo_cifre[3:-2]
        partija_sa_nulama = partija_racuna.zfill(13)
        return f"{kod_banke}{partija_sa_nulama}{kontrolni_broj}"
    return samo_cifre.zfill(18)

def formatiraj_za_prikaz(racun_18_cifara):
    if len(racun_18_cifara) == 18:
        return f"{racun_18_cifara[:3]}-{racun_18_cifara[3:-2]}-{racun_18_cifara[-2:]}"
    return racun_18_cifara

def formatiraj_broj_sa_tackom(broj):
    return f"{int(broj):,}".replace(",", ".")

# --- KONFIGURACIJA ---
st.set_page_config(page_title="Podela troškova", layout="centered")

if "tema_dark" not in st.session_state:
    st.session_state.tema_dark = True
if "reset_kljuc" not in st.session_state:
    st.session_state.reset_kljuc = 0
if "clanovi_univerzalni" not in st.session_state:
    st.session_state.clanovi_univerzalni = []

# --- CSS TEME ---
css_dark = """
<style>
.stApp { background-color: #081c15; color: #ffffff !important; }
h1,h2,h3,h4,h5,h6,p,span,label,div { color: #ffffff !important; }
input,textarea,select { background-color:#1b4332 !important; color:#ffffff !important; border:1px solid #2d6a4f !important; border-radius:8px !important; }
input::placeholder { color:#95d5b2 !important; }
.stButton button { background-color:#2d6a4f !important; color:white !important; border-radius:8px; font-weight:600; }
.stButton button:hover { background-color:#40916c !important; }
div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] { background-color:#1b4332 !important; border:1px solid #2d6a4f !important; border-radius:12px !important; }
div[data-testid="stMetricValue"] { color:#52b788 !important; font-size:1.8rem; }
</style>
"""

css_light = """
<style>
.stApp { background-color:#f8f9fa; color:#1b4332 !important; }
h1,h2,h3,h4,h5,h6,p,span,label,div { color:#1b4332 !important; }
input,textarea,select { background-color:#ffffff !important; color:#1b4332 !important; border:1px solid #d8f3dc !important; border-radius:8px !important; }
input::placeholder { color:#74c69d !important; }
.stButton button { background-color:#74c69d !important; color:#1b4332 !important; border-radius:8px; font-weight:600; }
.stButton button:hover { background-color:#52b788 !important; }
div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] { background-color:#ffffff !important; border:1px solid #d8f3dc !important; border-radius:12px !important; }
div[data-testid="stMetricValue"] { color:#2d6a4f !important; font-size:1.8rem; }
</style>
"""

# --- NASLOV ---
st.title("💰 Podela troškova")

# --- LIGHT/DARK SWITCH (instant, radi na telefonu) ---
switch_html = """
<div style="display:flex;align-items:center;gap:10px;margin-top:10px;">
    <span style="font-size:1.1rem;font-weight:600;">Tema:</span>
    <label class="switch">
      <input type="checkbox" id="themeToggle">
      <span class="slider round"></span>
    </label>
</div>

<style>
.switch { position: relative; display: inline-block; width: 52px; height: 28px; }
.switch input { display:none; }
.slider { position: absolute; cursor: pointer; top:0; left:0; right:0; bottom:0;
          background-color:#ccc; transition:.4s; border-radius:34px; }
.slider:before { position:absolute; content:""; height:22px; width:22px; left:3px; bottom:3px;
                 background-color:white; transition:.4s; border-radius:50%; }
input:checked + .slider { background-color:#2d6a4f; }
input:checked + .slider:before { transform:translateX(24px); }
</style>

<script>
const themeToggle = document.getElementById("themeToggle");
themeToggle.checked = %s;

themeToggle.addEventListener("change", function() {
    const theme = themeToggle.checked ? "dark" : "light";
    window.parent
