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
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from _http import curl_get_json

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "sec"
RAW_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = os.environ.get("SEC_USER_AGENT", "ai-data-center-report zhaoyu192403@gmail.com")

CIKS = {
    "MSFT": "0000789019",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
    "META": "0001326801",
}

# 每个指标可能对应多个XBRL标签(公司会换标签)，按优先级列出，逐个尝试，
# 按财季末日期(end)合并——2026-08-16实测发现AMZN在2017年后不再用
# PaymentsToAcquirePropertyPlantAndEquipment披露capex，改用了PaymentsToAcquireProductiveAssets，
# 若只查第一个标签，AMZN 2017年后的资本开支会全部缺失。
TAGS = {
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "ocf": ["NetCashProvidedByUsedInOperatingActivities"],
}


def _get_json(url: str):
    return curl_get_json(url, headers={"User-Agent": USER_AGENT})


def quarterize(facts: list) -> list:
    """把累计披露的 USD 事实换算为单季度值。

    2026-08-16 实测发现：不同公司的10-Q披露结构不同——
    GOOGL/META 只披露"年初至今累计"(YTD)，每期都要靠累计值相减才能还原单季度；
    MSFT/AMZN 除YTD累计外，**还会在同一份10-Q里同时披露"当季3个月"的直接数值**
    (duration~90天，但start是当季起点而非财年起点)。之前把所有事实混在一起、只按
    "fy"标签分组做链式差分，会把direct数值错当成累计值参与运算，产出错误结果
    (曾实测出MSFT单季资本开支被错误放大到$850亿，真实值约$358亿)。
    AMZN还额外披露过去12个月滚动值(TTM, duration~365天但来自10-Q而非10-K)，
    这类不是财年累计，必须排除，否则会污染年度合计。

    正确算法：按 `start` 日期分组(同一start必然属于同一条"YTD累计链"——无论是
    财年起点的Q1/H1/9mo/Annual链，还是某家公司直接披露的单季度事实，后者的start
    就是那一季度自己的起点，自成一条长度为1的链，天然不会与别的链混淆)。
    每条链内部按duration升序排序做差分：第一项(通常dur~90，无论是Q1还是某个
    direct单季度)直接当作单季度值；后续每项 = 本项累计值 - 链内上一项累计值。
    duration 350-380天且来自10-Q(而非10-K)的项目在分组前整体剔除(TTM噪音)。
    """
    from datetime import date

    def parse(d):
        return date.fromisoformat(d)

    dedup = {}
    for f in facts:
        key = (f["start"], f["end"], f["val"])
        dedup[key] = f
    items = [
        f for f in dedup.values()
        if not (350 <= (parse(f["end"]) - parse(f["start"])).days <= 380 and f["form"] != "10-K")
    ]

    by_start = defaultdict(list)
    for f in items:
        by_start[f["start"]].append(f)

    out = {}
    for start, chain in by_start.items():
        chain.sort(key=lambda f: parse(f["end"]))
        prev_cum = None
        for it in chain:
            if prev_cum is None:
                q_val = it["val"]
            else:
                q_val = it["val"] - prev_cum
            prev_cum = it["val"]
            # 同一end日期可能被多条链算出一致的值(如MSFT的direct fact链与差分链)，
            # 后处理的覆盖前面的，两者理论上应相等
            out[it["end"]] = {
                "fy": it["fy"], "fp": it["fp"], "end": it["end"], "form": it["form"], "quarter_val": q_val,
            }

    return list(out.values())


def fetch_company(ticker: str, cik: str):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    print(f"拉取 {ticker} ({url}) ...")
    payload = _get_json(url)
    out_raw = RAW_DIR / f"{ticker}_companyfacts_raw.json"
    out_raw.write_text(json.dumps(payload, ensure_ascii=False))

    gaap = payload.get("facts", {}).get("us-gaap", {})
    result = {}
    for key, tag_candidates in TAGS.items():
        by_end = {}
        for tag in tag_candidates:
            node = gaap.get(tag)
            if not node:
                continue
            usd_facts = node.get("units", {}).get("USD", [])
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
            for row in quarterize(filtered):
                # 先到先得：排在前面的标签优先，同一end只用第一个覆盖到的标签的值
                by_end.setdefault(row["end"], row)
        if not by_end:
            print(f"  [WARN] {ticker} 缺少标签 {tag_candidates}", file=sys.stderr)
        result[key] = list(by_end.values())

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
