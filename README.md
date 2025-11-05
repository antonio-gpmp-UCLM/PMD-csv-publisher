# PMD-csv-publisher

## Requisitos

- FastAPI (para la API)
- azure-storage-blob (para interactuar con Azure Blob Storage)
- pandas (para generar el CSV)
- random y datetime (para datos aleatorios)

## Estructura de la API

Endpoint: POST /create-csv
Parámetros:
- folder_name: carpeta dentro del contenedor
- subfolder_name: subcarpeta específica (por ejemplo, zona_norte)
- rows: número de filas
- latency: cada cuánto tiempo se envía un archivo (en segundos).
- duration: durante cuánto tiempo se estarán enviando archivos (en segundos).


## Acción

Generar y subir múltiples archivos CSV con columnas timestamp, temperatura y humedad al Blob Storage.
Cada archivo se sube después de esperar la latencia indicada.
El proceso termina cuando se cumple la duración.

