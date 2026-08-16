# 数据规划执行 — 项目骨架

对应《全民反对，美国 AI 基建的"逆风"？》数据规划与配图规格 v1（20幅核心图 + 4幅备选图）。

## 现状速览（2026-08-16）

本次执行的沙盒环境出站网络受限（EIA/FRED/BLS/SEC EDGAR/LBNL等域名及WebFetch均被
代理策略拦截，只有WebSearch可用）。因此本次交付的是：

1. **完整目录骨架**（`data/`, `src/`, `figures/`, `docs/`, `config/`），按文档§3规范建好
2. **`config/sources.yaml`**：文档§1全部数据源(E/G/M/C/J/W/P/O系列)的URL、级别、获取方式
3. **`src/fetch/` 四个可运行脚本**（fetch_eia.py / fetch_fred.py / fetch_sec_edgar.py / fetch_bls.py），
   对应文档"阶段一"T1-T5，逻辑已写好、语法已验证，只需在有网络权限的环境中执行即可产出真实数据
4. **`data/raw/manual/websearch_facts_2026-08-16.csv`**：通过WebSearch获取的约35条真实、带来源的
   锚点数字（Pew AI使用率、LBNL并网时长、四大厂商资本开支指引、州级立法、CBRE空置率等），
   每条都标注来源URL/访问日期/数据级别，明确标注为"二手转述"
5. **`docs/SOURCES.md`** / **`docs/CAVEATS.md`** / **`docs/DATA_GAPS.md`**：出处记录、口径限制、
   逐图数据缺口报告（哪些图能画、哪些不能、为什么、对论点的影响）

**没有产出**：`figures/` 下的实际PNG/SVG图表。原因见 `docs/DATA_GAPS.md`——当前能拿到的
真实数据只是零散锚点，不构成文档要求的完整时间序列，用这些零星数字画出"看起来完整"的
20幅图等于伪造密度，违反文档§5的质量校验规则。

## 下一步

在有出站网络权限的环境中（本地 Claude Code CLI，或向本会话提供 API key / 已下载的数据文件）：

```bash
cd src/fetch
export EIA_API_KEY=... FRED_API_KEY=... BLS_API_KEY=... SEC_USER_AGENT="..."
python fetch_eia.py --series retail-sales
python fetch_eia.py --series power-annual
python fetch_fred.py
python fetch_sec_edgar.py
python fetch_bls.py --dataset qcew --start-year 2010 --end-year 2026
python fetch_bls.py --dataset ppi
```

跑完后在 `src/clean/` 补清洗脚本、`src/plot/` 补画图脚本，逐图产出
`data/processed/F*.csv` 和 `figures/{png,svg}/F*.{png,svg}`。

详见 `docs/DATA_GAPS.md` 里"按严重程度排序的核心缺口"，建议按该顺序补数据。
