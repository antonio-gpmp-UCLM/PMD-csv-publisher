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
    latency: int           # Intervalo entre envíos (milisegundos)
    duration: int          # Tiempo total (segundos)
    id_max_paciente: int   # numero max de id de pacientes que tenemos

@app.post("/start-upload")
def start_upload(request: UploadRequest):
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    num_files = request.duration // (request.latency *1000)
    uploaded_files = []

    for i in range(num_files):
        # Generar datos aleatorios
        data = []
        id_max_paciente= 100 +request.rows
        for _ in range(request.rows):
            id_paciente = math.trunc(random.uniform(101, id_max_paciente))
            if generar_error_temperatura > 90:
  	         temperatura = round(random.uniform(-100, 100), 2)
            else:
             temperatura = round(random.uniform(20, 50), 2)
            SpO2 = round(random.uniform(60, 100), 2)
            timestamp = datetime.utcnow().isoformat()
            data.append({"id_paciente":id_paciente, "temperatura": temperatura, "SpO2": SpO2, "timestamp": timestamp })

        df = pd.DataFrame(data)

        # Convertir a CSV en memoria
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)

        # Construir la ruta completa: carpeta/subcarpeta/archivo.csv
        file_name = f"{request.folder_name}/{request.subfolder_name}/datos_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}.csv"

        # Construir la ruta completa: carpeta/subcarpeta/archivo.csv 
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
