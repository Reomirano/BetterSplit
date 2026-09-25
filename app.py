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

def formatiraj_za_prikaz(racun_18):
    if len(racun_18) == 18:
        return f"{racun_18[:3]}-{racun_18[3:-2]}-{racun_18[-2:]}"
    return racun_18

def formatiraj_broj_sa_tackom(broj):
    return f"{int(broj):,}".replace(",", ".")

# --- STATE ---
if "clanovi" not in st.session_state:
    st.session_state.clanovi = []

st.title("💰 Podela troškova")

# --- KORAK 1: PRIMALAC ---
st.header("1. Podaci o primaocu")

col1, col2 = st.columns(2)
ime = col1.text_input("Ime primaoca")
racun_unos = col2.text_input("Broj računa (npr. 160-12345678999-12)")

racun_cist = ocisti_racun(racun_unos) if racun_unos else ""
validan_racun = len(racun_cist) == 18

if racun_unos:
    if validan_racun:
        st.success(f"Validan račun: {formatiraj_za_prikaz(racun_cist)}")
    else:
        st.error("Nevažeći račun – proveri unos.")
        st.stop()

# --- KORAK 2: TROŠAK ---
st.header("2. Podaci o trošku")

col3, col4 = st.columns(2)
iznos = col3.number_input("Iznos sa računa (RSD)", min_value=0, step=1)
dostava = col4.number_input("Dostava (RSD)", min_value=0, step=1)

ukupno = iznos + dostava
st.metric("Ukupno", f"{formatiraj_broj_sa_tackom(ukupno)} RSD")

if ukupno == 0:
    st.warning("Unesi iznos da bi nastavio.")
    st.stop()

# --- KORAK 3: METODA ---
st.header("3. Metoda podele")
metoda = st.radio("Odaberi:", ["Ravnopravno", "Ručni unos"])

finalni_dugovi = {}

# --- KORAK 4A: RAVNOPRAVNO ---
if metoda == "Ravnopravno":
    br = st.number_input("Broj osoba", min_value=1, step=1)
    if br > 0:
        po_osobi = round(ukupno / br)
        st.info(f"Po osobi: {formatiraj_broj_sa_tackom(po_osobi)} RSD")
        finalni_dugovi["Zajednički"] = po_osobi

# --- KORAK 4B: RUČNI UNOS ---
else:
    def dodaj_clana():
        ime_novo = st.session_state.novi_clan.strip()
        if ime_novo and ime_novo not in st.session_state.clanovi:
            st.session_state.clanovi.append(ime_novo)
        st.session_state.novi_clan = ""

    st.text_input("Dodaj učesnika (Enter)", key="novi_clan", on_change=dodaj_clana)

    suma_rucno = 0
    for c in list(st.session_state.clanovi):
        col_a, col_b, col_c = st.columns([2, 2, 1])
        col_a.write(f"**{c}**")
        dug = col_b.number_input(f"Iznos_{c}", min_value=0, step=1, label_visibility="collapsed", key=f"dug_{c}")
        suma_rucno += dug
        finalni_dugovi[c] = dug

        if col_c.button("❌", key=f"del_{c}"):
            st.session_state.clanovi.remove(c)
            st.session_state.pop(f"dug_{c}", None)
            st.rerun()

    ostatak = ukupno - suma_rucno
    if st.session_state.clanovi:
        if abs(ostatak) < 0.01:
            st.success("Podela je validna.")
        elif ostatak > 0:
            st.warning(f"Nedostaje: {formatiraj_broj_sa_tackom(ostatak)} RSD")
            st.stop()
        else:
            st.error(f"Višak: {formatiraj_broj_sa_tackom(abs(ostatak))} RSD")
            st.stop()

# --- KORAK 5: QR ---
st.header("5. QR kodovi")

if st.button("GENERISI QR"):
    if not ime or not validan_racun:
        st.error("Popuni ime i račun.")
        st.stop()

    if metoda == "Ravnopravno":
        iz_fmt = "{:.2f}".format(finalni_dugovi["Zajednički"]).replace(".", ",")
        data = f"K:PR|V:01|C:1|R:{racun_cist}|N:{ime}|I:RSD{iz_fmt}|SF:289|S:Podela"
        img = qrcode.make(data)
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption=f"Iznos: {finalni_dugovi['Zajednički']} RSD")

    else:
        for c, dug in finalni_dugovi.items():
            if dug > 0:
                iz_fmt = "{:.2f}".format(dug).replace(".", ",")
                data = f"K:PR|V:01|C:1|R:{racun_cist}|N:{ime}|I:RSD{iz_fmt}|SF:289|S:{c}"
                img = qrcode.make(data)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.subheader(f"{c} – {dug} RSD")
                st.image(buf.getvalue())
