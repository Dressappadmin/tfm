/*
Lista de funciones, procedimientos o comandos almacenadas/ejectuados en Postgres necesarias/os para el funcionamiento del todos los routers.
Son las siguientes:
    - vector
    - buscar_prenda_por_slot_db
    - obtener_prenda_aleatoria_db
    - recomendar_feed_outfits
    - obtener_historial_usuario
*/

-- CREAR EL TIPO VECTOR
CREATE EXTENSION IF NOT EXISTS vector;

-- BUSCAR PRENDA POR SLOT
CREATE OR REPLACE FUNCTION buscar_prendas_por_slot_db(
    vector vector(512), 
    p_slot text,
    limite int
)
RETURNS TABLE (
    id uuid,                  
    slot text,                 
    color text,        
    embedding vector(512), 
    similitud float
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        prenda.id,
        prenda.slot,
        prenda.color,
        prenda.embedding,    
        (1 - (prenda.embedding <=> vector))::float AS similitud
    FROM 
        prenda
    WHERE 
        prenda.slot = p_slot
    ORDER BY 
        prenda.embedding <=> vector
    LIMIT 
        limite;
END;
$$;

-- BUSCAR PRENDA ALEATORIA
CREATE OR REPLACE FUNCTION obtener_prenda_aleatoria_db()
RETURNS SETOF prenda
LANGUAGE sql
AS $$
  SELECT *
  FROM prenda
  ORDER BY random()
  LIMIT 1;
$$;

-- RECOMENDAR FEED
CREATE OR REPLACE FUNCTION recomendar_feed_outfits(p_usuario_id uuid, p_limite int, p_offset int)
RETURNS SETOF posts_lucia
LANGUAGE plpgsql
AS $$
DECLARE
    v_usuario_embedding vector;
BEGIN
    SELECT embedding INTO v_usuario_embedding 
    FROM usuarios 
    WHERE id = p_usuario_id;

    IF v_usuario_embedding IS NULL THEN
        RETURN QUERY
        SELECT *
        FROM posts_lucia
        ORDER BY likes_count DESC, created_at DESC
        LIMIT p_limite
        OFFSET p_offset;
        
    ELSE
        RETURN QUERY
        SELECT p.*
        FROM posts_lucia p
        JOIN outfits o ON p.outfit_id = o.id
        ORDER BY o.embedding <=> v_usuario_embedding
        LIMIT p_limite
        OFFSET p_offset;
        
    END IF;
END;
$$;

-- HISTORIAL USUARIO
CREATE OR REPLACE FUNCTION obtener_historial_usuario(p_usuario_id uuid, p_max_items int)
RETURNS TABLE (
    embedding vector,
    color text
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.embedding, 
        p.color
    FROM interacciones_usuario i
    JOIN prenda p ON i.prenda_id = p.id
    WHERE i.usuario_id = p_usuario_id 
      AND i.is_good = TRUE
    ORDER BY i.fecha_interaccion DESC
    LIMIT p_max_items;
END;
$$;