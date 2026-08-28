# Usamos una imagen ligera de Python
FROM python:3.11-slim

# Configuramos el directorio de trabajo
WORKDIR /app

# Evita que Python escriba archivos .pyc y fuerza salida por consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalamos las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Cloud Run escucha en el puerto 8080
EXPOSE 8080

# Comando para lanzar Streamlit
CMD ["streamlit", "run", "votar_outfits.py", "--server.port=8080", "--server.address=0.0.0.0"]