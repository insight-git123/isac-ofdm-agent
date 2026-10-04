"""任务1端到端：3GPP文档 → 波形参数提取 → params.yaml + 验证报告"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.pdf_parser import parse_and_cache
from src.retrieval.retriever import Retriever
from src.retrieval.citation import format_citation, save_citations
from src.validation.validators import (
    validate_numerology,
    validate_cp_duration,
    compute_normal_cp_us,
)

RAW = ROOT / "data" / "raw" / "ts38211.pdf"
PROCESSED = ROOT / "data" / "processed" / "ts38211_parsed.txt"
OUT = ROOT / "outputs" / "task1"
SOURCES = yaml.safe_load((ROOT / "config" / "sources.yaml").read_text(encoding="utf-8"))


def get_source(sid: str) -> dict:
    for s in SOURCES["sources"]:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def extract_numerology(text: str):
    """从 Table 4.2-1 区域抽取 mu / SCS / CP 类型（适配真实 3GPP PDF 排版）。"""
    retriever = Retriever(text)
    # 使用“4.2 Numerologies”作为起点，“4.3 Frame structure”作为终点
    table_lines = retriever.extract_section(
        "4.2 Numerologies", "4.3 Frame structure"
    )
    
    rows = []
    for line in table_lines:
        # 注意：这里改用 re.search，兼容 PDF 解析后数字与文字间的各种空格
        # 匹配形如 "0 15 Normal" / "2 60 Normal,Extended"
        m = re.search(
            r"(\d+)\s+(\d+)\s+(Normal(?:\s*,\s*Extended)?)",
            line, flags=re.IGNORECASE,
        )
        if not m:
            continue
        mu = int(m.group(1))
        scs = int(m.group(2))
        cp_raw = m.group(3).lower()
        
        cp_types = []
        if "normal" in cp_raw:
            cp_types.append("normal")
        if "extended" in cp_raw:
            cp_types.append("extended")
        rows.append({"mu": mu, "scs_khz": scs, "cp_types": cp_types})
        
    return rows


def enrich(rows):
    for r in rows:
        if "normal" in r["cp_types"]:
            r["cp_duration_us"] = round(compute_normal_cp_us(r["mu"]), 4)
        else:
            r["cp_duration_us"] = None
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. 解析 + 缓存
    text = parse_and_cache(RAW, PROCESSED)
    print(f"[ingestion] 解析 {RAW.name} → {len(text.splitlines())} 行")

    # 2. 抽取
    rows = extract_numerology(text)
    print(f"[extraction] 识别 {len(rows)} 条 numerology")
    rows = enrich(rows)

    # 3. 验证
    v1 = validate_numerology(rows)
    v2 = validate_cp_duration(rows)
    validation = {"numerology": v1, "cp_duration": v2}
    (OUT / "validation_report.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 4. 引用
    src = get_source("ts38211")
    citations = [
        {
            "section": "§4.2 Table 4.2-1",
            "citation": format_citation(src, "§4.2 Table 4.2-1"),
            "fields": ["mu", "scs_khz", "cp_types"],
        },
        {
            "section": "§4.3.1",
            "citation": format_citation(src, "§4.3.1"),
            "fields": ["cp_duration_us"],
        },
    ]
    save_citations(citations, OUT / "citations.json")

    # 5. 生成 params.yaml
    params = {
        "meta": {
            "project": "isac-ofdm-agent",
            "task": "task1_extraction",
            "release": SOURCES["release_lock"],
            "source": f"3GPP {src['number']} {src['version']}",
            "validation_passed": v1["passed"] and v2["passed"],
        },
        "numerology": rows,
    }
    (OUT / "params.yaml").write_text(
        yaml.safe_dump(params, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    # 同步到 config/
    (ROOT / "config" / "params.yaml").write_text(
        yaml.safe_dump(params, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    # 6. 汇总
    ok = v1["passed"] and v2["passed"]
    print(f"[validation] numerology: {'PASS' if v1['passed'] else 'FAIL'}")
    for e in v1["errors"]:
        print("   -", e)
    print(f"[validation] cp_duration: {'PASS' if v2['passed'] else 'FAIL'}")
    for e in v2["errors"]:
        print("   -", e)
    print(f"[output] {OUT / 'params.yaml'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())