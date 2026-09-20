import streamlit as st
import qrcode
from io import BytesIO
import re

# --- KONFIGURACIJA STRANICE ---
st.set_page_config(page_title="BetterSplit | Podela troškova", page_icon="💳", layout="centered")

# --- KONTROLISANI FINTECH CSS (Pola puta) ---
st.markdown("""
    <style>
    /* Tamna, ali elegantna i umirena pozadina */
    .stApp {
        background-color: #12161c;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Kartice za sekcije - čiste, sa blagim sivi prelazom */
    .section-box {
        background-color: #1a202c;
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
    /* Stil za labele da budu jasne ali ne preagresivne */
    .stTextInput label, .stNumberInput label, .stRadio label, .stMultiSelect label {
        color: #cbd5e0 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    
    /* Input polja */
    .stTextInput input, .stNumberInput input {
        background-color: #242b38 !important;
        color: #ffffff !important;
        border: 1px solid #4a5568 !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3182ce !important;
        box-shadow: 0 0 0 1px #3182ce !important;
    }
    
    /* Istaknuti total baner */
    .total-display {
        background: linear-gradient(135deg, #2b6cb0 1e0%, #2c5282 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 8px;
        text-align: center;
        font-size: 1.25rem;
        font-weight: 600;
        margin: 14px 0;
        letter-spacing: 0.3px;
        border: 1px solid #4299e1;
    }
    
    /* Naslovi sekcija */
    .box-title {
        font-size: 1rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
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

# --- ZAGLAVLJE ---
st.markdown("<h2 style='text-align: center; color: #f7fafc; margin-bottom: 0;'>BetterSplit</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a0aec0; font-size: 0.9rem; margin-top: 4px;'>Pametna podela troškova i NBS IPS generisanje</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.expander("ℹ️ Uputstvo za korišćenje"):
    st.markdown("""
    1. **Primalac:** Unesi svoje ime i broj tekućeg računa.
    2. **Trošak:** Unesi iznos računa i eventualnu dostavu.
    3. **Metoda:** Izaberi ravnopravnu podelu ili ručni unos po učesnicima.
    4. **QR kodovi:** Skeniraj generisane kodove direktno preko mBanking aplikacije.
    """)

st.markdown("<br>", unsafe_allow_html=True)

# --- 1. PRIMALAC ---
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<div class="box-title">👤 Podaci o primaocu uplate</div>', unsafe_allow_html=True)

col_p1, col_p2 = st.columns(2)
moje_ime = col_p1.text_input("Primalac:", value="", key="user_name", placeholder="Ime i prezime")
moj_racun_unos = col_p2.text_input("Broj računa:", value="", key="user_bank", placeholder="npr. 160-12345678999-12")

moj_racun = re.sub(r'\D', '', moj_racun_unos)
c_racun = ocisti_racun(moj_racun) if moj_racun else ""
prikaz_racuna = formatiraj_za_prikaz(c_racun) if c_racun else "unesite račun"

st.markdown(f"""
    <div style="font-size: 0.85rem; color: #a0aec0; margin-top: 8px;">
        Validan račun: <span style="color: {'#48bb78' if len(c_racun) == 18 else '#e53e3e'}; font-weight: 600;">{prikaz_racuna}</span>
    </div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

sufiks = st.session_state.reset_kljuc

# --- 2. TROŠAK ---
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<div class="box-title">💰 Iznos i troškovi</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
v_racun = c1.number_input("Iznos sa računa (RSD):", min_value=0, value=0, step=1, format="%d", key=f"racun_num_{sufiks}")
v_dostava = c2.number_input("Dostava (RSD):", min_value=0, value=0, step=1, format="%d", key=f"dostava_num_{sufiks}")

suma_ukupno = v_racun + v_dostava

st.markdown(f"""
    <div class="total-display">
        Ukupno za podelu: {formatiraj_broj_sa_tackom(suma_ukupno)} RSD
    </div>
""", unsafe_allow_html=True)

nacin = st.radio("Metoda podele:", ["Ravnopravno", "Ručni unos"], horizontal=True, key=f"nacin_{sufiks}")
st.markdown('</div>', unsafe_allow_html=True)

finalni_dugovi = {}
validna_podela = False

# --- 3. ALOKACIJA ---
st.markdown('<div class="section-box">', unsafe_allow_html=True)
st.markdown('<div class="box-title">📊 Obračun i učesnici</div>', unsafe_allow_html=True)

if nacin == "Ravnopravno":
    broj_ljudi = st.number_input("Ukupan broj osoba:", min_value=1, value=2, step=1, key=f"br_ljudi_{sufiks}")
    if broj_ljudi > 1:
        po_osobi = suma_ukupno / broj_ljudi
        po_osobi_zaokruzeno = round(po_osobi, 2)
        po_osobi_str = "{:.2f}".format(po_osobi_zaokruzeno).replace('.', ',')
        st.markdown(f"<div style='color: #48bb78; font-weight: 600; margin-top: 8px;'>Iznos po osobi: {po_osobi_str} RSD</div>", unsafe_allow_html=True)
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

    st.text_input("Dodaj učesnika (Enter za potvrdu):", key="novo_ime_input", on_change=dodaj_direktno, placeholder="npr. Marko")
    
    sortirani = sorted(st.session_state.clanovi_univerzalni)
    
    if sortirani:
        odabrani = st.multiselect("Ko učestvuje:", options=sortirani, key=f"ucesnici_{sufiks}")
        
        if odabrani:
            br_ucesnika = len(odabrani)
            fiksna_dostava = v_dostava / br_ucesnika
            fiksna_dostava_str = "{:.2f}".format(fiksna_dostava).replace('.', ',')
            
            st.markdown(f"""
                <div style="background-color: #242b38; padding: 10px; border-radius: 6px; border-left: 3px solid #3182ce; margin: 12px 0; font-size: 0.85rem;">
                    Dostava po učesniku: <b>{fiksna_dostava_str} RSD</b>
                </div>
            """, unsafe_allow_html=True)
            
            trenutna_suma = 0
            for o in odabrani:
                v_dug = st.number_input(
                    f"Iznos za učesnika {o} (RSD):", 
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
                st.markdown(f"<div style='color: #d69e2e; font-size: 0.9rem;'>Preostalo za raspodelu: <b>{formatiraj_broj_sa_tackom(ostatak)} RSD</b></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color: #e53e3e; font-size: 0.9rem;'>Višak iznosa: <b>{formatiraj_broj_sa_tackom(abs(ostatak))} RSD</b></div>", unsafe_allow_html=True)
        
        def obrisi_listu_callback():
            st.session_state.clanovi_univerzalni = []
            kljuc_multi = f"ucesnici_{sufiks}"
            if kljuc_multi in st.session_state:
                del st.session_state[kljuc_multi]

        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Obriši listu učesnika", on_click=obrisi_listu_callback, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- QR KODOVI ---
if validna_podela and suma_ukupno > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔥 GENERIŠI QR KODOVE", use_container_width=True, type="primary"):
        if not moje_ime or not moj_racun:
            st.error("⚠️ Popuni podatke o primaocu (ime i broj računa gore)!")
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
                        st.markdown(f"<p style='text-align: center; font-weight: 600;'>Univerzalni kod</p>", unsafe_allow_html=True)
                        st.image(buf.getvalue(), use_container_width=True)
                        st.markdown(f"<p style='text-align: center; color: #48bb78; font-weight: bold;'>Iznos: {zajednicki_iznos_str} RSD</p>", unsafe_allow_html=True)
            else:
                for ime, dug in finalni_dugovi.items():
                    if dug > 0:
                        iz_fmt = "{:.2f}".format(float(dug)).replace('.', ',')
                        ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Uplata-{ime}"
                        qr_img = qrcode.make(ips_data)
                    
                        buf = BytesIO()
                        qr_img.save(buf, format="PNG")
                        
                        _, col_qr_inner, _ = st.columns([1, 2, 1])
                        with col_qr_inner:
                            with st.container(border=True):
                                dug_prikaz = formatiraj_broj_sa_tackom(dug)
                                st.markdown(f"<p style='text-align: center; font-weight: 600;'>{ime}</p>", unsafe_allow_html=True)
                                st.image(buf.getvalue(), use_container_width=True)
                                st.markdown(f"<p style='text-align: center; color: #48bb78; font-weight: bold;'>Za uplatu: {dug_prikaz} RSD</p>", unsafe_allow_html=True)

# --- RESET ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔄 Resetuj aplikaciju", use_container_width=True):
    st.session_state.reset_kljuc += 1
    st.session_state.clanovi_univerzalni = []
    if f"ucesnici_{sufiks}" in st.session_state:
        del st.session_state[f"ucesnici_{sufiks}"]
    st.rerun()

# --- FOOTER ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("💡 **Napomena:** Namenjeno za IPS sistem Narodne banke Srbije. Proverite podatke pre uplate.")
