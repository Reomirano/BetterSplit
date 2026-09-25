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

if "reset_kljuc" not in st.session_state:
    st.session_state.reset_kljuc = 0
if "clanovi_univerzalni" not in st.session_state:
    st.session_state.clanovi_univerzalni = []
if "tema_dark" not in st.session_state:
    st.session_state.tema_dark = True

# --- LIGHT / DARK TOGGLE ---
top_col1, top_col2 = st.columns([3, 1])
with top_col1:
    st.title("💰 Podela troškova")
with top_col2:
    st.session_state.tema_dark = st.toggle("Dark mode", value=st.session_state.tema_dark)

# --- CSS ZA TEME ---
css_dark = """
    <style>
    .stApp {
        background-color: #081c15;
        color: #ffffff !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label, div, 
    .stMarkdown, .stText, [data-testid="stMarkdownContainer"] p, 
    [data-testid="stWidgetLabel"] {
        color: #ffffff !important;
    }

    div[data-testid="stExpander"] summary span {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #b7e4c7 !important;
    }
    div[data-testid="stExpander"] summary p::before {
        content: "📖 ";
        font-size: 1.95rem;
    }

    div.stButton > button[kind="secondary"],
    div.stButton > button[kind="primary"] {
        font-size: 1.65rem !important;
        padding: 0.9rem 1.5rem !important;
    }

    input, textarea, select {
        background-color: #1b4332 !important;
        color: #ffffff !important;
        border: 1px solid #2d6a4f !important;
        border-radius: 8px !important;
    }
    
    input::placeholder, textarea::placeholder {
        color: #95d5b2 !important;
        opacity: 1 !important;
    }
    
    .stButton button {
        background-color: #2d6a4f !important;
        color: white !important;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease-in-out;
    }
    .stButton button * {
        color: white !important;
    }
    .stButton button:hover {
        background-color: #40916c !important;
        transform: translateY(-1px);
    }
    
    div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1b4332 !important;
        border: 1px solid #2d6a4f !important;
        border-radius: 12px !important;
    }
    
    div[data-testid="stMetricValue"] {
        color: #52b788 !important;
        font-size: 1.8rem;
    }
    </style>
"""

css_light = """
    <style>
    .stApp {
        background-color: #f8f9fa;
        color: #1b4332 !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, span, label, div, 
    .stMarkdown, .stText, [data-testid="stMarkdownContainer"] p, 
    [data-testid="stWidgetLabel"] {
        color: #1b4332 !important;
    }

    div[data-testid="stExpander"] summary span {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #2d6a4f !important;
    }
    div[data-testid="stExpander"] summary p::before {
        content: "📖 ";
        font-size: 1.95rem;
    }

    div.stButton > button[kind="secondary"],
    div.stButton > button[kind="primary"] {
        font-size: 1.65rem !important;
        padding: 0.9rem 1.5rem !important;
    }

    input, textarea, select {
        background-color: #ffffff !important;
        color: #1b4332 !important;
        border: 1px solid #d8f3dc !important;
        border-radius: 8px !important;
    }
    
    input::placeholder, textarea::placeholder {
        color: #74c69d !important;
        opacity: 1 !important;
    }
    
    .stButton button {
        background-color: #74c69d !important;
        color: #1b4332 !important;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease-in-out;
    }
    .stButton button * {
        color: #1b4332 !important;
    }
    .stButton button:hover {
        background-color: #52b788 !important;
        transform: translateY(-1px);
    }
    
    div[data-testid="stExpander"], div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border: 1px solid #d8f3dc !important;
        border-radius: 12px !important;
    }
    
    div[data-testid="stMetricValue"] {
        color: #2d6a4f !important;
        font-size: 1.8rem;
    }
    </style>
"""

st.markdown(css_dark if st.session_state.tema_dark else css_light, unsafe_allow_html=True)

with st.expander("Kako ovo radi?"):
    st.write("""
    1. Unesi podatke primaoca (ime i broj računa).
    2. Unesi iznos sa računa i cenu dostave.
    3. Odaberi metodu:
       - Ravnopravno: broj ljudi, univerzalni QR kod.
       - Ručni unos: imena učesnika i pojedinačni iznosi.
    4. Svako u mBankingu odabere IPS i očita svoj QR kod.
    """)

st.subheader("💳 Podaci o primaocu")

with st.container(border=True):
    col_p1, col_p2 = st.columns(2)
    moje_ime = col_p1.text_input("Primalac:", value="", key="user_name", placeholder="Ime i prezime")

    moj_racun_unos = col_p2.text_input(
        "Broj računa primaoca:", 
        value="", 
        key="user_bank", 
        placeholder="npr. 160-12345678999-12"
    )

moj_racun = re.sub(r'\D', '', moj_racun_unos)

c_racun = ocisti_racun(moj_racun) if moj_racun else ""
prikaz_racuna = formatiraj_za_prikaz(c_racun) if c_racun else ""

st.markdown(f"""
    <div style="padding: 8px 12px; background-color: {'#1b4332' if st.session_state.tema_dark else '#ffffff'}; border-radius: 6px; border-left: 4px solid #52b788; margin-top: 5px; margin-bottom: 5px;">
        <span style="font-size: 1rem; font-weight: 500; color: #b7e4c7 !important;">
            Validan račun: <b style="color: {'#ffffff' if st.session_state.tema_dark else '#1b4332'} !important;">{prikaz_racuna}</b>
        </span>
    </div>
""", unsafe_allow_html=True)

st.divider()

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

st.markdown('<p style="font-size: 1.35rem; font-weight: 700; margin-bottom: 8px;">Metoda podele:</p>', unsafe_allow_html=True)
nacin = st.pills("Metoda podele:", ["Ravnopravno", "Ručni unos"], default="Ravnopravno", label_visibility="collapsed", key=f"nacin_{sufiks}")

finalni_dugovi = {}
validna_podela = False

if nacin == "Ravnopravno":
    with st.container(border=True):
        broj_ljudi = st.number_input("Ukupan broj osoba:", min_value=1, value=2, step=1, key=f"br_ljudi_{sufiks}")
        if broj_ljudi > 1:
            po_osobi = suma_ukupno / broj_ljudi
            po_osobi_zaokruzeno = round(po_osobi)
            po_osobi_str = formatiraj_broj_sa_tackom(po_osobi_zaokruzeno)
            st.info(f"Po osobi: **{po_osobi_str} RSD**")
            finalni_dugovi["Zajednički"] = po_osobi_zaokruzeno
            validna_podela = True

else:
    def dodaj_direktno():
        ime = st.session_state.novo_ime_input.strip()
        if ime:
            if ime not in st.session_state.clanovi_univerzalni:
                st.session_state.clanovi_univerzalni.append(ime)
        st.session_state.novo_ime_input = ""

    with st.container(border=True):
        st.text_input("Dodaj učesnika na listu (potvrdi na Enter):", key="novo_ime_input", on_change=dodaj_direktno)
        
        aktivni_clanovi = st.session_state.clanovi_univerzalni
        
        if aktivni_clanovi:
            br_ucesnika = len(aktivni_clanovi)
            fiksna_dostava = v_dostava / br_ucesnika if br_ucesnika > 0 else 0
            fiksna_dostava_str = formatiraj_broj_sa_tackom(round(fiksna_dostava))
            
            st.markdown(f"""
                <div style="background-color: {'#1b4332' if st.session_state.tema_dark else '#ffffff'}; padding: 12px; border-radius: 8px; border-left: 5px solid #52b788; margin-bottom: 20px;">
                    <span>Učešće u dostavi po osobi: <b>{fiksna_dostava_str} RSD</b></span>
                </div>
            """, unsafe_allow_html=True)
            
            trenutna_suma = 0
            for o in list(aktivni_clanovi):
                col_i1, col_i2, col_i3 = st.columns([2, 2, 0.6])
                with col_i1:
                    st.markdown(f"<p style='padding-top: 8px; font-weight: 600;'>{o}:</p>", unsafe_allow_html=True)
                with col_i2:
                    v_dug = st.number_input(
                        f"Iznos_{o}", 
                        min_value=0, 
                        value=0, 
                        step=1, 
                        format="%d", 
                        label_visibility="collapsed",
                        key=f"rucni_num_{o}_{sufiks}"
                    )
                with col_i3:
                    if st.button("❌", key=f"obrisi_{o}_{sufiks}", help=f"Ukloni {o}"):
                        st.session_state.clanovi_univerzalni.remove(o)
                        if f"rucni_num_{o}_{sufiks}" in st.session_state:
                            del st.session_state[f"rucni_num_{o}_{sufiks}"]
                        st.rerun()
                
                finalni_dugovi[o] = v_dug
                trenutna_suma += v_dug
            
            ostatak = suma_ukupno - trenutna_suma
            if abs(ostatak) < 0.01:
                validna_podela = True
            elif ostatak > 0:
                st.warning(f"Preostalo: **{formatiraj_broj_sa_tackom(ostatak)} RSD**")
            else:
                st.error(f"Višak: **{formatiraj_broj_sa_tackom(abs(ostatak))} RSD**")
            
            def obrisi_listu_callback():
                st.session_state.clanovi_univerzalni = []

            st.write("")
            st.button("Obriši celu listu", on_click=obrisi_listu_callback)

# --- QR SEKCIJA + LINK-SHARE ---
st.divider()
if validna_podela and suma_ukupno > 0:
    if st.button("⚡ GENERIŠI QR KODOVE", use_container_width=True, type="primary"):
        if not moje_ime or not moj_racun:
            st.error("⚠️ Popuni podatke o primaocu na vrhu strane!")
        else:
            if nacin == "Ravnopravno":
                iz_fmt = "{:.2f}".format(float(finalni_dugovi['Zajednički'])).replace('.', ',')
                ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Podela racuna"
                qr_img = qrcode.make(ips_data)
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                
                with st.container(border=True):
                    _, col_qr, _ = st.columns([1, 2, 1])
                    with col_qr:
                        zajednicki_iznos_str = formatiraj_broj_sa_tackom(finalni_dugovi['Zajednički'])
                        st.image(buf.getvalue(), caption=f"Iznos: {zajednicki_iznos_str} RSD", use_container_width=True)
            else:
                for ime, dug in finalni_dugovi.items():
                    if dug > 0:
                        iz_fmt = "{:.2f}".format(float(dug)).replace('.', ',')
                        ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Rucak-{ime}"
                        qr_img = qrcode.make(ips_data)
                    
                        buf = BytesIO()
                        qr_img.save(buf, format="PNG")
                        
                        with st.container(border=True):
                            dug_prikaz = formatiraj_broj_sa_tackom(dug)
                            st.markdown(f"#### {ime} - {dug_prikaz} RSD")
                            _, col_qr_inner, _ = st.columns([1, 2, 1])
                            with col_qr_inner:
                                st.image(buf.getvalue(), use_container_width=True)

            # LINK-SHARE PANEL
            base_url = "https://bettersplit.streamlit.app"
            mode_param = "ravnopravno" if nacin == "Ravnopravno" else "rucni"
            link_share_url = f"{base_url}?mode={mode_param}&racun={v_racun}&dostava={v_dostava}"

            with st.container(border=True):
                st.markdown("#### Pošalji link drugima")
                st.write("Kopiraj link ispod i pošalji u Viber/WhatsApp:")
                st.text_input("Link za deljenje:", value=link_share_url, key="share_link", label_visibility="collapsed")
                st.caption("Link ne sadrži imena niti broj tekućeg, samo iznos i način podele.")

st.write("") 
st.divider() 
st.caption("Napomena: Aplikacija je namenjena isključivo za plaćanja u okviru IPS sistema Narodne banke Srbije. Pre potvrde plaćanja, obavezno proverite ispravnost podataka. Autor ne snosi odgovornost za pogrešne uplate.")
st.caption("Disclaimer: This app is designed solely for Serbian IPS payments. Please verify all details before confirming. The author is not responsible for any incorrect payments.")
