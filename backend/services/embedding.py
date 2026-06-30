import hashlib
import httpx
import numpy as np
from typing import List
from config import settings


import hashlib

def _fallback_embedding(texts: List[str]) -> List[List[float]]:
    """未配置 Embedding API 时，生成基于文本哈希的确定性单位向量，避免零向量导致 pgvector 距离异常。"""
    dim = settings.EMBEDDING_DIMENSION
    results = []
    for text in texts:
        seed = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (2**32)
        rng = np.random.default_rng(seed)
        vec = rng.normal(size=dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm == 0:
            vec[0] = 1.0
        else:
            vec = vec / norm
        results.append(vec.tolist())
    return results


async def get_embedding(texts: List[str]) -> List[List[float]]:
    if not settings.EMBEDDING_API_KEY or not settings.EMBEDDING_API_URL:
        return _fallback_embedding(texts)

    BATCH_SIZE = 10  # 阿里云 dashscope text-embedding-v3 单次最多 10 条
    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            for attempt in range(2):
                try:
                    resp = await client.post(
                        settings.EMBEDDING_API_URL,
                        headers={"Authorization": f"Bearer {settings.EMBEDDING_API_KEY}"},
                        json={"model": "text-embedding-v3", "input": {"texts": batch}},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    embeddings = data.get("output", {}).get("embeddings", [])
                    # 按 text_index 排序，确保顺序一致
                    embeddings.sort(key=lambda x: x.get("text_index", 0))
                    results.extend([item["embedding"] for item in embeddings])
                    break
                except Exception as e:
                    if attempt == 1:
                        raise RuntimeError(f"Embedding API 调用失败: {e}")
    return results


def normalize(vec: List[float]) -> List[float]:
    arr = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return vec
    return (arr / norm).tolist()
