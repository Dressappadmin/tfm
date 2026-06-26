Estructura del repo:

tfm/
└── fashionclip/
    ├── .gitignore                # Para ignorar archivos basura, pycache, etc.
    ├── requirements.txt          # Lista de librerías (mlflow, azureml-mlflow, torch, etc.)
    ├── README.md                 # Instrucciones para que el equipo sepa arrancar
    │
    ├── notebooks/                
    │   └── 01_exploracion.ipynb  # Solo para pruebas rápidas y visualización (no para entrenar)
    │
    ├── src/                      # Todo el código ejecutable va aquí
    │   ├── __init__.py
    │   ├── config.py             # Variables globales (ej. nombre del Data Asset de imágenes)
    │   ├── data_loader.py        # Funciones para montar y leer las 3000 imágenes de Azure
    │   ├── model.py              # La lógica de FashionCLIP y extracción de características
    │   ├── evaluate.py           # Funciones para calcular métricas de acierto
    │   └── train.py              # El script principal: junta los datos, el modelo y activa MLflow
    │
    └── scripts/                  
        └── submit_job.py         # El código para enviar el trabajo pesado al Clúster GPU
