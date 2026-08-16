"""
拉取 SEC EDGAR XBRL companyfacts，供 F14/F15（四大厂商资本开支/经营现金流/自由现金流）使用。

前置条件：
  - SEC 要求所有请求带能识别请求者的 User-Agent（形如 "组织名 邮箱"），否则会被拒绝。
    修改下面 USER_AGENT 变量为真实联系邮箱，或设置环境变量 SEC_USER_AGENT。
  - 无需 API key。

用法：
  python fetch_sec_edgar.py

输出：
  data/raw/sec/{TICKER}_companyfacts.json   原始整份 companyfacts（体积较大，仅存关键标签的提取结果供复核）
  data/raw/sec/capex_quarterly.csv          四家公司按日历季对齐后的资本开支/经营现金流/自由现金流

技术要点（对应文档 §1.4 备注）：
  - XBRL 标签: PaymentsToAcquirePropertyPlantAndEquipment (capex)
             NetCashProvidedByUsedInOperatingActivities (经营现金流)
  - 10-Q 披露的是"本财年累计"(YTD)数值，需要用相邻两期的差值还原出单季度值；
    10-K 年报披露的是全年数值，第四季度 = 全年 - 前三季度累计。
  - 微软(MSFT)财年 6 月结束，其"财季"与日历季错位一个季度，需要在清洗阶段
    额外做日历年对齐（见 src/clean/clean_sec_edgar.py，此处只做原始抓取+同财年内的季度换算）。
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "sec"
RAW_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = os.environ.get("SEC_USER_AGENT", "ai-data-center-report research@example.com")

CIKS = {
    "MSFT": "0000789019",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
    "META": "0001326801",
}

TAGS = {
    "capex": "PaymentsToAcquirePropertyPlantAndEquipment",
    "ocf": "NetCashProvidedByUsedInOperatingActivities",
}


def _get_json(url: str, retries: int = 3):
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except (HTTPError, URLError) as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def quarterize(facts: list) -> list:
    """把累计披露的 USD 事实换算为单季度值。
    facts: [{start, end, val, form, fy, fp}, ...] 按 end 升序
    返回: [{end, fy, fp, quarter_val}]
    简化算法：同一财年内，若本期 duration 明显长于90天，减去同财年内上一期累计值。
    """
    from datetime import date

    def parse(d):
        return date.fromisoformat(d)

    by_fy = defaultdict(list)
    for f in facts:
        by_fy[f["fy"]].append(f)

    out = []
    for fy, items in by_fy.items():
        items = sorted(items, key=lambda x: parse(x["end"]))
        prev_cum = 0
        prev_end = None
        for it in items:
            dur = (parse(it["end"]) - parse(it["start"])).days
            if dur <= 100:
                # 已经是单季度披露
                q_val = it["val"]
            else:
                q_val = it["val"] - prev_cum
            out.append(
                {
                    "fy": fy,
                    "fp": it["fp"],
                    "end": it["end"],
                    "form": it["form"],
                    "quarter_val": q_val,
                }
            )
            prev_cum = it["val"]
            prev_end = it["end"]
    return out


def fetch_company(ticker: str, cik: str):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    print(f"拉取 {ticker} ({url}) ...")
    payload = _get_json(url)
    out_raw = RAW_DIR / f"{ticker}_companyfacts_raw.json"
    out_raw.write_text(json.dumps(payload, ensure_ascii=False))

    gaap = payload.get("facts", {}).get("us-gaap", {})
    result = {}
    for key, tag in TAGS.items():
        node = gaap.get(tag)
        if not node:
            print(f"  [WARN] {ticker} 缺少标签 {tag}", file=sys.stderr)
            result[key] = []
            continue
        usd_facts = node.get("units", {}).get("USD", [])
        # 只保留 10-Q / 10-K 的公司自身报告(非修订)
        filtered = [
            {
                "start": f["start"],
                "end": f["end"],
                "val": f["val"],
                "form": f["form"],
                "fy": f["fy"],
                "fp": f["fp"],
            }
            for f in usd_facts
            if f.get("form") in ("10-Q", "10-K") and "start" in f
        ]
        result[key] = quarterize(filtered)

    return result


def main():
    all_rows = []
    for ticker, cik in CIKS.items():
        try:
            result = fetch_company(ticker, cik)
        except Exception as e:
            print(f"[WARN] {ticker} 拉取失败: {e}", file=sys.stderr)
            continue

        capex_by_end = {r["end"]: r["quarter_val"] for r in result.get("capex", [])}
        ocf_by_end = {r["end"]: r["quarter_val"] for r in result.get("ocf", [])}
        ends = sorted(set(capex_by_end) | set(ocf_by_end))
        for end in ends:
            capex = capex_by_end.get(end)
            ocf = ocf_by_end.get(end)
            fcf = (ocf - capex) if (capex is not None and ocf is not None) else None
            all_rows.append(
                {
                    "company": ticker,
                    "cik": cik,
                    "fiscal_period_end": end,
                    "capex_usd": capex,
                    "operating_cash_flow_usd": ocf,
                    "fcf_usd": fcf,
                }
            )

    import csv

    out_csv = RAW_DIR / "capex_quarterly_by_fiscal_period.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["company", "cik", "fiscal_period_end", "capex_usd", "operating_cash_flow_usd", "fcf_usd"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    meta = {
        "source": "SEC EDGAR XBRL companyfacts API",
        "url_template": "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        "tags": TAGS,
        "accessed": datetime.now(timezone.utc).isoformat(),
        "notes": (
            "按'财季末日期'(fiscal_period_end)输出，非日历季；"
            "MSFT财年6月结束，需在 src/clean/ 阶段对齐日历季度后才能与AMZN/GOOGL/META同图比较。"
            "季度值由累计披露值(YTD)相减还原，Q1为直接披露值，Q2-Q4为差分结果，10-K年报的Q4值=全年-前三季度累计。"
        ),
    }
    (RAW_DIR / "capex_quarterly_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"写入 {out_csv} ({len(all_rows)} 行)")


if __name__ == "__main__":
    main()
