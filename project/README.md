# 数据规划执行 — 项目骨架

对应《全民反对，美国 AI 基建的"逆风"？》数据规划与配图规格 v1（20幅核心图 + 4幅备选图）。

## 现状速览（2026-08-16，第三轮更新）

阶段一(T1-T5)四个免费公开数据源——**EIA / FRED / SEC EDGAR / BLS(QCEW+PPI) 全部已跑通**，
拉取到真实、完整、可复核的数据，并已清洗+画出5幅正式图表(300dpi PNG + SVG)：

| 图 | 数据源 | 规模 | 亮点 |
|---|---|---|---|
| F03 电价 | EIA(分州) + FRED(全国) | 10州×2015-2026月度，1,507行 | 密集州19.0¢ vs 对照组14.4¢/kWh，2022年后差距拉开 |
| F07 就业结构 | BLS QCEW | NAICS 518210分县，2014-2025逐季，102,300行 | Loudoun County VA(2,131) < Franklin County OH(4,066)——投资额与本地岗位不成比例的实证 |
| F15 资本开支 | SEC EDGAR | 4家公司2015Q1-2026Q2逐季，172行 | capex/经营现金流比率2026Q2达96% |
| F17 设备价格 | BLS PPI | 变压器制造业指数2017-2026月度，115点 | 10年+105%，上涨主要发生在2021年后 |

`figures/png/` 和 `figures/svg/` 下已有对应4个正式图表文件。

仍未解决的：**PJM**（网站可访问，未定位到历年BRA数据文件）、**LBNL emp.lbl.gov**
（被Cloudflare机器人防护拦截，与出站网络策略无关，curl/Playwright headless浏览器+
伪装UA均403，**这是当前全报告最大的单一缺口**，F09"并网时长"定盘星图卡在这里）。
详见 `docs/DATA_GAPS.md`。

## 目录说明

1. **`config/sources.yaml`**：文档§1全部数据源(E/G/M/C/J/W/P/O系列)的URL、级别、获取方式
2. **`src/fetch/`**：四个fetch脚本(EIA/FRED/SEC EDGAR/BLS)，统一通过`_http.py`用curl子进程
   发请求(`--http1.1`绕开本环境代理下Python urllib/requests的HTTP/2间歇性挂起问题)
3. **`src/clean/`**：四个清洗脚本，把raw数据整理成`data/processed/F*.csv`
4. **`src/plot/`**：四个画图脚本+共享样式模块`_style.py`(配色取自dataviz skill验证过的色板)
5. **`data/raw/`** → **`data/processed/`** → **`figures/{png,svg}/`**：完整数据管线
6. **`docs/SOURCES.md`** / **`docs/CAVEATS.md`** / **`docs/DATA_GAPS.md`**：出处记录、口径限制、
   逐图数据缺口报告（四轮迭代对比）

## 过程中修的两个真实bug（留痕，供复核）

1. **SEC EDGAR季度值计算错误**：MSFT/AMZN的10-Q会同时披露"当季3个月"直接数值和"财年累计"
   数值，混算导致MSFT单季资本开支一度被算成$850.72亿(真实值$358.02亿)。已修复并用各公司
   10-K年度合计逐一交叉验证。详见`src/fetch/fetch_sec_edgar.py`里的`quarterize()`函数注释。
2. **F03对照组选州不当**：低密度对照组原选WY/VT/MT，VT电价常年结构性偏高(~23-25¢/kWh，
   与该州电网结构有关，与数据中心无关)，已换成ND。

## 下一步

优先级见 `docs/DATA_GAPS.md`「按severity排序的下一步优先级」，简版：

1. **人工提供LBNL Queued Up数据文件**（emp.lbl.gov被Cloudflare拦截）→ 解决F09/F10，
   当前最高优先级
2. 深入PJM网站定位历年BRA出清价数据 → 补齐F04，顺带核实F03里马里兰州2026年3月的电价异常尖峰
3. LBNL数据中心用电报告(PDF，约10个数字需人工录入) → 补齐F06分子(分母已就绪)
4. 继续往下走阶段三/四(CBRE/Cushman/NCSL等需注册的商业数据源)
