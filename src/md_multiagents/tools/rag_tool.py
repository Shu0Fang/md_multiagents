from crewai import BaseTool

class RagTool(BaseTool):
    name = "RAG Tool"
    description = "根据知识库检索相关指南条目"

    def _run(self, query: str):
        # 简单实现：遍历 knowledge 目录文本，找包含 query 关键字的条目
        results = []
        for line in open("knowledge/ad_guideline_2020.txt", encoding="utf-8"):
            if any(word in query for word in line.strip().split()):
                results.append(line.strip())
        return results