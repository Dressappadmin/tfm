import numpy as np
import json
from config import COL_FAMILY

def buscar_similares(query_emb: np.ndarray, catalog: list, top_k=6, excluir_family: str = None) -> list:
    results = []
    for item in catalog:
        emb_raw = item.get('embedding')
        if emb_raw is None:
            continue
        if isinstance(emb_raw, str):
            emb_raw = json.loads(emb_raw)
        if excluir_family and item.get(COL_FAMILY, '').lower() == excluir_family.lower():
            continue
        emb = np.array(emb_raw, dtype=np.float32)
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        score = float(np.dot(query_emb, emb))
        results.append({**item, 'similarity': score})
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]