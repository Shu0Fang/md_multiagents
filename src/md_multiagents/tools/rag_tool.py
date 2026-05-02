from crewai.tools import BaseTool
from pathlib import Path
import re


class RagTool(BaseTool):
    name: str = "RAG Tool"
    description: str = "根据知识库检索相关指南条目（优先向量检索，失败时关键词兜底）"

    index_dir: Path = Path("knowledge/faiss_index")
    chunk_dir: Path = Path("knowledge/ad_chunks")
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    top_k: int = 5

    def _keyword_fallback(self, query: str) -> str:
        """Fallback retrieval when FAISS index is unavailable."""
        results = []
        keywords = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]+", query)

        for file in self.chunk_dir.glob("*.txt"):
            text = file.read_text(encoding="utf-8")
            hits = sum(1 for word in keywords if word in text)
            if hits > 0:
                results.append((hits, file.name, text.strip()))

        if not results:
            return "未检索到相关指南条目。"

        results.sort(key=lambda x: x[0], reverse=True)
        rendered = []
        for hits, filename, content in results[: self.top_k]:
            rendered.append(
                f"[SOURCE: {filename}; SCORE: {hits}; MODE: keyword]\n{content}"
            )
        return "\n\n".join(rendered)

    def _run(self, query: str) -> str:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import FAISS

            if not self.index_dir.exists():
                return self._keyword_fallback(query)

            embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            vectorstore = FAISS.load_local(
                str(self.index_dir),
                embeddings,
                allow_dangerous_deserialization=True,
            )

            docs_with_scores = vectorstore.similarity_search_with_score(query, k=self.top_k)
            if not docs_with_scores:
                return "未检索到相关指南条目。"

            rendered = []
            for doc, score in docs_with_scores:
                source = doc.metadata.get("source", "unknown")
                rendered.append(
                    f"[SOURCE: {source}; SCORE: {float(score):.4f}; MODE: vector]\n{doc.page_content.strip()}"
                )
            return "\n\n".join(rendered)
        except Exception:
            # 任何依赖/索引异常都回落到关键词检索，保证主流程可用
            return self._keyword_fallback(query)