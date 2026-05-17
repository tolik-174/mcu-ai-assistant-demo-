# import faiss
# import json
# from sentence_transformers import SentenceTransformer

# FAISS_PATH = "../data/faiss/local_multi.faiss"
# META_PATH = "../data/faiss/local_multi_meta.json"
# MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# def semantic_search(query, k=5):
#     model = SentenceTransformer(MODEL_NAME)
#     query_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
#     index = faiss.read_index(FAISS_PATH)
#     meta = json.load(open(META_PATH, "r", encoding="utf-8"))

#     D, I = index.search(query_emb.astype("float32"), k)
#     results = []
#     for i in I[0]:
#         if i < len(meta):
#             results.append(meta[i])
#     return results

# if __name__ == "__main__":
#     query = input(" Введи запит: ")
#     results = semantic_search(query, k=5)

#     for r in results:
#         print(f"\nSource: {r['source']}\n→ {r['text'][:400]}...")
#наразі нам його не потрібно при потребі додати зараз йог заміняє апп.ру