import random

def obtener_historial(usuario_id: str, max_items: int = 10):
    """
    Mock que simula la respuesta de una base de datos.
    Devuelve las últimas interacciones positivas del usuario.
    """
    historial = []
    
    # Simulamos que el usuario tiene entre 3 y max_items prendas en su historial
    num_prendas = random.randint(3, max_items)
    
    categorias_posibles = [
        'SUPERIOR', 'INFERIOR', 'CUERPO_COMPLETO', 
        'ABRIGO', 'CALZADO', 'ACCESORIO'
    ]
    
    for i in range(num_prendas):
        # Simulamos un embedding CLIP de tamaño 512 (valores aleatorios entre -1 y 1)
        # En la vida real, esto lo sacas de tu base de datos vectorial o PostgreSQL (pgvector)
        vector_falso = [random.uniform(-1.0, 1.0) for _ in range(512)]
        
        item = {
            "prenda_id": f"prenda_mock_{usuario_id}_{i}",
            "categoria": random.choice(categorias_posibles),
            "embedding": vector_falso, 
            "fecha_interaccion": f"2026-08-{random.randint(10,28)}T12:00:00Z",
            "is_good": True
        }
        historial.append(item)
        
    return historial