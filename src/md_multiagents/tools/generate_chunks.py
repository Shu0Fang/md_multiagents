import re
from pathlib import Path

# 可选：用于向量化
# from sentence_transformers import SentenceTransformer
# import faiss
# import pickle

txt_path = Path("knowledge/202412051733385834695675.txt")
chunk_dir = Path("knowledge/ad_chunks")
chunk_size = 500      # 每个 chunk 字符数，可根据需要调整
chunk_overlap = 100   # 相邻 chunk 重叠字符数
min_core_hits = 2     # 质量阈值：chunk 至少命中多少个核心关键词
min_cjk_ratio = 0.35  # 质量阈值：中文字符占比下限
min_len = 120         # 质量阈值：chunk 最小长度

chunk_dir.mkdir(parents=True, exist_ok=True)

CORE_HINTS = (
    "诊断", "标准", "推荐", "检查", "评估", "症状", "体征", "分期", "分级",
    "认知", "MRI", "PET", "脑脊液", "生物标志物", "可逆", "鉴别", "治疗",
    "MMSE", "MoCA", "ADL", "IADL", "BPSD", "海马", "风险",
)


def _is_page_noise(line: str) -> bool:
    # 常见页码/页眉页脚样式
    if re.fullmatch(r"\d{1,4}", line):
        return True
    if "中华老年医学杂志" in line and "Vol." in line:
        return True
    if "ChinJGeriatr" in line and "Vol." in line:
        return True
    return False


def _is_reference_line(line: str) -> bool:
    # 参考文献编号行，如 [12] xxx
    if re.match(r"^\[\d+\]", line):
        return True
    # 参考文献常见噪声关键词
    lowered = line.lower()
    if "doi:" in lowered:
        return True
    if "et al" in lowered or "lancet" in lowered or "jama" in lowered:
        return True
    return False


def _is_author_meta(line: str) -> bool:
    # 作者/单位/邮箱等元信息，通常不用于医学知识检索
    if "通信作者" in line or "email:" in line.lower():
        return True
    if line.startswith("中国阿尔茨海默病痴呆诊疗指南"):
        return True
    if line.startswith("·规范与指南·"):
        return True
    if re.match(r"^\d+.*\d{6,}$", line):
        return True
    if line.endswith(".com") or line.endswith(".cn"):
        return True
    return False


def _contains_core_hint(line: str) -> bool:
    return any(k in line for k in CORE_HINTS)


def _contains_cjk(line: str) -> bool:
    return re.search(r"[\u4e00-\u9fff]", line) is not None


def _is_english_noise(line: str) -> bool:
    lowered = line.lower()
    if any(k in lowered for k in ("doi", "et al", "lancet", "jama", "neurol", "meta-analysis")):
        return True

    # 无中文且英文字母占比高，通常是参考文献英文残片
    letters = sum(ch.isascii() and ch.isalpha() for ch in line)
    ratio = letters / max(len(line), 1)
    if not _contains_cjk(line) and ratio > 0.35:
        return True

    # 纯英文符号长句，通常不是指南正文
    if re.fullmatch(r"[A-Za-z0-9\s,.;:()\-/\[\]’'\"]+", line) and len(line) > 20:
        return True

    return False


def _normalize_line(raw_line: str) -> str:
    line = raw_line.replace("\u3000", " ").strip()
    line = re.sub(r"\s+", " ", line)
    # 去掉中文字符之间的异常空格，缓解 OCR 断裂
    line = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", line)
    return line


def clean_lines(raw_text: str) -> list[str]:
    lines = raw_text.replace("\r\n", "\n").split("\n")

    cleaned_lines = []
    in_reference_section = False
    started_body = False
    reached_tail_meta = False

    for raw_line in lines:
        line = _normalize_line(raw_line)
        if not line:
            continue

        # 跳过文首元信息，优先从摘要/正文开始
        if not started_body:
            if "【摘要】" in line or line.startswith("一、"):
                started_body = True
            else:
                continue

        # 进入参考文献区后默认全部跳过
        if line.startswith("参考文献"):
            in_reference_section = True
            continue
        if in_reference_section:
            continue

        # 到达尾部元信息区（专家名单/致谢等）后停止采集
        if any(
            marker in line
            for marker in (
                "指南小组共识调查专家",
                "指南小组循证医学人员",
                "致谢",
                "执笔",
                "作者贡献",
                "利益冲突",
            )
        ):
            reached_tail_meta = True
        if reached_tail_meta:
            continue

        # 强保留医学核心线索（避免误删）
        if _contains_core_hint(line):
            cleaned_lines.append(line)
            continue

        if _is_page_noise(line):
            continue
        if _is_reference_line(line):
            continue
        if _is_author_meta(line):
            continue
        if _is_english_noise(line):
            continue

        cleaned_lines.append(line)

    return cleaned_lines


def chunk_text(lines: list[str], size: int, overlap: int) -> list[str]:
    # 按行拼接，避免字符硬切造成句子截断
    chunks = []
    buffer: list[str] = []
    buffer_len = 0

    for line in lines:
        line_len = len(line) + 1
        if (buffer_len + line_len <= size) or (not buffer):
            buffer.append(line)
            buffer_len += line_len
            continue

        chunks.append("\n".join(buffer))

        # 取上一个 chunk 末尾若干行作为重叠上下文
        overlap_lines = []
        overlap_len = 0
        for prev in reversed(buffer):
            prev_len = len(prev) + 1
            if overlap_lines and overlap_len + prev_len > overlap:
                break
            overlap_lines.append(prev)
            overlap_len += prev_len

        overlap_lines.reverse()
        buffer = overlap_lines + [line]
        buffer_len = sum(len(x) + 1 for x in buffer)

    if buffer:
        chunks.append("\n".join(buffer))

    return chunks


def _core_hit_count(text: str) -> int:
    return sum(1 for k in CORE_HINTS if k in text)


def _cjk_ratio(text: str) -> float:
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return cjk_chars / max(len(text), 1)


def filter_chunks(chunks: list[str]) -> tuple[list[str], dict]:
    kept = []
    stats = {
        "total": len(chunks),
        "drop_short": 0,
        "drop_core": 0,
        "drop_ratio": 0,
    }

    for chunk in chunks:
        if len(chunk) < min_len:
            stats["drop_short"] += 1
            continue

        if _core_hit_count(chunk) < min_core_hits:
            stats["drop_core"] += 1
            continue

        if _cjk_ratio(chunk) < min_cjk_ratio:
            stats["drop_ratio"] += 1
            continue

        kept.append(chunk)

    return kept, stats


def clear_old_chunks(output_dir: Path) -> int:
    removed = 0
    for old in output_dir.glob("chunk_*.txt"):
        old.unlink(missing_ok=True)
        removed += 1
    return removed


def main() -> None:
    with open(txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    lines = clean_lines(raw_text)
    chunks = chunk_text(lines, chunk_size, chunk_overlap)
    chunks, stats = filter_chunks(chunks)

    removed = clear_old_chunks(chunk_dir)

    for i, chunk in enumerate(chunks, start=1):
        chunk_path = chunk_dir / f"chunk_{i:03d}.txt"
        with open(chunk_path, "w", encoding="utf-8") as f:
            f.write(chunk)

    print(f"已清理旧 chunk: {removed} 个")
    print(f"生成 {len(chunks)} 个 chunk，存放在 {chunk_dir}")
    print(
        "质量过滤统计: "
        f"原始={stats['total']} "
        f"短文本剔除={stats['drop_short']} "
        f"核心词不足剔除={stats['drop_core']} "
        f"中文占比不足剔除={stats['drop_ratio']}"
    )


if __name__ == "__main__":
    main()

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