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
    window.parent.postMessage({theme: theme}, "*");
});
</script>
""" % ("true" if st.session_state.tema_dark else "false")

st.markdown(switch_html, unsafe_allow_html=True)

# --- JS LISTENER ---
msg = st.experimental_get_query_params().get("theme_msg", [""])[0]
if msg:
    st.session_state.tema_dark = (msg == "dark")

# --- PRIMENA TEME ---
st.markdown(css_dark if st.session_state.tema_dark else css_light, unsafe_allow_html=True)

# --- EXPLAINER ---
with st.expander("Kako ovo radi?"):
    st.write("""
    1. Unesi podatke primaoca.
    2. Unesi iznos i dostavu.
    3. Odaberi metod podele.
    4. Generiši QR kodove.
    """)

# --- PODACI O PRIMAOcu ---
st.subheader("💳 Podaci o primaocu")

with st.container(border=True):
    col_p1, col_p2 = st.columns(2)
    moje_ime = col_p1.text_input("Primalac:", value="", key="user_name", placeholder="Ime i prezime")
    moj_racun_unos = col_p2.text_input("Broj računa primaoca:", value="", key="user_bank", placeholder="npr. 160-12345678999-12")

moj_racun = re.sub(r'\D', '', moj_racun_unos)
c_racun = ocisti_racun(moj_racun) if moj_racun else ""
prikaz_racuna = formatiraj_za_prikaz(c_racun) if c_racun else ""

st.markdown(f"""
<div style="padding:8px 12px; background-color:{'#1b4332' if st.session_state.tema_dark else '#ffffff'};
            border-radius:6px; border-left:4px solid #52b788; margin-top:5px; margin-bottom:5px;">
    <span style="font-size:1rem; font-weight:500;">Validan račun:
        <b style="color:{'#ffffff' if st.session_state.tema_dark else '#1b4332'};">{prikaz_racuna}</b>
    </span>
</div>
""", unsafe_allow_html=True)

st.divider()

# --- TROŠAK ---
sufiks = st.session_state.reset_kljuc

st.subheader("🧾 Podaci o trošku")
with st.container(border=True):
    c1, c2 = st.columns(2)
    v_racun = c1.number_input("Iznos sa računa (RSD):", min_value=0, value=0, step=1, format="%d", key=f"racun_num_{sufiks}")
    v_dostava = c2.number_input("Dostava (RSD):", min_value=0, value=0, step=1, format="%d", key=f"dostava_num_{sufiks}")

if st.button("🔄 Novi iznos", use_container_width=True):
    st.session_state.reset_kljuc += 1
    st.session_state.clanovi_univerzalni = []
    st.rerun()

suma_ukupno = v_racun + v_dostava
st.metric(label="Ukupno", value=f"{formatiraj_broj_sa_tackom(suma_ukupno)} RSD")
st.divider()

# --- METODA ---
st.markdown('<p style="font-size:1.35rem; font-weight:700; margin-bottom:8px;">Metoda podele:</p>', unsafe_allow_html=True)
nacin = st.pills("Metoda podele:", ["Ravnopravno", "Ručni unos"], default="Ravnopravno", label_visibility="collapsed", key=f"nacin_{sufiks}")

finalni_dugovi = {}
validna_podela = False

# --- RAVNOPRAVNO ---
if nacin == "Ravnopravno":
    with st.container(border=True):
        broj_ljudi = st.number_input("Ukupan broj osoba:", min_value=1, value=2, step=1, key=f"br_ljudi_{sufiks}")
        if broj_ljudi > 1:
            po_osobi = round(suma_ukupno / broj_ljudi)
            st.info(f"Po osobi: **{formatiraj_broj_sa_tackom(po_osobi)} RSD**")
            finalni_dugovi["Zajednički"] = po_osobi
            validna_podela = True

# --- RUČNI UNOS ---
else:
    def dodaj_direktno():
        ime = st.session_state.novo_ime_input.strip()
        if ime and ime not in st.session_state.clanovi_univerzalni:
            st.session_state.clanovi_univerzalni.append(ime)
        st.session_state.novo_ime_input = ""

    with st.container(border=True):
        st.text_input("Dodaj učesnika (Enter):", key="novo_ime_input", on_change=dodaj_direktno)

        aktivni = st.session_state.clanovi_univerzalni
        if aktivni:
            br = len(aktivni)
            fiksna_dostava = round(v_dostava / br) if br else 0

            st.markdown(f"""
            <div style="background-color:{'#1b4332' if st.session_state.tema_dark else '#ffffff'};
                        padding:12px; border-radius:8px; border-left:5px solid #52b788; margin-bottom:20px;">
                Učešće u dostavi po osobi: <b>{formatiraj_broj_sa_tackom(fiksna_dostava)} RSD</b>
            </div>
            """, unsafe_allow_html=True)

            trenutna_suma = 0
            for o in list(aktivni):
                col1, col2, col3 = st.columns([2, 2, 0.6])
                with col1:
                    st.markdown(f"<p style='padding-top:8px; font-weight:600;'>{o}:</p>", unsafe_allow_html=True)
                with col2:
                    dug = st.number_input(f"Iznos_{o}", min_value=0, value=0, step=1, format="%d",
                                          label_visibility="collapsed", key=f"rucni_num_{o}_{sufiks}")
                with col3:
                    if st.button("❌", key=f"obrisi_{o}_{sufiks}"):
                        st.session_state.clanovi_univerzalni.remove(o)
                        del st.session_state[f"rucni_num_{o}_{sufiks}"]
                        st.rerun()

                finalni_dugovi[o] = dug
                trenutna_suma += dug

            ostatak = suma_ukupno - trenutna_suma
            if abs(ostatak) < 0.01:
                validna_podela = True
            elif ostatak > 0:
                st.warning(f"Preostalo: **{formatiraj_broj_sa_tackom(ostatak)} RSD**")
            else:
                st.error(f"Višak: **{formatiraj_broj_sa_tackom(abs(ostatak))} RSD**")

            st.button("Obriši celu listu", on_click=lambda: st.session_state.clanovi_univerzalni.clear())

# --- QR KODOVI ---
st.divider()
if validna_podela and suma_ukupno > 0:
    if st.button("⚡ GENERIŠI QR KODOVE", use_container_width=True, type="primary"):
        if not moje_ime or not moj_racun:
            st.error("⚠️ Popuni podatke o primaocu!")
        else:
            if nacin == "Ravnopravno":
                iznos = finalni_dugovi["Zajednički"]
                iz_fmt = "{:.2f}".format(float(iznos)).replace('.', ',')
                ips = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Podela"
                qr = qrcode.make(ips)
                buf = BytesIO()
                qr.save(buf, format="PNG")

                with st.container(border=True):
                    _, col, _ = st.columns([1, 2, 1])
                    with col:
                        st.image(buf.getvalue(), caption=f"Iznos: {formatiraj_broj_sa_tackom(iznos)} RSD", use_container_width=True)

            else:
                for ime, dug in finalni_dugovi.items():
                    if dug > 0:
                        iz_fmt = "{:.2f}".format(float(dug)).replace('.', ',')
                        ips = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:{ime}"
                        qr = qrcode.make(ips)
                        buf = BytesIO()
                        qr.save(buf, format="PNG")

                        with st.container(border=True):
                            st.markdown(f"#### {ime} - {formatiraj_broj_sa_tackom(dug)} RSD")
                            _, col, _ = st.columns([1, 2, 1])
                            with col:
                                st.image(buf.getvalue(), use_container_width=True)

# --- FOOTER ---
st.divider()
st.caption("Napomena: Aplikacija je namenjena isključivo za IPS plaćanja. Proverite podatke pre potvrde.")
st.caption("Disclaimer: This app is designed solely for Serbian IPS payments.")
