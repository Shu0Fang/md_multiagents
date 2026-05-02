from pathlib import Path
import shutil


def build_index(
    chunk_dir: Path = Path("knowledge/ad_chunks"),
    index_dir: Path = Path("knowledge/faiss_index"),
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
) -> None:
    from langchain_community.docstore.document import Document
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    if not chunk_dir.exists():
        raise FileNotFoundError(f"chunk directory not found: {chunk_dir}")

    files = sorted(chunk_dir.glob("chunk_*.txt"))
    if not files:
        raise RuntimeError(f"no chunk files found in: {chunk_dir}")

    docs = []
    for file in files:
        text = file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        docs.append(Document(page_content=text, metadata={"source": file.name}))

    if not docs:
        raise RuntimeError("all chunk files are empty after trimming")

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = FAISS.from_documents(docs, embeddings)

    if index_dir.exists():
        shutil.rmtree(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_dir))

    print(f"index built: {index_dir}")
    print(f"chunks indexed: {len(docs)}")
    print(f"embedding model: {model_name}")


if __name__ == "__main__":
    build_index()
