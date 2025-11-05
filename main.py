from fastapi import FastAPI
from pydantic import BaseModel
from azure.storage.blob import BlobServiceClient
import pandas as pd
import random
from datetime import datetime
import io
import time
import os

# Configuración Azure como variables de entorno
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING") 
CONTAINER_NAME =  os.getenv("AZURE_CONTAINER_NAME") 
#CONTAINER_NAME =  "contenedor-demo"

app = FastAPI()

class UploadRequest(BaseModel):
    folder_name: str       # Carpeta principal
    subfolder_name: str    # Subcarpeta específica
    rows: int              # Número de filas por archivo
    latency: int           # Intervalo entre envíos (segundos)
    duration: int          # Tiempo total (segundos)

@app.post("/start-upload")
def start_upload(request: UploadRequest):
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    num_files = request.duration // request.latency
    uploaded_files = []

    for i in range(num_files):
        # Generar datos aleatorios
        data = []
        for _ in range(request.rows):
            temperatura = round(random.uniform(15, 35), 2)
            humedad = round(random.uniform(30, 90), 2)
            timestamp = datetime.utcnow().isoformat()
            data.append({"timestamp": timestamp, "temperatura": temperatura, "humedad": humedad})

        df = pd.DataFrame(data)

        # Convertir a CSV en memoria
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)

        # Construir la ruta completa: carpeta/subcarpeta/archivo.csv
        file_name = f"{request.folder_name}/{request.subfolder_name}/datos_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}.csv"

        # Subir a Azure Blob Storage
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file_name)
        blob_client.upload_blob(csv_buffer.getvalue(), overwrite=True)
        uploaded_files.append(file_name)

        # Esperar latencia antes del siguiente envío
        if i < num_files - 1:
            time.sleep(request.latency)

    return {
        "message": f"{num_files} archivos subidos correctamente",
        "files": uploaded_files
    }
