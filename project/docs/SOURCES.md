# SOURCES.md — 数据出处记录

本文件记录本项目已获取的每一批数据的来源、访问方式、访问日期与已知限制。
按文档 v1 §5.1 要求：每个 CSV 应附带来源 URL、访问日期、口径说明、已知限制。

---

## 状态总览（2026-08-16）

本项目在一个网络出站受限的沙盒环境中执行：直接 API/HTTP 访问
（`api.eia.gov`、`fred.stlouisfed.org`、`data.sec.gov`、`api.bls.gov`、`emp.lbl.gov`
等域名，以及通用网页抓取工具 WebFetch）被代理策略拦截（403 policy denial）。
唯一可用的外部信息获取渠道是 **WebSearch**（返回搜索摘要及来源链接，不返回原始
结构化数据/完整页面）。因此：

| 类别 | 状态 | 说明 |
|---|---|---|
| `src/fetch/*.py` 四个脚本 | **已写好，未跑通** | 代码通过语法检查(`py_compile`)，逻辑指向正确的公开免费API；需在无网络限制的环境中执行 |
| `data/raw/manual/websearch_facts_2026-08-16.csv` | **已采集，二手转述** | 通过WebSearch获得的具体数字，每条都标注来源URL、访问日期、数据级别(B/C)；**均为搜索摘要转述，非原始API/PDF/官网表格**，只能作为交叉验证锚点，不能直接当作图表主曲线的原始数据源 |
| CBRE/Cushman历史各期、LBNL Queued Up原始XLSX、PJM历史BRA PDF、Shovels.ai、Pew原始topline | **未获取** | 需要真实网络访问、注册或付费；详见 `docs/DATA_GAPS.md` |

---

## 已写好但未执行的 fetch 脚本

| 脚本 | 数据源ID | 覆盖图表 | 状态 |
|---|---|---|---|
| `src/fetch/fetch_eia.py` | E1, E3 | F03, F06 | 需 `EIA_API_KEY`，本环境网络被拦截 |
| `src/fetch/fetch_fred.py` | E2 | F03(兜底), F05 | 需 `FRED_API_KEY`，本环境网络被拦截 |
| `src/fetch/fetch_sec_edgar.py` | C1 | F14, F15 | 无需key，本环境网络被拦截 |
| `src/fetch/fetch_bls.py` | J1(QCEW), C3(PPI) | F07, F17 | QCEW无需key；PPI建议申请key；本环境网络被拦截 |

详细运行方法见 `src/fetch/README.md`。这些脚本本身是本次任务的实际产出，
在有网络权限的环境（例如本地 Claude Code CLI）中可直接运行产出真实数据。

---

## WebSearch 采集的锚点数字

完整表格见 `data/raw/manual/websearch_facts_2026-08-16.csv`，每行含
`figure_id, metric, value, unit, period, source_name, source_url, accessed_date, data_level, caveat`。

摘要（访问日期均为 2026-08-16）：

### F02 — AI使用率 vs 反对率四线分离
- Pew: AI chatbot使用率 23%(2023) / 33%(2024夏) / 49%(2026早)
  来源: https://www.pewresearch.org/internet/2026/06/17/americans-and-ai-2026-chatbots-smart-devices-and-views-on-impact/
  **与规划文档草稿引用数字一致**，但仍是WebSearch摘要转述，正式成图前建议下载Pew原始topline核对样本量/问法。
- Pew: ChatGPT专项使用率 18%(2023) → 34%(2025)
  来源: https://www.pewresearch.org/short-reads/2025/06/25/34-of-us-adults-have-used-chatgpt-about-double-the-share-in-2023/

### F09 — 并网队列时长（全报告定盘星）
- LBNL Queued Up 2025版（经二手转述）：并网中位时长 22个月(2008) → 36个月(2015) → 61个月(2025)，17年间+177%
  来源: https://www.publicpower.org/periodical/article/backlog-power-plants-seeking-transmission-grid-connection-eased-somewhat-2025-lbnl
  **注意**：文档草稿引用的是"84个月"，此处转述数字为"61个月"，两者很可能统计的是不同环节
  （申请→商运 vs 申请→签署并网协议），**必须拿到LBNL原始报告核实具体口径后才能定稿**，
  不可把两个数字混用在同一张图上。
- 队列总容量2025年末超2,060GW；2000-2020年cohort完成率13%/撤回75%/仍活跃10%（三者相加98%，
  有约2个百分点缺口，需核对原始报告）；2025年撤回容量750GW+
  来源: https://www.latitudemedia.com/news/the-us-interconnection-queue-is-twice-its-installed-capacity/ ，
  https://www.publicpower.org/periodical/article/backlog-power-plants-seeking-transmission-grid-connection-eased-somewhat-2025-lbnl
- **这三个年份点(2008/2015/2025)远不构成文档要求的"2000-2025年度完整序列"**，只能作为兜底散点，
  不能画出完整折线。原始序列必须去 https://emp.lbl.gov/queues 下载XLSX。

### F12 — 州级立法
- 2026年前六周300+法案提案，覆盖30+州（与文档已引用数字一致）
- 38州现有税收优惠，28州2026年提案削减/修改，9州考虑彻底撤回
- 已成法个案：俄克拉荷马HB2992（2026-05-11，消费者电价保护法）；亚利桑那3年销售税豁免暂停
  来源: multistate.us 系列文章（见CSV明细）

### F14/F15 — 资本开支 vs 受阻金额
- 四大厂商2026资本开支指引合计约$725B，较2025年$410B增77%；Amazon~$220B、Alphabet$195-205B、
  Meta$130-145B、Microsoft~$190B（均为公司指引区间，非SEC实际值，需用C1原始XBRL数据校验）
  来源: https://finance.yahoo.com/sectors/technology/articles/google-microsoft-meta-amazon-capex-131823436.html
- Data Center Watch: 2026Q1受阻/延迟75个项目、约$130B（与2025全年持平）；活跃反对组织396(2025末)→833(2026-03)；
  2026年3月末-6月受阻$98B，2023-2025年3月末累计$64B
  来源: https://www.nbcnews.com/tech/tech-news/data-center-opposition-sharply-rising-2026-study-finds-rcna349728
  （C级，私人追踪口径，缺少分母，图注必须声明）

### F18 — 已宣布 vs 在建缺口
- Sightline Climate: 2026年计划16GW/约140个项目，仅约5GW在建（动工率约31%），预计30%-50%延期
  来源: https://www.sightlineclimate.com/research/data-center-outlook
  （C级，仅为单点截面，非文档要求的分年序列）

### F19 — 供给紧张度
- CBRE(2026)：北美主要市场空置率1.6%、在建预租率74.3%、库存同比+43%、
  前四大市场2026Q1净吸纳量2,236.2MW、北弗吉尼亚空置率0.3%、亚特兰大1%
  来源: https://www.cbre.com/insights/books/north-america-data-center-trends-h2-2025
  （单期数字，**不能画趋势线**，必须拿2016年以来各期历史报告）

### F03 — 电价
- 弗州数据中心用电占比40%(2026) vs <5%(2010)；弗州居民电价"低于全国均值~18¢/kWh"（定性表述）
  来源: https://introl.com/blog/virginia-sb-253-data-center-electricity-rate-shift-2026
  （未核实原始出处的二手转述，**不可直接用作F03主曲线**，必须用E1/EIA API拿精确月度数字替换）

---

## 名义值 vs 实际值

本批WebSearch采集的所有金额（$130B、$725B等）均为名义值（当年美元），
未做CPI平减。正式成图前需按文档§5.1要求补充实际值序列。

## 命名与更新规则

新增数据源时，在对应 `data/raw/{source}/` 目录下同时提供：
1. 原始数据文件（CSV/XLSX/JSON）
2. `{filename}_meta.json`：source, url, accessed(ISO8601), unit, notes
3. 在本文件补充一节，注明覆盖图表编号
