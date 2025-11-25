from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import asyncio
import requests
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

# variable de entorno definida en la Web App en Azure para ser utilizada por la api para comprobar si está autorizado
API_KEY = os.getenv("API_KEY")
# api_key utilizada en la invocación
API_KEY_NAME = "X-API-Key"

app = FastAPI()

# --- Definir esquema de seguridad ---
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# async def get_api_key(api_key: str = Depends(api_key_header)):
#    if api_key != API_KEY:
#        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
#    return api_key

async def verify_api_key(x_api_key: APIKeyHeader(name=API_KEY_NAME, auto_error=False)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return True


# @app.get("/get-env")
# def get_env():
#    valor =  = os.getenv("API_KEY", "nodefinida")
#    return f"Valor de la variable: {valor}"


 class UploadRequest(BaseModel):
    folder_name: str       # Carpeta principal
    subfolder_name: str    # Subcarpeta específica
    rows: int              # Número de filas por archivo
    latency: int           # Intervalo entre envíos (milisegundos)
    duration: int          # Tiempo total (segundos)
    
#@app.post("/send-data")
#async def send_data(folder_name: str, subfolder_name: str, rows: int, latency: int, duration: int, api_key: str = Depends(get_api_key)):
    
@app.post("/start-upload")
def start_upload(request: UploadRequest, authorized: bool = Depends(verify_api_key)):
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    num_files = request.duration // (request.latency *1000)
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

        # Construir la ruta completa: carpeta/subcarpeta/archivo.csv si
        if not request.subfolder_name: #si no hay subcarpeta lo guarda en la ruta principal
            file_name = f"{request.folder_name}/datos_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}.csv"
        else:
            file_name = f"{request.folder_name}/{request.subfolder_name}/datos_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}.csv"

        # Subir a Azure Blob Storage
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file_name)
        blob_client.upload_blob(csv_buffer.getvalue(), overwrite=True)
        uploaded_files.append(file_name)

        # Esperar latencia antes del siguiente envío
        if i < num_files - 1:
            time.sleep(request.latency/1000) #el parámetro de sleep está en segundos

    return {
        "message": f"{num_files} archivos subidos correctamente",
        "files": uploaded_files
    }
