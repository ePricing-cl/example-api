import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
EPRICING_OAUTH_URL = os.getenv("EPRICING_OAUTH_URL")
EPRICING_API_URL = os.getenv("EPRICING_API_URL")


def test_api_epricing_download():
    # 1. Obtener Token de Cognito
    print("Obteniendo token...")
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r_token = requests.post(EPRICING_OAUTH_URL, data=data)
    r_token.raise_for_status()
    access_token = r_token.json().get("access_token")

    # 2. Llamar a tu API con ese token
    print("Token obtenido satisfactoriamente. ")
    print("Llamando a ePricing API...")
    # access_token = "eyJraWQiOiJI..."
    headers = {"Authorization": f"Bearer {access_token}"}

    # Payload de ejemplo, ajusta según tus necesidades
    payload = {
        "report_type": "prices",
        "type_date": "day",  # 
        "dates_ranges": [{"start_date": "2026-04-01", "end_date": "2026-04-30"}],
        "filters": [
            {
                "key": "chain",
                "data_type": "STRING",
                "filter_type": "chain_filter",
                "values": ["Ahumada", "Cruz Verde", "Salcobrand", "Ligafarmacia", "Cofar"],
            }
            # {
            #     "key": "fabricante",
            #     "data_type": "STRING",
            #     "filter_type": "product_attribute",
            #     "values": ["Sophia"],
            # }
        ],
    }
    r_api = requests.post(EPRICING_API_URL, json=payload, headers=headers)
    r_api.raise_for_status()

    file_url = r_api.json().get("download_url")
    if file_url:
        # 1. Parsear la URL para quitar los parámetros de S3 (?X-Amz-...)
        path = urlparse(file_url).path
        # 2. Extraer el nombre del archivo (ej. "datos_2023.csv")
        filename = os.path.basename(path)

        # Si por alguna razón la URL no tiene nombre, asignamos uno personalizado
        if not filename:
            filename = "descarga.csv"

        # 3. Descargar
        response = requests.get(file_url, stream=True)
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Archivo guardado exitosamente como: {filename}")


test_api_epricing_download()
