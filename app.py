import streamlit as st
import qrcode
from io import BytesIO
import re

# --- FUNKCIJE ---
def ocisti_racun(racun_str):
    # Izbacuje sve što nisu cifre iz unetog stringa računa
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
if 'clanovi_univerzalni' not in st.session_state:
    st.session_state.clanovi_univerzalni = []

# --- GLAVNI PANEL ---
st.title("💰 Podela troškova")

with st.expander("📖 Kako ovo radi?"):
    st.write("""
    1. **Unesi podatke primaoca:** Upiši svoje ime i broj računa direktno u polja ispod.
    2. **Unesi iznose:** Upiši vrednost sa računa i cenu dostave u celim dinarima.
    3. **Odaberi metodu:**
        * **Ravnopravno:** Unesi broj ljudi i dobijaš univerzalni QR kod.
        * **Ručni unos:** Dodaš imena učesnika i uneseš pojedinačnu vrednost.
    4. **Skeniranje:** Svako otvori mBanking, odabere 'IPS' i očita kod sa ekrana (univerzalni ili lični).
    """)

st.subheader("⚙️ Podaci o primaocu")
col_p1, col_p2 = st.columns(2)
moje_ime = col_p1.text_input("Primalac:", value="", key="user_name", placeholder="Ime i prezime")

# Ovde je sada text_input umesto number_input (nema +/- strelica, čisto polje)
moj_racun_unos = col_p2.text_input(
    "Broj računa primaoca:", 
    value="", 
    key="user_bank", 
    placeholder="npr. 160-12345678999-12"
)

# Automatsko čišćenje unosa da ostanu samo cifre
moj_racun = re.sub(r'\D', '', moj_racun_unos)

c_racun = ocisti_racun(moj_racun) if moj_racun else ""
prikaz_racuna = formatiraj_za_prikaz(c_racun) if c_racun else "unesite račun"

st.markdown(f"""
    <p style="font-size: 1.1rem; font-weight: 500; margin-top: 5px; margin-bottom: 0; color: gray;">
        Validan račun: <b>{prikaz_racuna}</b>
    </p>
""", unsafe_allow_html=True)

st.divider()

sufiks = st.session_state.reset_kljuc

if st.button("🔄 Novi unos", use_container_width=True, type="primary"):
    st.session_state.reset_kljuc += 1
    st.session_state.clanovi_univerzalni = []
    if f"ucesnici_{sufiks}" in st.session_state:
        del st.session_state[f"ucesnici_{sufiks}"]
    st.rerun()

st.subheader("✍️ Podaci o trošku")
c1, c2 = st.columns(2)
v_racun = c1.number_input("Iznos sa računa (RSD):", min_value=0, value=0, step=1, format="%d", key=f"racun_num_{sufiks}")
v_dostava = c2.number_input("Dostava (RSD):", min_value=0, value=0, step=1, format="%d", key=f"dostava_num_{sufiks}")

suma_ukupno = v_racun + v_dostava

st.markdown(f"### Ukupno: {formatiraj_broj_sa_tackom(suma_ukupno)} RSD")
st.divider()

nacin = st.radio("Metoda podele:", ["Ravnopravno", "Ručni unos"], horizontal=True, key=f"nacin_{sufiks}")

finalni_dugovi = {}
validna_podela = False

if nacin == "Ravnopravno":
    broj_ljudi = st.number_input("Ukupan broj osoba:", min_value=1, value=2, step=1, key=f"br_ljudi_{sufiks}")
    if broj_ljudi > 1:
        po_osobi = suma_ukupno / broj_ljudi
        po_osobi_zaokruzeno = round(po_osobi, 2)
        po_osobi_str = "{:.2f}".format(po_osobi_zaokruzeno).replace('.', ',')
        st.info(f"Po osobi: **{po_osobi_str} RSD**")
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

    st.text_input("Dodaj učesnika na listu (potvrdi na Enter):", key="novo_ime_input", on_change=dodaj_direktno)
    
    sortirani = sorted(st.session_state.clanovi_univerzalni)
    
    if sortirani:
        odabrani = st.multiselect("Ko učestvuje:", options=sortirani, key=f"ucesnici_{sufiks}")
        
        if odabrani:
            br_ucesnika = len(odabrani)
            fiksna_dostava = v_dostava / br_ucesnika
            fiksna_dostava_str = "{:.2f}".format(fiksna_dostava).replace('.', ',')
            
            st.markdown(f"""
                <div style="background-color: #f3e5f5; padding: 10px; border-radius: 5px; border-left: 5px solid #9c27b0; margin-bottom: 20px;">
                    <span style="color: #4a148c;">Učešće u dostavi po osobi: <b>{fiksna_dostava_str} RSD</b></span>
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
                st.warning(f"Preostalo: **{formatiraj_broj_sa_tackom(ostatak)} RSD**")
            else:
                st.error(f"Višak: **{formatiraj_broj_sa_tackom(abs(ostatak))} RSD**")
        
        def obrisi_listu_callback():
            st.session_state.clanovi_univerzalni = []
            kljuc_multi = f"ucesnici_{sufiks}"
            if kljuc_multi in st.session_state:
                del st.session_state[kljuc_multi]

        st.button("Obriši celu listu", on_click=obrisi_listu_callback)

# --- QR SEKCIJA ---
st.divider()
if validna_podela and suma_ukupno > 0:
    if st.button("🔥 GENERIŠI QR KODOVE", use_container_width=True, type="primary"):
        if not moje_ime or not moj_racun:
            st.error("⚠️ Popuni podatke o primaocu na vrhu strane!")
        else:
            if nacin == "Ravnopravno":
                iz_fmt = "{:.2f}".format(finalni_dugovi['Zajednički']).replace('.', ',')
                ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Podela racuna"
                qr_img = qrcode.make(ips_data)
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                
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

st.write("") 
st.divider() 
st.caption("**Napomena:** Aplikacija je namenjena isključivo za plaćanja u okviru **IPS sistema Narodne banke Srbije**. Pre potvrde plaćanja, obavezno **proverite ispravnost podataka**. Autor ne snosi odgovornost za pogrešne uplate.")
st.caption("**Disclaimer:** This app is designed solely for **Serbian IPS payments**. Please verify all details before confirming. The author is not responsible for any incorrect payments.")
