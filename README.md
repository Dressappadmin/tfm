# 👗 DressApp

Repositorio principal para el desarrollo y despliegue de OutfitAI, el motor y API del proyecto DressApp.

---

## Estructura del Repositorio

Nota: La carpeta del entorno virtual (venv) no se sube a Git porque contiene ejecutables y rutas exclusivas de cada sistema operativo. Cada desarrollador debe crear la suya localmente.

```text
tfm/
│
├── modulos/                     # Lógica principal de IA, negocio y algoritmos
│   ├── __init__.py
│   ├── buscar_prendas_similares_pgvector.py
│   ├── buscar_prendas_similares.py      # Búsqueda vectorial en RAM (Similitud Coseno con NumPy)
│   ├── cargar_modelos.py        # Inicialización de FashionCLIP y rembg en el arranque
│   ├── completar_outfit.py      # Generación de outfits, detección de color y metadatos AI
│   ├── eliminar_imagen_bucket.py
│   ├── eliminar_prenda_bd.py
│   ├── procesar_imagen.py       # Eliminación de fondo y redimensión de imágenes (PIL)
│   └── recomendar_posts.py       # Algoritmo híbrido para el feed social de posts

│
├── utils/                       # Funciones auxiliares aisladas y reutilizables
│   ├── __init__.py
│   ├── calcular_embedding.py         # Extracción del vector de 512 dimensiones
│   ├── cargar_imagen_url_bucket.py   # Descarga optimizada de imágenes desde URLs/Storage
│   ├── cargar_imagen_url_publica.py
│   ├── eliminar_prenda_bd.py
│   ├── normalizar_vector.py      # Normalización L2 de vectores para similitud
│   ├── registrar_outfit_bd.py
│   └── registrar_prenda_bd.py
│
├── data/                        # Gestión de persistencia y catálogo en memoria
│   ├── __init__.py
│   └── cargar_tabla_memoria.py             # Cliente de Supabase, carga de 'catalog' y matriz NumPy
│
├── schemas/                     # Modelos de validación Pydantic (FastAPI input/output)
│   ├── __init__.py
│   └── outfits.py               # Esquemas (ej. OutfitMetadataAI, OutfitCreate)
│
├── api.py                      # Punto de entrada FastAPI + manejador Lifespan
├── config.py                    # Variables de entorno y constantes (PRENDAS, OUTFITS)
├── requirements.txt             # Dependencias del proyecto para el contenedor
├── Dockerfile                   # Configuración para despliegue en Google Cloud Run
├── .env                         # Variables de entorno locales (NO SE SUBE A GIT)
├── .gitignore                   # Archivos y carpetas excluidos del control de versiones
├── .dockerignore
└── README.md                    # Documentación, comandos de build y despliegue
```

---

## 1. Requisitos Previos

Antes de empezar, asegúrate de tener instalado en tu equipo:
* Python: Versión 3.11.9 (imprescindible coincidir con la versión 3.11 definida en el proyecto).
* Git: Para el control de versiones.
* VS Code: Como editor de código recomendado.
* Google Cloud SDK (gcloud) y Docker: (Solo necesario para quienes vayan a construir y desplegar en producción).

---

## 2. Configuración Inicial y Git (Setup Local)

Para descargar el repositorio por primera vez en tu ordenador y empezar a trabajar:

1. Abre una terminal en la carpeta de tu ordenador donde quieras guardar el proyecto.
2. Configura tu usuario (si no lo tienes configurado globalmente) y conecta el repositorio local ejecutando los siguientes comandos:

   git config --global user.name "Dressappadmin"
   git config --global user.email "dressappadmin@gmail.com"
   git init
   git remote add origin https://github.com/Dressappadmin/tfm.git
   git pull origin main

3. ¡Importante para la organización! No trabajes directamente en la rama main. Crea y cámbiate a tu propia rama de desarrollo personal:

   git checkout -b develop_nombre

   (Reemplaza nombre por tu nombre, por ejemplo: develop_laura o develop_carlos).

---

## 3. Configuración del Entorno Virtual en VS Code

Una vez descargados los archivos, debemos configurar el entorno aislado para instalar las librerías:

1. Abre VS Code y selecciona Archivo > Abrir carpeta... para abrir la carpeta del proyecto (tfm).
2. Abre una terminal integrada en VS Code (Ctrl + ñ o Ver > Terminal).
3. Crea tu entorno virtual ejecutando:

   python -m venv venv

   (Nos dará a elegir la versión de Python; elegimos la 3.11.9, y si no la tenemos hay que descargarla).
4. Activa el entorno virtual según tu sistema operativo:

   * Windows (PowerShell):
     .\venv\Scripts\Activate.ps1

     Solución a error común en Windows: Si PowerShell te muestra un error en rojo diciendo que la ejecución de scripts está deshabilitada, ejecuta primero este comando y luego vuelve a activar el entorno:
     Set-ExecutionPolicy Unrestricted -Scope Process

   * Windows (CMD - Símbolo del sistema):
     venv\Scripts\activate

   * macOS / Linux:
     source venv/bin/activate

   (Sabrás que está activado porque aparecerá (venv) al inicio de la línea en tu terminal).

5. Selecciona el intérprete en VS Code para el autocompletado:
   * Pulsa Ctrl + Shift + P (en Mac: Cmd + Shift + P).
   * Escribe y selecciona: Python: Select Interpreter (o Seleccionar intérprete).
   * Elige la opción que apunta a la carpeta local: venv/bin/python o venv\Scripts\python.exe.

6. Instala todas las librerías del proyecto ejecutando en la terminal de VS Code:

   pip install -r requirements.txt

---

## 4. Flujo de Trabajo Diario

Cuando vuelvas a abrir el proyecto otro día para programar, el proceso es muy simple:

1. Abre la terminal de VS Code y activa el entorno virtual.
2. Descarga los últimos cambios de la rama principal por si un compañero subió algo:

   git pull origin main

3. (Opcional) Si se añadieron nuevas librerías, actualiza tus dependencias:

   pip install -r requirements.txt

4. ¡Ponte a programar en tu rama develop_nombre!

---

## 5. Despliegue en Google Cloud Platform (Docker & Cloud Run)

Instrucciones para empaquetar la aplicación y subirla a producción en Google Cloud Run.

⚠️ ATENCIÓN: En los siguientes comandos, recuerda cambiar v7 por el número de versión incremental que corresponda subir (ej: v8, v9, etc.).

### Paso 1: Requisitos previos en la terminal
1. Asegúrate de haber guardado todos tus archivos en el editor y estar en la raíz del proyecto (cd ruta/carpeta/tfm):

   cd ruta/carpeta/tfm

2. Instalar las librerías de gcloud (esto cambia según el sistema operativo). En Linux Fedora:

   sudo dnf install gcloud

### Paso 2: Autenticación en Google Cloud
Iniciar sesión en Google desde la terminal nos permite enlazar nuestra terminal con los servidores para ejecutar ahí comandos con el prefijo gcloud:

   gcloud auth login
   gcloud config set project dressapp-503311
   gcloud auth print-access-token | sudo docker login -u oauth2accesstoken --password-stdin https://europe-southwest1-docker.pkg.dev

### Paso 3: Construir, subir y desplegar la imagen
Ejecuta los siguientes comandos en orden (cambiando el 7 por la versión que toque):

   # 1. Construir el Docker
   En prod:
      sudo docker build -t europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7 .
   En dev:
      sudo docker build -t europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7-dev .

   # 2. Hacer el push
   En prod:
      sudo docker push europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7
   En dev:
      sudo docker push europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7-dev

   # 3. Ponerlo en marcha en Cloud Run
   En prod:
      gcloud run deploy outfitai-api \
         --image europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7 \
         --region europe-southwest1 \
         --set-env-vars SUPABASE_URL="tu_url_de_supabase",SUPABASE_KEY="tu_anon_key_de_supabase"
   En dev:
      gcloud run deploy outfitai-api \
         --image europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7-dev \
         --region europe-southwest1 \
         --set-env-vars SUPABASE_URL="tu_url_de_supabase",SUPABASE_KEY="tu_anon_key_de_supabase"

---

## 6. Atajos Rápidos y Comandos Útiles

### Ver los logs de producción
Podemos cambiar el límite a nuestro antojo para leer los registros, en prod:

   gcloud run services logs read outfitai-api --region europe-southwest1 --limit 60

o en dev:

   gcloud run services logs read outfitai-api-dev --region europe-southwest1 --limit 60

### Despliegue rápido (Modificaciones posteriores)
Cuando se modifique el código, una vez guardado, si no es la primera vez que tenemos que iniciar sesión, podemos pegar directamente en la terminal los pasos seguidos (cambiando el 7 a la versión que corresponda). Además, no hace falta volver a pasar las variables de entorno:

En prod:
   gcloud auth print-access-token | sudo docker login -u oauth2accesstoken --password-stdin https://europe-southwest1-docker.pkg.dev
   sudo docker build -t europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7 .
   sudo docker push europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7
   gcloud run deploy outfitai-api --image europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v7 --region europe-southwest1

En dev:
   gcloud auth print-access-token | sudo docker login -u oauth2accesstoken --password-stdin https://europe-southwest1-docker.pkg.dev
   sudo docker build -t europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v1-dev .
   sudo docker push europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v1-dev
   gcloud run deploy outfitai-api-dev --image europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v1-dev --region europe-southwest1

Nota: puede ser que de errores debido a poca capacidad de cómputo. 
Como referencia, la última ejecución se hizo con los parámetros:
   gcloud run deploy outfitai-api-dev \
   --image europe-southwest1-docker.pkg.dev/dressapp-503311/outfitai-repo/outfitai-app:v1-dev \
   --region europe-southwest1 \
   --memory 8Gi \
   --cpu 2 \
   --timeout 300

### Probar la api en local
Abre una terminal de VSCode y escribe
   uvicorn api:app --reload --port 8000

Escribe en tu navegador:
   http://127.0.0.1:8000/docs

### Limpieza
Cuando se crean muchas imágenes de docker la basura se acumula... con este comando hacemos limpieza:
   docker system prune -a --volumes -f
