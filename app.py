import streamlit as st
import qrcode
from io import BytesIO
import re

# --- KONFIGURACIJA STRANICE ---
st.set_page_config(page_title="Podela troškova | BetterSplit", page_icon="💸", layout="centered")

# --- CUSTOM CSS ZA ATRAKTIVNIJI IZGLED ---
st.markdown("""
    <style>
    /* Glavne boje i pozadine */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Stil za kartice (container) */
    div.element-container div.stMarkdown > div {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Kartice za sekcije */
    .custom-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border: 1px solid #eaeaea;
    }
    
    /* Istaknuti total */
    .total-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(118, 75, 162, 0.2);
    }
    
    /* Step naslovi */
    .step-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 10px;
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
st.markdown("<h1 style='text-align: center; color: #1a202c; margin-bottom: 0;'>💸 BetterSplit</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #718096; margin-top: 5px;'>Brza podela troškova i generisanje IPS QR kodova</p>", unsafe_allow_html=True)

with st.expander("📖 Kako ovo radi?"):
    st.markdown("""
    1. **Podaci o primaocu:** Unesi svoje ime i broj računa na koji nam stiže uplata.
    2. **Unesi iznose:** Unesi vrednost računa i trošak dostave.
    3. **Izaberi metodu:** Deli ravnopravno na broj ljudi ili ručno unesi specifične iznose za svakoga.
    4. **Skeniraj i plati:** Generiši QR kodove koje ekipa može odmah da skenira preko mBanking aplikacije!
    """)

st.markdown("<br>", unsafe_allow_html=True)

# --- KORAK 1: PODACI O PRIMAOCU ---
st.markdown('<div class="step-title">👤 Korak 1: Podaci o primaocu uplate</div>', unsafe_allow_html=True)
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
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
prikaz_racuna = formatiraj_za_prikaz(c_racun) if c_racun else "unesite račun"

st.markdown(f"""
    <p style="font-size: 0.95rem; font-weight: 500; margin-top: 10px; margin-bottom: 0; color: #4a5568;">
        Validan račun: <code style="background: #edf2f7; padding: 2px 6px; border-radius: 4px; color: #2b6cb0;"><b>{prikaz_racuna}</b></code>
    </p>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

sufiks = st.session_state.reset_kljuc

# --- KORAK 2: PODACI O TROŠKU ---
st.markdown('<div class="step-title">🛒 Korak 2: Unos iznosa troška</div>', unsafe_allow_html=True)
st.markdown('<div class="custom-card">', unsafe_allow_html=True)
c1, c2 = st.columns(2)
v_racun = c1.number_input("Iznos sa računa (RSD):", min_value=0, value=0, step=1, format="%d", key=f"racun_num_{sufiks}")
v_dostava = c2.number_input("Dostava (RSD):", min_value=0, value=0, step=1, format="%d", key=f"dostava_num_{sufiks}")

suma_ukupno = v_racun + v_dostava

st.markdown(f"""
    <div class="total-banner">
        Ukupno za podelu: {formatiraj_broj_sa_tackom(suma_ukupno)} RSD
    </div>
""", unsafe_allow_html=True)

nacin = st.radio("Metoda podele:", ["Ravnopravno", "Ručni unos"], horizontal=True, key=f"nacin_{sufiks}")
st.markdown('</div>', unsafe_allow_html=True)

finalni_dugovi = {}
validna_podela = False

# --- KORAK 3: METODA PODELE ---
st.markdown('<div class="step-title">⚖️ Korak 3: Obračun i QR kodovi</div>', unsafe_allow_html=True)
st.markdown('<div class="custom-card">', unsafe_allow_html=True)

if nacin == "Ravnopravno":
    broj_ljudi = st.number_input("Ukupan broj osoba:", min_value=1, value=2, step=1, key=f"br_ljudi_{sufiks}")
    if broj_ljudi > 1:
        po_osobi = suma_ukupno / broj_ljudi
        po_osobi_zaokruzeno = round(po_osobi, 2)
        po_osobi_str = "{:.2f}".format(po_osobi_zaokruzeno).replace('.', ',')
        st.success(f"Iznos po osobi: **{po_osobi_str} RSD**")
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

    st.text_input("Dodaj učesnika (pritisni Enter za potvrdu):", key="novo_ime_input", on_change=dodaj_direktno, placeholder="npr. Marko")
    
    sortirani = sorted(st.session_state.clanovi_univerzalni)
    
    if sortirani:
        odabrani = st.multiselect("Ko učestvuje u trošku:", options=sortirani, key=f"ucesnici_{sufiks}")
        
        if odabrani:
            br_ucesnika = len(odabrani)
            fiksna_dostava = v_dostava / br_ucesnika
            fiksna_dostava_str = "{:.2f}".format(fiksna_dostava).replace('.', ',')
            
            st.markdown(f"""
                <div style="background-color: #f3e5f5; padding: 12px; border-radius: 8px; border-left: 5px solid #9c27b0; margin-bottom: 20px;">
                    <span style="color: #4a148c; font-size: 0.95rem;">Trošak dostave po osobi: <b>{fiksna_dostava_str} RSD</b></span>
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
                st.warning(f"Preostalo za raspodelu: **{formatiraj_broj_sa_tackom(ostatak)} RSD**")
            else:
                st.error(f"Uneta suma prelazi ukupni iznos za: **{formatiraj_broj_sa_tackom(abs(ostatak))} RSD**")
        
        def obrisi_listu_callback():
            st.session_state.clanovi_univerzalni = []
            kljuc_multi = f"ucesnici_{sufiks}"
            if kljuc_multi in st.session_state:
                del st.session_state[kljuc_multi]

        st.markdown("<br>", unsafe_allow_html=True)
        st.button("🗑️ Obriši celu listu učesnika", on_click=obrisi_listu_callback, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- QR SEKCIJA ---
if validna_podela and suma_ukupno > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔥 GENERIŠI IPS QR KODOVE", use_container_width=True, type="primary"):
        if not moje_ime or not moj_racun:
            st.error("⚠️ Molimo te da popuniš podatke o primaocu na vrhu strane (ime i broj računa)!")
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
                        st.markdown(f"<h4 style='text-align: center;'>Univerzalni kod</h4>", unsafe_allow_html=True)
                        st.image(buf.getvalue(), use_container_width=True)
                        st.markdown(f"<p style='text-align: center; font-weight: 600; color: #2b6cb0;'>Iznos: {zajednicki_iznos_str} RSD</p>", unsafe_allow_html=True)
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
                                st.markdown(f"<h4 style='text-align: center;'>{ime}</h4>", unsafe_allow_html=True)
                                st.image(buf.getvalue(), use_container_width=True)
                                st.markdown(f"<p style='text-align: center; font-weight: 600; color: #2b6cb0;'>Za uplatu: {dug_prikaz} RSD</p>", unsafe_allow_html=True)

# --- RESET DUGME ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔄 Resetuj sve i počni ispočetka", use_container_width=True):
    st.session_state.reset_kljuc += 1
    st.session_state.clanovi_univerzalni = []
    if f"ucesnici_{sufiks}" in st.session_state:
        del st.session_state[f"ucesnici_{sufiks}"]
    st.rerun()

# --- FOOTER ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.caption("💡 **Napomena:** Aplikacija je namenjena isključivo za plaćanja u okviru **IPS sistema Narodne banke Srbije**. Pre potvrde plaćanja, obavezno proverite ispravnost podataka.")
st.caption("🔒 **Disclaimer:** This app is designed solely for Serbian IPS payments. Please verify all details before confirming. The author is not responsible for any incorrect payments.")
