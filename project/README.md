# 数据规划执行 — 项目骨架

对应《全民反对，美国 AI 基建的"逆风"？》数据规划与配图规格 v1（20幅核心图 + 4幅备选图）。

## 现状速览（2026-08-16，第二轮更新）

第一轮执行时，沙盒环境出站网络受限，只能靠WebSearch摘要拼凑零散数字。用户调整了
环境的网络策略后，**FRED / SEC EDGAR / BLS(QCEW+PPI) 三个数据源已验证可正常访问，
并已实际拉取到真实、完整、可复核的数据**：

| 数据源 | 覆盖图 | 规模 | 亮点 |
|---|---|---|---|
| SEC EDGAR | F14/F15 | 4家公司(MSFT/AMZN/GOOGL/META) 2008-2026逐季，258行 | MSFT 2026Q4单季资本开支$850.72亿 |
| BLS QCEW | F07 | NAICS 518210分县，2014-2025逐季，102,300行 | Loudoun County VA 2025Q4: 2,131名员工 |
| BLS PPI | F17 | 变压器制造业指数，2017-2026月度，115点 | 10年间指数+105% |
| FRED | F03兜底/F05 | 全国电价，1978-2026月度，573点 | 完整基准线 |

仍未解决的：**EIA**（网络已通，缺免费API key）、**PJM**（网站可访问，未定位到历年BRA数据文件）、
**LBNL emp.lbl.gov**（被Cloudflare机器人防护拦截，与出站网络策略无关，curl/Playwright headless
浏览器+伪装UA均403）。详见 `docs/DATA_GAPS.md`。

## 目录说明

1. **`config/sources.yaml`**：文档§1全部数据源(E/G/M/C/J/W/P/O系列)的URL、级别、获取方式
2. **`src/fetch/`**：四个fetch脚本(EIA/FRED/SEC EDGAR/BLS)，均已重构为用curl子进程发请求
   （本环境的Python urllib/requests对多个站点会间歇性挂起或报HTTP/2流错误，`--http1.1`修复），
   三个已跑通产出真实数据，EIA待用户提供API key
3. **`data/raw/`**：
   - `sec/capex_quarterly_by_fiscal_period.csv`、`bls/qcew_518210_combined.csv`、
     `bls/ppi_transformers.csv`、`fred/APU000072610.csv` —— 真实一手数据
   - `manual/websearch_facts_2026-08-16.csv` —— 第一轮WebSearch采集的约35条二手转述锚点，
     仍保留作为交叉参考，但已被上述一手数据在覆盖范围内取代
4. **`docs/SOURCES.md`** / **`docs/CAVEATS.md`** / **`docs/DATA_GAPS.md`**：出处记录、口径限制、
   逐图数据缺口报告（两轮对比，哪些图从"未获取"提升到"已获取"）

**没有产出**：`figures/`下的实际PNG/SVG图表和`src/clean/`/`src/plot/`清洗画图脚本。
下一步该做这个——四个真实数据源已经到位，可以先把F07/F15/F17开始清洗画图。

## 下一步

优先级见 `docs/DATA_GAPS.md`「按severity排序的下一步优先级」，简版：

1. 拿到EIA免费API key（https://www.eia.gov/opendata/register.php）→ 补齐F03分州电价
2. 人工提供LBNL Queued Up数据文件（emp.lbl.gov被Cloudflare拦截，需人工下载或换渠道）→ 解决F09/F10
3. 深入PJM网站定位历年BRA出清价数据 → 补齐F04
4. 写 `src/clean/` 清洗脚本，把已有的4组真实数据整理成 `data/processed/F*.csv`
5. 写 `src/plot/` 画图脚本，产出F07/F15/F17的正式图表
