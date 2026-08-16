"""
拉取 Census Bureau BTOS(Business Trends and Outlook Survey) 的AI使用率数据。

对应用户提出的新需求："AI应用深度增加/工作中使用增加"的真实时间序列——用于强化F02
（当前F02只有Pew的个人AI使用率一条线，缺"工作场景/企业采用"这个维度）。

数据源发现记录（2026-08-16）：BTOS官网是React SPA，真实API藏在前端JS bundle里，
通过 grep app.js 找到 api_base="/hfp/btos/api"，实际端点为
https://www.census.gov/hfp/btos/api/periods/{period_id}/data
（不在标准data.census.gov目录/data.json目录下，需要这样发现）。

核心问题(从Period 31起，即2023-09-11起，保持问法不变，可安全连成一条线)：
  "In the last two weeks, did this business use Artificial Intelligence (AI) in
   producing goods or services?" (current)
  "During the next six months, do you think this business will be using
   Artificial Intelligence (AI) in producing goods or services?" (expected)
全国口径 = STATE/NAICS2/NAICS3/EMPSIZE/MSA 全部为null的那一行。
已用Period 31验证：Yes=3.7%，与NBER Working Paper w32319摘要("3.7% in Sept 2023")完全一致。

用法：python fetch_btos.py --start-period 31 --end-period 106
输出：data/raw/census_btos/F02_btos_ai_use_national.csv
      列: period_id, date_range, metric(current/expected), answer(Yes/No/Do not know), pct
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from _http import curl_get_json

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "census_btos"
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "https://www.census.gov/hfp/btos/api/periods"

Q_CURRENT = (
    "In the last two weeks, did this business use Artificial Intelligence (AI) in producing "
    "goods or services? (Examples of AI: machine learning, natural language processing, "
    "virtual agents, voice recognition, etc.)"
)
Q_EXPECTED = (
    "During the next six months, do you think this business will be using Artificial "
    "Intelligence (AI) in producing goods or services? (Examples of AI: machine learning, "
    "natural language processing, virtual agents, voice recognition, etc.)"
)

# 2025-11-17(period 88)起，原问题被替换为口径更宽的新问法("任意业务环节"而非"生产商品/服务")，
# 是两个不同的指标，绝不可与上面的Q_CURRENT/Q_EXPECTED连成同一条线。分别抓取，分别标注metric。
Q_CURRENT_V2 = (
    "In the last two weeks, did this business use Artificial Intelligence (AI) in any of its "
    "business functions? (Examples of AI: machine learning, natural language processing, "
    "virtual agents, voice recognition, etc.)"
)
Q_EXPECTED_V2 = (
    "During the next six months, do you think this business will be using Artificial "
    "Intelligence (AI)  in any of its business functions? (Examples of AI: machine learning, "
    "natural language processing, virtual agents, voice recognition, etc.)"
)


def is_national(row: dict) -> bool:
    return all(row.get(k) is None for k in ("STATE", "NAICS2", "NAICS3", "EMPSIZE", "MSA"))


QUESTION_MAP = [
    (Q_CURRENT, "current_v1_goods_services"),
    (Q_EXPECTED, "expected_v1_goods_services"),
    (Q_CURRENT_V2, "current_v2_any_function"),
    (Q_EXPECTED_V2, "expected_v2_any_function"),
]


def fetch_period(period_id: int, null_retries: int = 4):
    """拉取单期数据。API在连续密集请求时会对个别期返回JSON字面量null(非报错，
    HTTP 200但body=null)，实测这是限流/瞬时问题，加大间隔重试即可拿到真实数据。"""
    url = f"{API_BASE}/{period_id}/data"
    for attempt in range(null_retries):
        data = curl_get_json(url, headers={"User-Agent": "ai-data-center-report/1.0"}, timeout=40)
        if data:
            break
        time.sleep(4 + attempt * 3)
    if not data:
        return None, []

    out_rows = []
    date_range = data[0]["DATE_RANGE"] if data else None
    for q, metric in QUESTION_MAP:
        for row in data:
            if row["QUESTION"] == q and is_national(row):
                out_rows.append(
                    {
                        "period_id": period_id,
                        "date_range": date_range,
                        "metric": metric,
                        "answer": row["ANSWER"],
                        "pct": row["ESTIMATE_PERCENTAGE"],
                        "standard_error": row["STANDARD_ERROR"],
                    }
                )
    return date_range, out_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-period", type=int, default=31)
    parser.add_argument("--end-period", type=int, default=106)
    args = parser.parse_args()

    all_rows = []
    for p in range(args.start_period, args.end_period + 1):
        try:
            date_range, rows = fetch_period(p)
        except Exception as e:
            print(f"[WARN] period {p} 拉取失败: {e}", file=sys.stderr)
            continue
        if not rows:
            print(f"[WARN] period {p}: 无AI问题数据(重试后仍为空，该期可能真的未发布)", file=sys.stderr)
            continue
        all_rows.extend(rows)
        print(f"period {p} ({date_range}): {len(rows)} 行")
        time.sleep(1.5)

    out_csv = RAW_DIR / "F02_btos_ai_use_national.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["period_id", "date_range", "metric", "answer", "pct", "standard_error"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    meta = {
        "source": "Census Bureau Business Trends and Outlook Survey (BTOS), core AI questions",
        "url_template": "https://www.census.gov/hfp/btos/api/periods/{period_id}/data",
        "url_discovered_via": "front-end JS bundle (https://www.census.gov/hfp/btos/js/app.*.js), "
        "not in standard data.census.gov catalog",
        "accessed": datetime.now(timezone.utc).isoformat(),
        "question_current": Q_CURRENT,
        "question_expected": Q_EXPECTED,
        "national_filter": "STATE=NAICS2=NAICS3=EMPSIZE=MSA=null",
        "verification": "Period 31 (2023-09-11~09-24) Yes=3.7%，与NBER Working Paper w32319摘要一致",
        "question_current_v2": Q_CURRENT_V2,
        "question_expected_v2": Q_EXPECTED_V2,
        "notes": (
            "*_v1_goods_services: Period 31(2023-09-11)至Period 87(2025-11-16)期间的问法，"
            "限定'生产商品或服务'场景，可安全连成一条时间序列。"
            "*_v2_any_function: Period 88(2025-11-17)起替换为更宽泛的'任意业务环节使用AI'问法，"
            "是另一个不同的指标，两者绝不可连成同一条线(问法变了，口径不可比)。"
        ),
    }
    (RAW_DIR / "F02_btos_ai_use_national_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"写入 {out_csv} ({len(all_rows)} 行)")


if __name__ == "__main__":
    main()
