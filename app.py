import streamlit as st
import qrcode
from io import BytesIO
import re

# --- FUNKCIJE ---
def ocisti_racun(racun):
    samo_cifre = re.sub(r'\D', '', racun)
    
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

def parsiraj_broj(tekst):
    if not tekst:
        return 0.0
    samo_cifre = re.sub(r'\D', '', tekst)
    if not samo_cifre:
        return 0.0
    return float(samo_cifre) / 100.0

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
    2. **Unesi iznose:** Upiši vrednost sa računa i cenu dostave.
    3. **Odaberi metodu:**
        * **Ravnopravno:** Unesi broj ljudi i dobijaš univerzalni QR kod.
        * **Ručni unos:** Dodaš imena učesnika i uneseš pojedinačnu vrednost.
    4. **Skeniranje:** Svako otvori mBanking, odabere 'IPS' i očita kod sa ekrana (univerzalni ili lični).
    """)

st.subheader("⚙️ Podaci o primaocu")
col_p1, col_p2 = st.columns(2)
moje_ime = col_p1.text_input("Primalac:", value="", key="user_name", placeholder="Ime i prezime")

def sanitize_bank():
    st.session_state.user_bank = re.sub(r'\D', '', st.session_state.user_bank)

moj_racun = col_p2.text_input("Broj računa primaoca:", value="", key="user_bank", placeholder="Samo cifre", on_change=sanitize_bank)
moj_racun = re.sub(r'\D', '', moj_racun)

c_racun = ocisti_racun(moj_racun) if moj_racun else ""
prikaz_racuna = formatiraj_za_prikaz(c_racun) if c_racun else "Nije unet"

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

def sanitize_racun():
    key = f"racun_str_{sufiks}"
    if key in st.session_state:
        st.session_state[key] = re.sub(r'\D', '', st.session_state[key])

def sanitize_dostava():
    key = f"dostava_str_{sufiks}"
    if key in st.session_state:
        st.session_state[key] = re.sub(r'\D', '', st.session_state[key])

s_racun_input = c1.text_input("Iznos sa računa (RSD):", value="", placeholder="npr. 150050", key=f"racun_str_{sufiks}", on_change=sanitize_racun)
s_racun_input = re.sub(r'\D', '', s_racun_input)

s_dostava_input = c2.text_input("Dostava (RSD):", value="", placeholder="npr. 25000", key=f"dostava_str_{sufiks}", on_change=sanitize_dostava)
s_dostava_input = re.sub(r'\D', '', s_dostava_input)

v_racun = parsiraj_broj(s_racun_input)
v_dostava = parsiraj_broj(s_dostava_input)
suma_ukupno = v_racun + v_dostava

st.markdown(f"### Ukupno: {f'{suma_ukupno:.2f}'.replace('.', ',')} RSD")
st.divider()

nacin = st.radio("Metoda podele:", ["Ravnopravno", "Ručni unos"], horizontal=True, key=f"nacin_{sufiks}")

finalni_dugovi = {}
validna_podela = False

if nacin == "Ravnopravno":
    broj_ljudi = st.number_input("Ukupan broj osoba:", min_value=1, value=2, step=1, format="%d", key=f"br_ljudi_{sufiks}")
    if broj_ljudi > 1:
        po_osobi = suma_ukupno / broj_ljudi
        st.info(f"Po osobi: **{f'{po_osobi:.2f}'.replace('.', ',')} RSD**")
        finalni_dugovi["Zajednički"] = po_osobi
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
            
            st.markdown(f"""
                <div style="background-color: #f3e5f5; padding: 10px; border-radius: 5px; border-left: 5px solid #9c27b0; margin-bottom: 20px;">
                    <span style="color: #4a148c;">Učešće u dostavi po osobi: <b>{f'{fiksna_dostava:.2f}'.replace('.', ',')} RSD</b></span>
                </div>
            """, unsafe_allow_html=True)
            
            trenutna_suma = 0.0
            for o in odabrani:
                def make_sanitize(member):
                    def sanitize_fn():
                        key = f"rucni_str_{member}_{sufiks}"
                        if key in st.session_state:
                            st.session_state[key] = re.sub(r'\D', '', st.session_state[key])
                    return sanitize_fn

                s_dug_input = st.text_input(f"Iznos za učesnika {o} (RSD):", value="", placeholder="npr. 50000", key=f"rucni_str_{o}_{sufiks}", on_change=make_sanitize(o))
                s_dug_input = re.sub(r'\D', '', s_dug_input)
                v_dug = parsiraj_broj(s_dug_input)
                finalni_dugovi[o] = v_dug
                trenutna_suma += v_dug
            
            ostatak = suma_ukupno - trenutna_suma
            if abs(ostatak) < 0.01:
                validna_podela = True
            elif ostatak > 0:
                st.warning(f"Preostalo: **{f'{ostatak:.2f}'.replace('.', ',')} RSD**")
            else:
                st.error(f"Višak: **{f'{abs(ostatak):.2f}'.replace('.', ',')} RSD**")
        
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
                    zajednicki_iznos_str = f"{finalni_dugovi['Zajednički']:.2f}".replace('.', ',')
                    st.image(buf.getvalue(), caption=f"Iznos: {zajednicki_iznos_str} RSD", use_container_width=True)
            else:
                for ime, dug in finalni_dugovi.items():
                    if dug > 0:
                        iz_fmt = "{:.2f}".format(dug).replace('.', ',')
                        ips_data = f"K:PR|V:01|C:1|R:{c_racun}|N:{moje_ime}|I:RSD{iz_fmt}|SF:289|S:Rucak-{ime}"
                        qr_img = qrcode.make(ips_data)
                    
                        buf = BytesIO()
                        qr_img.save(buf, format="PNG")
                        
                        with st.container(border=True):
                            dug_str = f"{dug:.2f}".replace('.', ',')
                            st.markdown(f"#### {ime} - {dug_str} RSD")
                            _, col_qr_inner, _ = st.columns([1, 2, 1])
                            with col_qr_inner:
                                st.image(buf.getvalue(), use_container_width=True)

st.write("") 
st.divider() 
st.caption("**Napomena:** Aplikacija je namenjena isključivo za plaćanja u okviru **IPS sistema Narodne banke Srbije**. Pre potvrde plaćanja, obavezno **proverite ispravnost podataka**. Autor ne snosi odgovornost za pogrešne uplate.")
st.caption("**Disclaimer:** This app is designed solely for **Serbian IPS payments**. Please verify all details before confirming. The author is not responsible for any incorrect payments.")
