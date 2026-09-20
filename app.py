import streamlit as st
import qrcode
from io import BytesIO
import re

# --- KONFIGURACIJA STRANICE ---
st.set_page_config(page_title="BetterSplit", page_icon="⚡", layout="centered")

# --- OZBILJAN FINTECH CSS (DARK MODE & PROFESSIONAL UI) ---
st.markdown("""
    <style>
    /* Osnovna pozadina aplikacije - duboka tamno siva / crna */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    
    /* Sakrivanje Streamlit brendiranja za čistiji look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Input polja u stilu bankarskih aplikacija */
    .stTextInput input, .stNumberInput input {
        background-color: #161b22 !important;
        color: #ffffff !important;
        border: 1px. solid #30363d !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2) !important;
    }
    
    /* Labele iznad polja */
    .stTextInput label, .stNumberInput label, .stRadio label, .stMultiSelect label {
        color: #8b949e !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    /* Glavne finansijske kartice / paneli */
    .fintech-panel {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 16px;
    }
    
    /* Istaknuti total (moćan, čist baner) */
    .fintech-total-banner {
        background: linear-gradient(135deg, #1f6feb 0%, #1158c7 100%);
        color: #ffffff;
        padding: 18px 24px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 16px 0;
        border: 1px solid #388bfd;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Sekcijski naslovi */
    .fintech-header {
        font-size: 0.9rem;
        font-weight: 600;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 12px;
        border-bottom: 1px solid #21262d;
        padding-bottom: 6px;
    }
    
    /* Primarno dugme */
    .stButton button {
        background-color: #238636 !important;
        color: #ffffff !important;
        border: 1px solid rgba(240, 246, 252, 0.1) !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: background-color 0.2s ease;
    }
    
    .stButton button:hover {
        background-color: #2ea043 !important;
        border-color: rgba(240, 246, 252, 0.2) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        color: #c9d1d9 !important;
    }
    </style>
""", unsafe_allow_html=True)

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

# --- STANJE APLIKACIJE ---
if "reset_kljuc" not in st.session_state:
    st.session_state.reset_kljuc = 0
if 'clanovi_univerzalni' not in st.session_state:
    st.session_state.clanovi_univerzalni = []

# --- HEADER ---
st.markdown("<h2 style='font-family: monospace; color: #ffffff; margin-bottom: 0;'>BETTER_SPLIT // v2.6</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e; font-size: 0.9rem; margin-top: 4px;'>Sistem za direkcionu podelu troškova i generisanje NBS IPS kodova</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.expander("Sistemske instrukcije i specifikacija"):
    st.markdown("""
    * **Modul 01:** Unos parametara primaoca i validacija standarda računa.
    * **Modul 02:** Agregacija iznosa (osnovni račun + troškovi isporuke).
    * **Modul 03:** Metodologija podele (Ravnopravno / Granularno po učesnicima).
    * **Modul 04:** Generisanje dinamičkih IPS QR kodova sa ugrađenim parametrima uplate.
    """)

st.markdown("<br>", unsafe_allow_html=True)

# --- SEKCIJA 1: PARAMETRI PRIMAOCA ---
st.markdown('<div class="fintech-header">01. Parametri primaoca uplate</div>', unsafe_allow_html=True)
st.markdown('<div class="fintech-panel">', unsafe_allow_html=True)

col_p1, col_p2 = st.columns(2)
moje_ime = col_p1.text_input("Naziv / Primalac", value="", key="user_name", placeholder="Ime i prezime")
moj_racun_unos = col_p2.text_input("Broj računa", value="", key="user_bank", placeholder="160-XXXXXXXXXXXXX-XX")

moj_racun = re.sub(r'\D', '', moj_racun_unos)
c_racun = ocisti_racun(moj_racun) if moj_racun else ""
prikaz_racuna = formatiraj_za_prikaz(c_racun) if c_racun else "Nije unet validan račun"

st.markdown(f"""
    <div style="font-size: 0.85rem; color: #8b949e; margin-top: 10px; font-family: monospace;">
        STATUS RAČUNA: <span style="color: {'#3fb950' if len(c_racun) == 18 else '#f85149'};"><b>{prikaz_racuna}</b></span>
    </div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

sufiks = st.session_state.reset_kljuc

# --- SEKCIJA 2: FINANSIJSKA STRUKTURA ---
st.markdown('<div class="fintech-header">02. Finansijska struktura troška</div>', unsafe_allow_html=True)
st.markdown('<div class="fintech-panel">', unsafe_allow_html=True)

c1, c2 = st.columns(2)
v_racun = c1.number_input("Osnovni iznos (RSD)", min_value=0, value=0, step=1, format="%d", key=f"racun_num_{sufiks}")
v_dostava = c2.number_input("Troškovi dostave (RSD)", min_value=0, value=0, step=1, format="%d", key=f"dostava_num_{sufiks}")

suma_ukupno = v_racun + v_dostava

st.markdown(f"""
    <div class="fintech-total-banner">
        <span>UKUPNO ZA ALOKACIJU:</span>
        <span>{formatiraj_broj_sa_tackom(suma_ukupno)} RSD</span>
    </div>
""", unsafe_allow_html=True)

nacin = st.radio("Model alokacije", ["Ravnopravno", "Granularno (Ručni unos)"], horizontal=True, key=f"nacin_{sufiks}")
st.markdown('</div>', unsafe_allow_html=True)

finalni_dugovi = {}
validna_podela = False

# --- SEKCIJA 3: OBDRAČUN I ALOKACIJA ---
st.markdown('<div class="fintech-header">03. Parametri alokacije i generisanje</div>', unsafe_allow_html=True)
st.markdown('<div class="fintech-panel">', unsafe_allow_html=True)

if nacin == "Ravnopravno":
    broj_ljudi = st.number_input("Broj subjekata (učesnika)", min_value=1, value=2, step=1, key=f"br_ljudi_{sufiks}")
    if broj_ljudi > 1:
        po_osobi = suma_ukupno / broj_ljudi
        po_osobi_zaokruzeno = round(po_osobi, 2)
        po_osobi_str = "{:.2f}".format(po_osobi_zaokruzeno).replace('.', ',')
        st.markdown(f"""
            <div style="font-family: monospace; font-size: 1rem; color: #3fb950; margin-top: 10px;">
                > Alocirano po subjektu: <b>{po_osobi_str} RSD</b>
            </div>
        """, unsafe_allow_html=True)
        finalni_dugovi["Zajednički"] = po_osobi_zaokruzeno
        validna_podela = True

else:
    def dodaj_direktno():
        ime = st.session_state.novo_ime_input.strip()
        if ime:
            if ime not in st.session_state.clanovi_univerzalni:
                st.session_state.clanovi_univerzalni.append(ime)
            kljuc_multi = f"ucesnici_{sufiks}"
            trenutno_selektovani = list(st.session_state.get(kljuc_multi, []))
            if ime not in trenutno_selektovani:
                trenutno_selektovani.append(ime)
                st.session_state[kljuc_multi] = trenutno_selektovani
        st.session_state.novo_ime_input = ""

    st.text_input("Dodaj učesnika (Enter za potvrdu)", key="novo_ime_input", on_change=dodaj_direktno, placeholder="Unesi ime...")
    
    sortirani = sorted(st.session_state.clanovi_univerzalni)
    
    if sortirani:
        odabrani = st.multiselect("Aktivni učesnici u transakciji", options=sortirani, key=f"ucesnici_{sufiks}")
        
        if odabrani:
            br_ucesnika = len(odabrani)
            fiksna_dostava = v_dostava / br_ucesnika
            fiksna_dostava_str = "{:.2f}".format(fiksna_dostava).replace('.', ',')
            
            st.markdown(f"""
                <div style="background-color: #21262d; padding: 10px; border-radius: 6px; border-left: 3px solid #58a6ff; margin: 15px 0; font-family: monospace; font-size: 0.85rem;">
                    Proporcionalna dostava po subjektu: <b>{fiksna_dostava_str} RSD</b>
                </div>
            """, unsafe_allow_html=True)
            
            trenutna_suma = 0
            for o in odabrani:
                v_dug = st.number_input(
                    f"Iznos za učesnika: {o} (RSD)", 
                    min_value=0, 
                    value=0, 
                    step=1, 
                    format="%d", 
                    key=f"rucni_num_{o}_{sufiks}"
                )
                finalni_dugovi[o] = v_dug
                trenutna_suma += v_dug
            
            ostatak = suma_ukupno - trenutna_suma
            if abs(ostatak) < 0.01:
                validna_podela = True
            elif ostatak > 0:
                st.markdown(f"<p style='color: #d29922; font-family: monospace;'>[INFO] Preostalo neraspoređeno: {formatiraj_broj_sa_tackom(ostatak)} RSD</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='color: #f85149; font-family: monospace;'>[GREŠKA] Prekoračenje iznosa za: {formatiraj_broj_sa_tackom(abs(ostatak))} RSD</p>", unsafe_allow_html=True)
        
        def obrisi_listu_callback():
            st.session_state.clanovi_univerzalni = []
            kljuc_multi = f"ucesnici_{sufiks}"
            if kljuc_multi in st.session_state:
                del st.session_state[kljuc_multi]

        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Resetuj listu učesnika", on_click=obrisi_listu_callback)

st.markdown('</div>', unsafe_allow_html=True)

# --- QR GENERATOR SEKCIJA ---
if validna_podela and suma_ukupno > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("GENERISANJE IPS QR KODOVA", use_container_width=True):
        if not moje_ime or not moj_racun:
            st.error("[KRITIČNO] Nisu definisani parametri primaoca (naziv i validan broj računa).")
        else:
            st.markdown("---")
            if nacin == "Ravnopravno":
                iz_fmt = "{:.2f}".format(finalni_dugovi['Zajednički']).replace('.', ',')
                ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Podela racuna"
                qr_img = qrcode.make(ips_data)
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                
                _, col_qr, _ = st.columns([1, 2, 1])
                with col_qr:
                    zajednicki_iznos_str = formatiraj_broj_sa_tackom(finalni_dugovi['Zajednički'])
                    with st.container(border=True):
                        st.markdown(f"<p style='text-align: center; font-family: monospace; font-weight: 600;'>UNIVERZALNI NALOG</p>", unsafe_allow_html=True)
                        st.image(buf.getvalue(), use_container_width=True)
                        st.markdown(f"<p style='text-align: center; font-family: monospace; color: #3fb950; font-weight: bold;'>Iznos: {zajednicki_iznos_str} RSD</p>", unsafe_allow_html=True)
            else:
                for ime, dug in finalni_dugovi.items():
                    if dug > 0:
                        iz_fmt = "{:.2f}".format(float(dug)).replace('.', ',')
                        ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Transakcija-{ime}"
                        qr_img = qrcode.make(ips_data)
                    
                        buf = BytesIO()
                        qr_img.save(buf, format="PNG")
                        
                        _, col_qr_inner, _ = st.columns([1, 2, 1])
                        with col_qr_inner:
                            with st.container(border=True):
                                dug_prikaz = formatiraj_broj_sa_tackom(dug)
                                st.markdown(f"<p style='text-align: center; font-family: monospace; font-weight: 600;'>SUBJEKT: {ime.upper()}</p>", unsafe_allow_html=True)
                                st.image(buf.getvalue(), use_container_width=True)
                                st.markdown(f"<p style='text-align: center; font-family: monospace; color: #3fb950; font-weight: bold;'>Zaduženje: {dug_prikaz} RSD</p>", unsafe_allow_html=True)

# --- GLOBALNI RESET ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("RESETUJ SESIJU", use_container_width=True):
    st.session_state.reset_kljuc += 1
    st.session_state.clanovi_univerzalni = []
    if f"ucesnici_{sufiks}" in st.session_state:
        del st.session_state[f"ucesnici_{sufiks}"]
    st.rerun()

# --- FOOTER ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #484f58; font-size: 0.75rem; font-family: monospace;'>SYSTEM NOTICE: Kompatibilno isključivo sa NBS IPS sistemom elektronskog bankarstva. Proverite parametre transakcije pre izvršenja.</p>", unsafe_allow_html=True)
