import streamlit as st
import cv2
import numpy as np
import requests
from bs4 import BeautifulSoup
import pandas as pd
from qreader import QReader
from PIL import Image
import re

st.set_page_config(page_title="SUF Skener Računa", layout="centered")

# Inicijalizacija YOLO modela za QReader (keširano kako bi se izbeglo ponovno učitavanje pri svakom kliku)
@st.cache_resource
def load_qreader():
    return QReader()

qreader = load_qreader()

def extract_receipt_data(url):
    """
    Konektuje se na sajt Poreske uprave i parsira stavke sa računa.
    Napomena: HTML struktura sajta se može menjati. Ovo je bazični parser 
    koji hvata standardne elemente e-fiskalizacije.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = []
        
        # Poreska uprava često drži stavke u listi ili gridu. 
        # Najčešće se podaci o artiklima nalaze u elementima koji sadrže klase vezane za 'invoice-item' ili slično.
        # Ukoliko se DOM struktura sajta promeni, ovde je potrebno ažurirati CSS selektore.
        
        # Primer selektora (Prilagodi nakon testiranja na konkretnom linku Poreske uprave):
        # Nalazimo blokove koji sadrže artikle
        item_rows = soup.find_all("div", class_=re.compile("row.*item.*", re.IGNORECASE)) 
        
        # Ako specifičan dizajn koristi tabele:
        tables = soup.find_all("table")
        if tables:
            df_list = pd.read_html(str(tables[0]))
            if df_list:
                return df_list[0] # Vraća pandas dataframe ako je račun formatiran kao HTML tabela
                
        # Alternativno čupanje teksta ukoliko je layout drugačiji
        for row in item_rows:
            # Ovo su placeholderi za tipične nazive klasa
            name = row.find(class_=re.compile("name", re.IGNORECASE))
            qty = row.find(class_=re.compile("quantity", re.IGNORECASE))
            price = row.find(class_=re.compile("price", re.IGNORECASE))
            
            if name and price:
                items.append({
                    "Naziv": name.get_text(strip=True),
                    "Količina": qty.get_text(strip=True) if qty else "1",
                    "Iznos": price.get_text(strip=True)
                })
                
        if not items:
             st.warning("Uspelo je očitavanje linka, ali nismo pronašli artikle na stranici. HTML struktura Poreske uprave se možda promenila.")
             return pd.DataFrame()
             
        return pd.DataFrame(items)

    except Exception as e:
        st.error(f"Greška pri preuzimanju podataka sa sajta: {e}")
        return pd.DataFrame()

def process_image(image_file):
    # Konverzija fajla u OpenCV BGR format koji QReader očekuje
    image = Image.open(image_file)
    img_array = np.array(image)
    
    # Ako je slika RGBA (png), konvertuj u RGB
    if len(img_array.shape) > 2 and img_array.shape[2] == 4:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
    img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    with st.spinner("Skeniranje QR koda pomoću AI modela..."):
        decoded_texts = qreader.detect_and_decode(image=img_cv2)
        
    if not decoded_texts or decoded_texts[0] is None:
        st.error("QR kod nije pronađen ili je previše oštećen. Pokušaj sa boljim osvetljenjem.")
        return
        
    url = decoded_texts[0]
    st.success("QR Kod uspešno očitan!")
    st.info(f"Link: {url}")
    
    if "suf.purs.gov.rs" in url:
        with st.spinner("Preuzimanje podataka sa sajta Poreske uprave..."):
            df = extract_receipt_data(url)
            if not df.empty:
                st.subheader("Stavke sa računa")
                st.dataframe(df, use_container_width=True)
    else:
        st.warning("Očitani kod ne vodi na sajt Poreske uprave (suf.purs.gov.rs).")

# UI Aplikacije
st.title("🧾 SUF Skener Fiskalnih Računa")
st.write("Skeniraj ili otpremi sliku fiskalnog računa kako bi automatski preuzeo stavke sa sajta Poreske uprave.")

tab1, tab2 = st.tabs(["📸 Kamera", "📁 Upload Slike"])

with tab1:
    camera_img = st.camera_input("Slikaj QR kod sa računa")
    if camera_img is not None:
        process_image(camera_img)

with tab2:
    uploaded_img = st.file_uploader("Otpremi sliku računa", type=['png', 'jpg', 'jpeg'])
    if uploaded_img is not None:
        process_image(uploaded_img)
