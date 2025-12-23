from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED
from pydantic import BaseModel
from azure.storage.blob import BlobServiceClient
import pandas as pd
import random
from datetime import datetime
import io
import time
import os
import math

# Configuración Azure
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
API_KEY_AUTORIZADA = os.getenv("API_KEY")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verificar_api_key(api_key_param: str = Depends(api_key_header)):
    if api_key_param != API_KEY_AUTORIZADA:
        raise HTTPException(status_code=401, detail="API Key no válida")
    return True

app = FastAPI(title="API de Generación de Datos para Databricks (Escenarios Batch)")

class UploadRequest(BaseModel):
    folder_name: str       # 'sin_particionar' o 'particionado'
    rows: int = 100        # Aumentamos filas por defecto para ver rendimiento
    latency: int = 1000    # ms
    duration: int = 10     # segundos
    id_max_paciente: int = 10

def generar_datos_csv(rows, id_max):
    """Función auxiliar para generar un DataFrame con datos aleatorios"""
    data = []
    for _ in range(rows):
        id_paciente = random.randint(1, id_max)
        # Simulación de errores (10% de probabilidad)
        if random.random() > 0.9:
            temp = round(random.uniform(-10, 100), 2)
        else:
            temp = round(random.uniform(35.5, 41.0), 2)
        
        data.append({
            "id_paciente": id_paciente,
            "temperatura": temp,
            "SpO2": round(random.uniform(90, 100), 2),
            "timestamp": datetime.utcnow().isoformat()
        })
    return pd.DataFrame(data)

def subir_a_azure(blob_service_client, path, content):
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=path)
    blob_client.upload_blob(content, overwrite=True)

@app.post("/upload-standard", dependencies=[Depends(verificar_api_key)])
def upload_standard(request: UploadRequest):
    """ESCENARIO 1: Sin particionamiento en origen"""
    if not AZURE_CONNECTION_STRING or not CONTAINER_NAME:
        raise HTTPException(status_code=500, detail="Variables de entorno Azure no configuradas")

    client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    num_files = max(1, math.trunc(request.duration / (request.latency / 1000)))
    uploaded = []

    for i in range(num_files):
        df = generar_datos_csv(request.rows, request.id_max_paciente)
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        
        # Ruta estándar: carpeta/archivo.csv
        file_path = f"{request.folder_name}/datos_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}.csv"
        
        subir_a_azure(client, file_path, csv_buf.getvalue())
        uploaded.append(file_path)
        if i < num_files - 1: time.sleep(request.latency/1000)

    return {"message": "Escenario Standard completado", "files": uploaded}

@app.post("/upload-partitioned", dependencies=[Depends(verificar_api_key)])
def upload_partitioned(request: UploadRequest):
    """ESCENARIO 2: Con particionamiento id_paciente=X en origen"""
    if not AZURE_CONNECTION_STRING or not CONTAINER_NAME:
        raise HTTPException(status_code=500, detail="Variables de entorno Azure no configuradas")

    client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    num_files = max(1, math.trunc(request.duration / (request.latency / 1000)))
    uploaded = []

    for i in range(num_files):
        # En cada envío, generamos datos de UN SOLO PACIENTE para simular el particionado físico real
        p_id = random.randint(1, request.id_max_paciente)
        df = generar_datos_csv(request.rows, request.id_max_paciente)
        # Forzamos a que todo este archivo sea del mismo paciente para la partición física
        df['id_paciente'] = p_id 
        
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        
        # RUTA CRÍTICA PARA DATABRICKS: carpeta/id_paciente=X/archivo.csv
        file_path = f"{request.folder_name}/id_paciente={p_id}/datos_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}.csv"
        
        subir_a_azure(client, file_path, csv_buf.getvalue())
        uploaded.append(file_path)
        if i < num_files - 1: time.sleep(request.latency/1000)

    return {"message": "Escenario Particionado completado", "files": uploaded}
