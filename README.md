# 👗 DressApp

Repositorio principal para el desarrollo y despliegue de OutfitAI, el motor y API del proyecto DressApp.

---

## Estructura del Repositorio

Nota: La carpeta del entorno virtual (venv) no se sube a Git porque contiene ejecutables y rutas exclusivas de cada sistema operativo. Cada desarrollador debe crear la suya localmente.

```text
tfm/
│
├── api/                         # Capa de Enrutamiento (Endpoints HTTP con FastAPI)
│   ├── __init__.py
│   ├── router_chat.py           # Endpoints del Agente Conversacional (Function Calling)
│   ├── router_outfits.py        # Endpoints de generación y recomendación multimodal de moda
│   ├── router_posts.py          # Endpoints para la publicación y visualización de outfits en el feed
│   └── router_prendas.py        # Endpoints CRUD para la gestión del armario virtual del usuario
│
├── core/                        # Configuración global y ciclo de vida de la aplicación
│   ├── __init__.py
│   ├── config.py                # Variables de entorno y constantes del sistema (Cloud Run, Supabase)
│   └── cargar_modelos.py        # Lógica de carga de pesos de PyTorch y FashionCLIP en RAM (Lifespan)
│
├── crud/                        # Capa de Acceso a Datos (Supabase / PostgreSQL con pgvector)
│   ├── __init__.py
│   ├── funciones_bd.sql         # Procedimientos almacenados y funciones (ej. búsquedas vectoriales)
│   ├── outfits.py               # Gestión transaccional de los looks generados y guardados
│   ├── posts.py                 # Operaciones de BD para interacciones y publicaciones sociales
│   ├── prendas.py               # Consultas SQL y búsquedas de similitud del coseno (KNN)
│   ├── storage.py               # Interfaz con Supabase Storage (carga, descarga y gestión de imágenes)
│   └── usuarios.py              # Gestión de perfiles y persistencia de datos de usuario
│
├── ia/                          # Motor de Deep Learning (Modelos, Inferencia y Pipelines)
│   ├── __init__.py
│   ├── modelos/
│   │   └── AttentionOutfitGenerator.py # Arquitectura basada en Transformers/Multi-Head Attention (PyTorch)
│   ├── pesos/                   # Directorio para almacenar los pesos preentrenados (.pt / .pth)
│   ├── device.py                # Configuración dinámica del hardware de ejecución (CPU/CUDA/MPS)
│   ├── ejecutar_pipeline_outfit.py     # Orquestador: une la inferencia de la red neuronal con pgvector
│   ├── InfoNCELoss.py           # Función de pérdida para aprendizaje contrastivo (Contrastive Learning)
│   └── utils_tensores.py        # Transformaciones matemáticas, embeddings multimodales (Multi-hot, Mean Pooling)
│
├── schemas/                     # Contratos de Datos y Validación (Pydantic)
│   ├── __init__.py
│   ├── ChatRequest.py           # Validación de entrada para la interacción con el LLM
│   ├── GenerarOutfitRequest.py  # Parámetros para la predicción y generación del modelo
│   ├── OutfitEmbeddingRequest.py# Esquema para el espacio latente/vectorial de un conjunto completo
│   ├── ProcesarPrendaRequest.py # Datos de entrada para la extracción de características visuales
│   └── ValidarOutfitRequest.py  # Estructura para las peticiones de evaluación lógica de la ropa
│
├── services/                    # Lógica de Negocio y Conexión con APIs Externas
│   ├── __init__.py
│   ├── generador_contenido.py   # Integración con el LLM para descripciones y tips de estilo
│   ├── procesar_imagen.py       # Interfaz con los modelos de Visión Artificial para procesar las prendas
│   └── validar_reglas_outfit.py # Evaluación de conjunto mínimo viable (top + bottom, lógicas de calzado, etc.)
│
├── training/                    # Entorno de Entrenamiento MLOps (Excluido de Producción)
│   ├── __init__.py 
│   ├── config.yaml              # Hiperparámetros de entrenamiento (learning rate, epochs, batch size)
│   ├── dataset.py               # Lógica del DataLoader y aumentación (Random Item Drop / Masking)
│   ├── entrenamiento.py         # Loop principal de entrenamiento (Forward, Backward pass, Optimizadores)
│   └── perdida.py               # Función de pérdida customizada para el ajuste de similitud vectorial
│
├── utils/                       # Utilidades transversales, limpieza de datos y estáticos
│   ├── __init__.py
│   ├── catalogos.py             # Taxonomías fijas de moda, mapeos de slots y vocabularios
│   └── helpers.py               # Funciones puras de soporte genérico
│
├── main.py                      # Punto de entrada de FastAPI y registro unificado de Routers
├── requirements.txt             # Dependencias del proyecto (PyTorch, FastAPI, Supabase, etc.)
├── Dockerfile                   # Receta de construcción de la imagen para Google Cloud Run
├── .env.example                 # Plantilla de variables de entorno seguras
├── .dockerignore                # Archivos excluidos del contenedor de producción (ej: /training, venv)
└── README.md                    # Documentación técnica e instrucciones de despliegue
```

---

## 1. Requisitos Previos

Antes de empezar, asegúrate de tener instalado en tu equipo:

* **Python:** Versión 3.11.9 (imprescindible para coincidir con la versión definida en el proyecto).
* **Git:** Para el control de versiones.
* **VS Code:** Como editor de código recomendado.
* **Google Cloud SDK (gcloud) y Docker:** Solo necesario para los encargados de construir y desplegar en producción.

Los siguientes comandos están diseñados para terminales basadas en Linux/Unix. Existen alternativas equivalentes para otros sistemas operativos.
---

## 2. Configuración Inicial y Git (Setup Local)

Para descargar el repositorio por primera vez en tu equipo y empezar a trabajar:

1. Abre una terminal en la carpeta local donde quieras alojar el proyecto.
2. Configura tu usuario (si no lo tienes configurado globalmente) y vincula el repositorio ejecutando:

   git config --global user.name "[TU_USUARIO_GIT]"
   git config --global user.email "[TU_CORREO_GIT]"
   git init
   git remote add origin https://github.com/[TU_ORGANIZACION]/[TU_REPOSITORIO].git
   git pull origin main

---

## 3. Configuración del Entorno Virtual en VS Code

Es fundamental configurar un entorno aislado para las librerías del proyecto:

1. Abre VS Code y selecciona **Archivo > Abrir carpeta...** para abrir la carpeta del proyecto.
2. Abre una terminal integrada (Ctrl + ñ o **Ver > Terminal**).
3. Crea tu entorno virtual ejecutando:

   python -m venv venv

   *(Selecciona la versión 3.11.9 si el sistema te lo solicita).*

4. Activa el entorno virtual:

     source venv/bin/activate

   *(Sabrás que está activado porque aparecerá `(venv)` al inicio de tu línea de comandos).*

5. Selecciona el intérprete en VS Code para habilitar el autocompletado:
   * Pulsa `Ctrl + Shift + P` (en Mac: `Cmd + Shift + P`).
   * Escribe y selecciona: **Python: Select Interpreter**.
   * Elige la opción que apunta a la carpeta local (`venv/bin/python` o `venv\Scripts\python.exe`).

6. Instala las dependencias del proyecto:

   pip install -r requirements.txt

---

## 4. Flujo de Trabajo Diario

Cuando retomes el proyecto para seguir programando, sigue estos pasos:

1. Abre la terminal de VS Code y **activa el entorno virtual**.
2. Descarga los últimos cambios de la rama principal para mantenerte sincronizado con el equipo:

   git pull origin main

3. Si se han añadido nuevas librerías, actualiza tus dependencias:

   pip install -r requirements.txt

4. ¡Listo! Ya puedes empezar a programar en tu rama `develop_[tu_nombre]`.

---

## 5. Despliegue en Google Cloud Platform (Docker & Cloud Run) desde LINUX

Instrucciones para empaquetar la aplicación y subirla a producción.

> **ATENCIÓN:** En los siguientes comandos, recuerda cambiar `vX` por el número de versión incremental correspondiente (ej. `v8`, `v9`, etc.).

### Paso 1: Preparación
Asegúrate de haber guardado todos los archivos y de estar ubicado en la raíz del proyecto:
   
   cd ruta/a/tu/proyecto

   *(Si usas Linux Fedora, asegúrate de tener instalado gcloud: `sudo dnf install gcloud`)*.

### Paso 2: Autenticación en Google Cloud
Si tenías otra sesión iniciada, ciérrala primero:
   
   gcloud auth revoke --all

A continuación, inicia sesión y configura el proyecto (Ejemplo para entorno principal):
   
   gcloud auth login
   gcloud config set project [ID_PROYECTO_GCP]
   gcloud auth print-access-token | sudo docker login -u oauth2accesstoken --password-stdin https://[REGION]-docker.pkg.dev

### Paso 3: Construir, subir y desplegar la imagen

Sigue el orden a continuación, reemplazando `vX` por tu versión actual.

**1. Construir la imagen Docker:**
   
   sudo docker build -t [REGION]-docker.pkg.dev/[ID_PROYECTO_GCP]/[NOMBRE_REPO]/[NOMBRE_APP]:vX .

**2. Subir la imagen (Push):**
   
   sudo docker push [REGION]-docker.pkg.dev/[ID_PROYECTO_GCP]/[NOMBRE_REPO]/[NOMBRE_APP]:vX

**3. Desplegar en Cloud Run:**
   
   gcloud run deploy [NOMBRE_SERVICIO_API] \
      --image [REGION]-docker.pkg.dev/[ID_PROYECTO_GCP]/[NOMBRE_REPO]/[NOMBRE_APP]:vX \
      --region [REGION] \
      --set-env-vars SUPABASE_URL="[URL_SUPABASE]",SUPABASE_KEY="[CLAVE_SUPABASE]",LLM_API_KEY="[CLAVE_API_LLM]"

---

## 6. Atajos Rápidos y Comandos Útiles

### Ver los logs del servicio
Puedes ajustar el límite de líneas leídas con el parámetro `--limit`.

   gcloud run services logs read [NOMBRE_SERVICIO_API] --region [REGION] --limit 60

### Probar la API en local
Para levantar el servidor localmente con recarga automática:
   
   uvicorn api:app --reload --port 8000

Una vez iniciado, abre en tu navegador la documentación interactiva: http://127.0.0.1:8000/docs

### Configuración avanzada de hardware en Cloud Run
Si la API presenta problemas por falta de recursos (timeout o memoria), puedes utilizar parámetros adicionales en el despliegue. Ejemplo de una configuración superior:
   
   gcloud run deploy [NOMBRE_SERVICIO_API] \
      --image [REGION]-docker.pkg.dev/[ID_PROYECTO_GCP]/[NOMBRE_REPO]/[NOMBRE_APP]:vX \
      --region [REGION] \
      --memory 8Gi \
      --cpu 2 \
      --timeout 300

### Limpieza de Docker
La creación de múltiples imágenes puede llenar el almacenamiento de tu disco. Para limpiar contenedores, imágenes y volúmenes en desuso, ejecuta:
   
   docker system prune -a --volumes -f