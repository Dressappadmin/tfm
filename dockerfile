# Usar la imagen oficial y ligera de Python 3.11
FROM python:3.11-slim

# Evitar la creación de archivos .pyc y asegurar que los logs se muestren en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cloud Run utiliza el puerto 8080 por defecto
ENV PORT=8080

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el código de la aplicación
COPY . .

# --- NUEVO: Descarga en caché de los modelos de IA ---
# Ejecutamos tu función de carga de modelos. Esto descargará FashionCLIP (y 
# cualquier otra IA como la de quitar fondos) y las guardará dentro de la imagen.
RUN python -c "from modulos.model_loader import cargar_modelos; cargar_modelos()"

# --- ACTUALIZADO: Comando de Producción ---
# Lanzamos FastAPI usando el puerto dinámico de Google
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]