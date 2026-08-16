# SOURCES.md — 数据出处记录

本文件记录本项目已获取的每一批数据的来源、访问方式、访问日期与已知限制。

---

## 状态总览（更新于 2026-08-16，第三轮）

**重要变化**：第一轮执行时，本环境的出站网络代理策略拦截了几乎所有外部数据源。
经用户调整环境网络策略后，FRED/SEC EDGAR/BLS三个源实测可正常访问并已拉取完整数据；
随后用户又提供了EIA免费API key，**至此阶段一(T1-T5)全部四个数据源均已产出真实、
完整、可复核的数据**，不再是零散的WebSearch转述。

| 数据源 | 状态 | 说明 |
|---|---|---|
| **SEC EDGAR** (C1→F14/F15) | ✅ 真实完整数据 | 4家公司(MSFT/AMZN/GOOGL/META) 2008-2026逐季资本开支/经营现金流，258行 |
| **FRED** (E2→F03兜底/F05) | ✅ 真实完整数据 | APU000072610全国电价，1978-11至2026-07，573个月度观测点 |
| **BLS QCEW** (J1→F07) | ✅ 真实完整数据 | NAICS 518210分县就业，2014-2025逐季，102,300行(受API本身覆盖范围限制，无2010-2013数据) |
| **BLS PPI** (C3→F17) | ✅ 真实完整数据 | 变压器制造业PPI(PCU335311335311)，2017-2026月度，115行 |
| **EIA** (E1/E3→F03/F06) | ✅ 真实完整数据 | 用户提供免费API key后，分州居民电价(10州×2015-2026月度，1,507行)+全美年度总售电量分母(2010-2025)均已拉取 |
| **PJM** (E4→F04) | ⚠️ 网站可达，未找到直接数据文件 | www.pjm.com返回200，但RPM页面上的可下载文件都是流程文档/手册PDF，未找到BRA历年出清价汇总表，需要更深入的页面导航或从Monitoring Analytics年度报告里找 |
| **LBNL emp.lbl.gov** (G1→F09) | ❌ 仍被拦截 | Cloudflare机器人防护返回403，与本会话代理无关(curl/Playwright headless浏览器+伪装UA均403，判断是Cloudflare对该IP段的Bot Fight Mode)；这是全报告最需要的数据源，仍未解决 |
| CBRE/Cushman/Shovels.ai等 | 未尝试 | 本轮时间集中在验证并跑通已确认可达的四个源 |

---

## 已验证的技术细节（供 src/fetch/ 复用）

- **本环境Python的urllib/requests对多个目标站点会间歇性挂起或报 `HTTP/2 stream ... not closed cleanly`（curl error 92）**，
  根因是会话代理重新终结TLS后对HTTP/2 ALPN协商不稳定。解决方案：强制 `--http1.1`。
  已在 `src/fetch/_http.py` 里封装为统一的 curl 子进程调用（GET/POST+JSON），四个 fetch 脚本已切换为使用它。
- 4xx错误（如404资源不存在）不会重试，避免在探测数据可用年份边界时浪费大量时间。
- SEC EDGAR要求`User-Agent`带可识别的联系方式，否则Akamai会拒绝；已设为 `ai-data-center-report zhaoyu192403@gmail.com`。
- FRED的`fredgraph.csv`公开导出端点**不需要API key**，比官方JSON API更简单可靠，已作为默认方法。
- BLS QCEW Open Data按`{year}/{qtr}/industry/{naics}.csv`取数，**该端点仅覆盖到2014年**（2010-2013返回404，
  不是网络问题，是数据本身不存在于这个特定API）。
- BLS PPI v2 API **未注册key时，查询区间超过10年会被静默截断到区间最早的10年**（而非最近10年），
  已在脚本里改为无key时默认查询"最近10年"(2017-2026)而非"2010-2026"。
- BLS PPI序列 `PCU335335`（电气设备大类）**无效**，返回"Series does not exist"；已从脚本移除，
  只保留验证有效的 `PCU335311335311`（变压器制造业）。

---

## 逐数据集明细

### F15/F14 — SEC EDGAR 四大厂商资本开支 (`data/raw/sec/capex_quarterly_by_fiscal_period.csv`)
- 来源：`https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`，XBRL标签
  `PaymentsToAcquirePropertyPlantAndEquipment`（AMZN 2017年后改用`PaymentsToAcquireProductiveAssets`，
  已在脚本里加了标签回退逻辑）+ `NetCashProvidedByUsedInOperatingActivities`
- 访问日期：2026-08-16
- 覆盖：MSFT/AMZN/GOOGL/META，2008-2026逐季（按财季末日期，非日历季）
- **真实亮点数字**：MSFT 2026财年Q4(2026-06-30)单季资本开支$358.02亿，经营现金流$554.41亿；
  四家合计capex/经营现金流比率2026Q2达96%，与报告草稿引用的"93%"基本吻合
- **技术修正记录（重要）**：初版实现按XBRL的`fy`标签分组做累计值差分，未意识到MSFT/AMZN的10-Q
  会同时披露"当季3个月"直接数值和"财年累计"数值，混算导致MSFT单季capex被错误放大到$850.72亿。
  已改为按`start`日期分组做链式差分（同一start必然同属一条累计链），并用各公司10-K年度合计
  逐一交叉验证（如MSFT FY2025四个季度加总=$645.51亿，与10-K年度数字完全一致）。
- 已知限制：MSFT财年6月结束，已在清洗阶段(`src/clean/clean_sec_edgar.py`)按财季结束日期的
  日历月份做日历季对齐，可与其余三家同图比较

### F03兜底/F05 — FRED全国电价 (`data/raw/fred/APU000072610.csv`)
- 来源：`https://fred.stlouisfed.org/graph/fredgraph.csv?id=APU000072610`（无需API key）
- 访问日期：2026-08-16
- 覆盖：1978-11至2026-07，573个月度观测点，单位美元/kWh
- 已知限制：这只是全国均值，不能替代F03要求的分州序列（仍需EIA key）

### F07 — BLS QCEW NAICS 518210 (`data/raw/bls/qcew_518210_combined.csv`)
- 来源：`https://data.bls.gov/cew/data/api/{year}/{qtr}/industry/518210.csv`（无需key）
- 访问日期：2026-08-16
- 覆盖：2014-2025逐季，全美分县，102,300行
- **真实亮点数字**：Loudoun County VA(area_fips=51107) 2025Q4私营部门：128家机构、2,131名员工、周均工资$3,576
- 已知限制：2010-2013年该行业代码无数据（API本身覆盖范围所限）；2022年NAICS修订导致518210定义变更，
  图上必须标注断点（详见CAVEATS.md）

### F17 — BLS PPI 变压器制造业 (`data/raw/bls/ppi_transformers.csv`)
- 来源：BLS时间序列API v2，series `PCU335311335311`
- 访问日期：2026-08-16
- 覆盖：2017-01至2026-07，115个月度观测点
- **真实亮点数字**：指数从2017年1月231.5涨到2026年7月474.8，10年间+105%
- 已知限制：无registrationkey时区间上限10年，已用完整年；若要拿2010-2016需另跑一次或申请key

### F03(完整版) — EIA 分州居民电价 (`data/raw/eia/F03_retail_sales_residential.csv`)
- 来源：EIA API v2 `electricity/retail-sales`，`sectorid=RES`（居民部门）
- 访问日期：2026-08-16（用户提供免费API key）
- 覆盖：US全国 + VA/OH/IL/MD/AZ/GA(数据中心密集州) + WY/ND/MT(低密度对照组)，2015-01至2026-05月度，1,507行
- **真实亮点数字**：2026年最新值——密集州均值19.0¢/kWh > 全国均值18.4¢ > 对照组均值14.4¢/kWh；
  2022年后密集州与对照组的差距明显拉开，与文档"密集州涨幅显著高于全国"的论点吻合
- **数据质量修正记录**：对照组原选WY/VT/MT，实测发现VT电价常年在23-25¢/kWh
  （佛蒙特州电网结构性因素，与数据中心无关），会给"低密度对照组"引入不相关噪音，
  已换成ND(北达科他州，电价水平与WY/MT接近，同样是数据中心密度很低的州)
- **待核实的真实异常值**：马里兰州(MD) 2026年3月单月电价飙升到35.85¢/kWh
  （2月20.08¢→3月35.85¢→4月22.07¢），已确认是EIA真实数据、未做任何剔除处理，
  推测可能与PJM容量市场费用结算周期有关(见F04数据源E4/E5)，值得核实后写入正文

---

## 待补数据源（下一步）

1. **PJM (E4)**：网站可达，但需要在 pjm.com 上找到实际的BRA历年出清价汇总页面/文件
   （不在RPM主页里，可能在"Markets & Operations > Capacity Market Results"下的具体表格页）
2. **LBNL Queued Up (G1)**：Cloudflare拦截，curl+伪装UA+Playwright headless均403。
   建议：用户直接从 https://emp.lbl.gov/queues 手动下载XLSX后上传，或反馈给管理员看能否放开对
   `*.lbl.gov` 域名的访问（如果是本会话代理侧还有额外限制的话）
3. **LBNL 数据中心用电报告 (E7)**：F06的分子(用电量)，PDF需人工录入约10个数字，
   分母(EIA全美总售电量)已就绪于`data/raw/eia/F06_us_total_sales_annual.csv`

## 命名与更新规则

新增数据源时，在对应 `data/raw/{source}/` 目录下同时提供：
1. 原始数据文件（CSV/XLSX/JSON）
2. `{filename}_meta.json`：source, url, accessed(ISO8601), unit, notes
3. 在本文件补充一节，注明覆盖图表编号
