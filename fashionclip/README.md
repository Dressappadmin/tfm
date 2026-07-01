## ESTRUCTURA DEL REPO 
(provisional)

fashionclip/

│

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

## OTRAS COSAS

- NO usar tildes en los comentarios
- tener instalado mlflow


## PARA EJECUTAR PRUEBAS DEL MODELO EN AZURE ML

### Abrir el Workspace de azure

1. Abris azure con vuestra cuenta (lo hemos probado en la web, ns si la app esa local será igual)

2. Arriba a la derecha donde os sale vuestro directorio le dais a change directory o lo que sea

3. Vereis una lista con vuestro directorio y otro que se llama 'Default directory' cuyo owner soy yo. Le dais a cambiar o conmutar o lo que diga

4. Os pedirá que guardeis el acceso con authenticator bla bla bla

5. Una vez hecho eso estareis ya dentro. Os vais a 'todos los recursos'

6. Haceis click en uno que se llama FashionClip con simbolito de matraz

7. le dais y en información general hay un apartado que pone 'studio web url'. Haceis click

8. Os llevará a la página de MLFlow. Una vez ahí, click en la pestañita de 'trabajos (jobs)'. Ahí es donde se suben los resultados/ejecuciones de los modelos

9. Si veis un 'prueba-conexion-fashionclip' es que todo va como debe ir

### Conectar VS Code con los recursos de azure

1. Ir a proceso

2. Hay un 'recursobarato'. En aplicaciones, le dais a abrir con VS Code (local). Seguramente le tengais que dar a los tres puntitos para que salga. Si no está encendido, encendedlo antes.

3. Una vez en VS Code os pedirá quizá iniciar sesión con github en algún momento. Iniciad con la cuenta que creamos.

4. Cread un repositorio git como vimos en clase y haced un pull del repo ahí (Si teneis dudas de esto me avisais)

5. Ahora abrid en en vs code una terminal (en la barra de arriba está el botón).

6. Ejecutad una a una las siguientes lineas de comando:
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
conda create -n asistente_tfm python=3.10 -y
conda activate asistente_tfm
pip install "mlflow<3.5.0" "azureml-mlflow" torch transformers pandas langchain
pip install azure-identity azure-ai-ml
az login

7. az login os pedirá iniciar sesión y elegir un workspace para trabajar. Os aparecerá una lista con los workspaces numerados. poned el número del workspace que se corresponda al default que usamos en mlflow

8. Modificad la línea 8 del archivo .py con vuestro nombre:
    mlflow.set_experiment("prueba-conexion-fashionclip-nombre")

9. Guardad el archivo (ctrl + s)

10. ejecutad el archivo poniendo en la terminal:
    python prueba.py
Aseguraos de que estais en el directorio fashionclip. Seguramente tendreis que hacer un 'cd fashionclip' o similar antes

11. Si la ejecución acaba bien, id a la web de mlflow otra vez, a la pestaña de trabajos. Deberíais ver un 'prueba-conexion-fashionclip-nombre'. Eso es que ha ido todo bien!
