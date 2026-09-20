# SUF Skener Fiskalnih Računa

Streamlit aplikacija koja koristi naprednu AI detekciju (YOLOv8 preko `qreader` biblioteke) za čitanje oštećenih i loše odštampanih QR kodova sa srpskih fiskalnih računa i preuzimanje stavki sa sajta Poreske uprave (suf.purs.gov.rs).

## Pokretanje u lokalnom okruženju

1. Kreiraj virtuelno okruženje i aktiviraj ga:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
