from typing import Any
from data.supabase import supabase

def buscar_prendas_similares_pgvector(
    embedding_usuario: list[float], 
    top_n: int = 3
) -> list[dict[str, Any]] | None:
    '''
    Busca las N prendas del catálogo más similares a un vector de embedding mediante pgvector en Supabase.
    
    Llama a una función RPC (Remote Procedure Call) almacenada en PostgreSQL que calcula la 
    similitud visual en la base de datos a partir del vector del usuario.

    Parameters
    ----------
    embedding_usuario : list[float]
        Vector flotante numérico (ej. de 512 dimensiones obtenido mediante FashionCLIP) 
        que representa las características visuales de la imagen de entrada.
    top_n : int, opcional
        Número de prendas más afines estéticamente a retornar, por defecto 3.

    Precondition
    ------------
    La función RPC 'buscar_prendas_similares_db' y la extensión 'pgvector' deben estar 
    previamente instaladas y configuradas en el servidor de PostgreSQL/Supabase.

    Returns
    -------
    list[dict[str, Any]] | None
        Lista de diccionarios con la información de las prendas similares encontradas y su 
        grado de similitud/distancia, o None si ocurre un fallo o no hay registros.
    '''
    try:
        respuesta = supabase.rpc(
            "buscar_prendas_similares_db",
            {
                "vector_usuario": embedding_usuario,
                "top_n": top_n
            }
        ).execute()

        return respuesta.data

    except Exception as e:
        print(f"❌ Error al realizar la búsqueda vectorial con pgvector: {e}")
        return None


'''
Procedure SQL
CREATE OR REPLACE FUNCTION buscar_prendas_similares_db(
  vector_usuario vector(512),
  top_n int DEFAULT 3
)
RETURNS SETOF prendas AS $$
BEGIN
  RETURN QUERY
  SELECT *
  FROM prendas
  ORDER BY embedding <=> vector_usuario -- '<=>' es el operador de distancia coseno en pgvector
  LIMIT top_n;
END;
$$ LANGUAGE plpgsql;


En Supabase (SQL): Activar pgvector y crear un índice HNSW

En tu consola SQL de Supabase ejecutarías:
-- 1. Activar la extensión vectorial
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Convertir la columna embedding al tipo vector(512)
ALTER TABLE prendas ALTER COLUMN embedding TYPE vector(512);

-- 3. Crear un índice HNSW para búsquedas instantáneas entre millones de filas
CREATE INDEX ON prendas USING hnsw (embedding vector_cosine_ops);
'''