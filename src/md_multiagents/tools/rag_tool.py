from crewai.tools import BaseTool
from pathlib import Path
import re

class RagTool(BaseTool):
    name: str = "RAG Tool"
    description: str = "根据知识库检索相关指南条目"

    chunk_dir: Path = Path("knowledge/ad_chunks")

    def _run(self, query: str) -> str:
        results = []
        keywords = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]+", query)

        for file in self.chunk_dir.glob("*.txt"):
            text = file.read_text(encoding="utf-8")
            # 简单关键字匹配
            if any(word in text for word in keywords):
                results.append(text.strip())

        if not results:
            return "未检索到相关指南条目。"

        # 返回前 3 条，避免上下文过长
        return "\n\n".join(results[:3])