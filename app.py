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
st.set_page_config(page_title="NeshatSplit", page_icon="💸", layout="centered")

# --- CUSTOM CSS (MODERAN PREFINJENI DARK MODE) ---
st.markdown("""
    <style>
    /* Pozadina i osnovni tekst */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Sakrivanje standardnog Streamlit zaglavlja i menija */
    header {visibility: hidden;}
    
    /* Naslovi */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.025em;
        color: #ffffff !important;
        margin-bottom: 0.2rem !important;
    }
    h3, h4 {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }

    /* Polja za unos (Input fields) */
    div[data-baseweb="input"] > div {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }
    div[data-baseweb="input"] input {
        color: #ffffff !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #10b981 !important;
    }

    /* Stil za Dugmad */
    .stButton button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    /* Primary Dugme (Generiši QR) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }
    div.stButton > button[kind="primary"]:hover {
        opacity: 0.95;
        transform: translateY(-1px);
    }

    /* Secondary Dugme */
    div.stButton > button[kind="secondary"] {
        background-color: #1e293b !important;
        color: #cbd5e1 !important;
        border: 1px solid #334155 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #334155 !important;
        color: #ffffff !important;
    }

    /* Stil za Expander */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }
    
    /* Kartica sa ukupnim iznosom */
    .total-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-left: 5px solid #10b981;
        padding: 18px 24px;
        border-radius: 12px;
        margin: 15px 0px;
    }
    .total-title {
        color: #94a3b8;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .total-amount {
        color: #10b981;
        font-size: 2.2rem;
        font-weight: 800;
    }

    /* Validacioni box za račun */
    .account-badge {
        padding: 8px 14px;
        background-color: #1e293b;
        border-radius: 8px;
        border: 1px solid #334155;
        font-size: 0.9rem;
        color: #94a3b8;
        margin-top: 5px;
    }
    .account-badge b {
        color: #38bdf8 !important;
    }
    </style>
""", unsafe_allow_html=True)

if "reset_kljuc" not in st.session_state:
    st.session_state.reset_kljuc = 0
if 'clanovi_univerzalni' not in st.session_state:
    st.session_state.clanovi_univerzalni = []

# --- GLAVNI PANEL ---
st.title("💸 NeshatSplit")
st.caption("Brza podela računa i generisanje IPS QR kodova za prenos")

with st.expander("📖 Uputstvo za korišćenje"):
    st.write("""
    1. **Primalac:** Unesi ime i broj tekućeg računa na koji uplate treba da legnu.
    2. **Iznosi:** Upiši cifru sa računa i cenu dostave.
    3. **Izbor metode:** Odaberi ravnopravnu podelu ili podelu po stavkama za svakog učesnika.
    4. **Plaćanje:** Prikaži QR kod i skenirajte ga direktno kroz bilo koju mBanking aplikaciju (opcija IPS pokaži/izvrši).
    """)

st.write("")
st.subheader("💳 Podaci o primaocu")

col_p1, col_p2 = st.columns(2)
moje_ime = col_p1.text_input("Ime i prezime", value="", key="user_name", placeholder="Petar Petrović")
moj_racun_unos = col_p2.text_input("Broj računa", value="", key="user_bank", placeholder="160-12345678999-12")

moj_racun = re.sub(r'\D', '', moj_racun_unos)
c_racun = ocisti_racun(moj_racun) if moj_racun else ""
prikaz_racuna = formatiraj_za_prikaz(c_racun) if c_racun else "Nije unet"

st.markdown(f"""
    <div class="account-badge">
        Validiran IPS račun: <b>{prikaz_racuna}</b>
    </div>
""", unsafe_allow_html=True)

st.write("")
st.subheader("🧾 Podaci o trošku")

sufiks = st.session_state.reset_kljuc

c1, c2 = st.columns(2)
v_racun = c1.number_input("Iznos računa (RSD)", min_value=0, value=0, step=10, format="%d", key=f"racun_num_{sufiks}")
v_dostava = c2.number_input("Dostava (RSD)", min_value=0, value=0, step=10, format="%d", key=f"dostava_num_{sufiks}")

suma_ukupno = v_racun + v_dostava

# Kartica sa ukupnim iznosom
st.markdown(f"""
    <div class="total-card">
        <div class="total-title">Ukupan iznos za podelu</div>
        <div class="total-amount">{formatiraj_broj_sa_tackom(suma_ukupno)} <span style="font-size: 1.2rem;">RSD</span></div>
    </div>
""", unsafe_allow_html=True)

col_reset, _ = st.columns([1, 2])
with col_reset:
    if st.button("🔄 Resetuj iznose", use_container_width=True):
        st.session_state.reset_kljuc += 1
        st.session_state.clanovi_univerzalni = []
        st.rerun()

st.write("")
st.subheader("⚙️ Metoda podele")
nacin = st.pills("Metoda podele:", ["Ravnopravno", "Ručni unos"], default="Ravnopravno", label_visibility="collapsed", key=f"nacin_{sufiks}")

finalni_dugovi = {}
validna_podela = False

if nacin == "Ravnopravno":
    broj_ljudi = st.number_input("Broj osoba koje dele račun:", min_value=1, value=2, step=1, key=f"br_ljudi_{sufiks}")
    if broj_ljudi > 0:
        po_osobi = suma_ukupno / broj_ljudi
        po_osobi_zaokruzeno = round(po_osobi)
        po_osobi_str = formatiraj_broj_sa_tackom(po_osobi_zaokruzeno)
        
        st.info(f"Svaka osoba plaća: **{po_osobi_str} RSD**")
        finalni_dugovi["Zajednički"] = po_osobi_zaokruzeno
        validna_podela = True

else:
    def dodaj_direktno():
        ime = st.session_state.novo_ime_input.strip()
        if ime and ime not in st.session_state.clanovi_univerzalni:
            st.session_state.clanovi_univerzalni.append(ime)
        st.session_state.novo_ime_input = ""

    st.text_input("Dodaj učesnika (Enter za potvrdu):", key="novo_ime_input", on_change=dodaj_direktno, placeholder="Npr. Marko")
    
    aktivni_clanovi = st.session_state.clanovi_univerzalni
    
    if aktivni_clanovi:
        br_ucesnika = len(aktivni_clanovi)
        fiksna_dostava = v_dostava / br_ucesnika if br_ucesnika > 0 else 0
        fiksna_dostava_str = formatiraj_broj_sa_tackom(round(fiksna_dostava))
        
        st.caption(f"💡 Učešće u dostavi po osobi iznosi: **{fiksna_dostava_str} RSD**")
        
        trenutna_suma = 0
        for o in list(aktivni_clanovi):
            col_i1, col_i2, col_i3 = st.columns([2, 2, 0.5])
            with col_i1:
                st.markdown(f"<p style='padding-top: 10px; font-weight: 500;'>{o}</p>", unsafe_allow_html=True)
            with col_i2:
                v_dug = st.number_input(
                    f"Iznos_{o}", 
                    min_value=0, 
                    value=0, 
                    step=10, 
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
            st.warning(f"Preostalo za raspodelu: **{formatiraj_broj_sa_tackom(ostatak)} RSD**")
        else:
            st.error(f"Zbir prekoračuje ukupan račun za: **{formatiraj_broj_sa_tackom(abs(ostatak))} RSD**")
        
        def obrisi_listu_callback():
            st.session_state.clanovi_univerzalni = []

        st.button("Obriši celu listu", on_click=obrisi_listu_callback)

# --- QR SEKCIJA ---
st.write("")
if validna_podela and suma_ukupno > 0:
    if st.button("⚡ GENERIŠI QR KODOVE", use_container_width=True, type="primary"):
        if not moje_ime or not moj_racun:
            st.error("⚠️ Unesite ime i broj računa primaoca na vrhu stranice!")
        else:
            st.subheader("📱 Kodovi za skeniranje")
            
            if nacin == "Ravnopravno":
                iz_fmt = "{:.2f}".format(float(finalni_dugovi['Zajednički'])).replace('.', ',')
                ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Podela racuna"
                qr_img = qrcode.make(ips_data)
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                
                _, col_qr, _ = st.columns([1, 2, 1])
                with col_qr:
                    zajednicki_iznos_str = formatiraj_broj_sa_tackom(finalni_dugovi['Zajednički'])
                    st.image(buf.getvalue(), caption=f"Iznos po osobi: {zajednicki_iznos_str} RSD", use_container_width=True)
            else:
                for ime, dug in finalni_dugovi.items():
                    if dug > 0:
                        iz_fmt = "{:.2f}".format(float(dug)).replace('.', ',')
                        ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Rucak-{ime}"
                        qr_img = qrcode.make(ips_data)
                        buf = BytesIO()
                        qr_img.save(buf, format="PNG")
                        
                        dug_prikaz = formatiraj_broj_sa_tackom(dug)
                        st.markdown(f"#### {ime} • `{dug_prikaz} RSD`")
                        
                        _, col_qr_inner, _ = st.columns([1, 2, 1])
                        with col_qr_inner:
                            st.image(buf.getvalue(), use_container_width=True)

st.write("") 
st.caption("**Napomena:** Aplikacija generiše standardizovane kodove za **IPS NBS** sistem. Proverite tačnost podataka pre slanja uplate.")
