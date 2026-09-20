import streamlit as st
from pyzbar.pyzbar import decode
from PIL import Image
import requests
import json

st.title("Fiskalni QR čitač – Poreska uprava")

uploaded = st.file_uploader("Ubaci sliku fiskalnog QR koda", type=["png", "jpg", "jpeg"])

def extract_qr_data(image):
    decoded = decode(image)
    if not decoded:
        return None
    return decoded[0].data.decode("utf-8")

def fetch_pu_data(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Učitana slika", use_column_width=True)

    qr_text = extract_qr_data(img)

    if not qr_text:
        st.error("QR kod nije pronađen.")
    else:
        st.success("QR kod uspešno očitan.")
        st.write("Sadržaj QR koda:", qr_text)

        # QR kod fiskalnog računa uvek sadrži URL ka PU
        if "http" not in qr_text:
            st.error("QR kod ne sadrži validan PU URL.")
        else:
            st.info("Povlačim podatke sa Poreske uprave...")

            data = fetch_pu_data(qr_text)

            if "error" in data:
                st.error("Greška pri komunikaciji sa PU: " + data["error"])
            else:
                # Pretpostavka: PU vraća JSON sa poljem 'items'
                items = data.get("items", [])

                if not items:
                    st.warning("PU nije vratila artikle.")
                else:
                    st.success("Podaci uspešno preuzeti.")

                    # Priprema tabele
                    table = []
                    for item in items:
                        table.append({
                            "Naziv": item.get("name", ""),
                            "Količina": item.get("quantity", ""),
                            "Cena": item.get("price", "")
                        })

                    st.table(table)
