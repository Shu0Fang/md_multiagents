import os
from pathlib import Path

# 可选：用于向量化
# from sentence_transformers import SentenceTransformer
# import faiss
# import pickle

# ------------------------------
# 参数设置
# ------------------------------
txt_path = Path("knowledge/202412051733385834695675.txt")
chunk_dir = Path("knowledge/ad_chunks")
chunk_size = 500      # 每个 chunk 字符数，可根据需要调整
chunk_overlap = 100   # 相邻 chunk 重叠字符数

chunk_dir.mkdir(parents=True, exist_ok=True)

# ------------------------------
# 读取文本
# ------------------------------
with open(txt_path, "r", encoding="utf-8") as f:
    text = f.read()

# 清理多余换行
text = text.replace("\r\n", "\n").replace("\n\n", "\n").strip()

# ------------------------------
# 拆成 chunk
# ------------------------------
chunks = []
start = 0
while start < len(text):
    end = start + chunk_size
    chunk = text[start:end]
    chunks.append(chunk)
    start += chunk_size - chunk_overlap  # 保持重叠

# ------------------------------
# 保存 chunk 文件
# ------------------------------
for i, chunk in enumerate(chunks):
    chunk_path = chunk_dir / f"chunk_{i+1:03d}.txt"
    with open(chunk_path, "w", encoding="utf-8") as f:
        f.write(chunk)

print(f"生成 {len(chunks)} 个 chunk，存放在 {chunk_dir}")

# ------------------------------
# 可选：生成向量存储
# ------------------------------
# model = SentenceTransformer("all-MiniLM-L6-v2")
# embeddings = model.encode(chunks)
# 
# index = faiss.IndexFlatL2(embeddings.shape[1])
# index.add(embeddings)
# 
# # 保存索引和 chunk 原文
# faiss.write_index(index, "knowledge/faiss_index.index")
# with open("knowledge/chunks.pkl", "wb") as f:
#     pickle.dump(chunks, f)
# 
# print("FAISS 索引生成完成，可用于 RAG 检索")