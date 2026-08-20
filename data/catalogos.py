# data/catalogo_memoria.py
from config import PRENDAS_TABLA, EMBEDDING_PRENDA
from data.cargar_tabla_memoria import cargar_tabla_memoria

print("Inicializando catálogo en memoria global...")

prendas, embeddings_prendas = cargar_tabla_memoria(PRENDAS_TABLA, embedding=EMBEDDING_PRENDA)