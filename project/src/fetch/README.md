# fetch 脚本使用说明

四个脚本对应文档"阶段一：可API直取"(T1-T5)。2026-08-16第二轮测试：
FRED / SEC EDGAR / BLS(QCEW+PPI) 已在本环境实际跑通，产出真实数据（见 `data/raw/`）。
EIA 网络已通但需要免费 API key（未获取到）。

## 技术说明：为什么用 curl 子进程而不是 requests/urllib

本环境的 Python urllib/requests 对多个目标站点会间歇性挂起或报
`HTTP/2 stream ... was not closed cleanly`（curl error 92）。根因是会话出站代理
重新终结TLS后，对下游的HTTP/2 ALPN协商不稳定。强制curl用`--http1.1`后100%稳定
（亚秒级返回）。因此四个脚本统一改为通过 `_http.py` 用 curl 子进程发请求。
在没有这层代理的普通环境里，这个实现同样能正常工作。

## 运行前准备

```bash
export EIA_API_KEY=xxx     # https://www.eia.gov/opendata/register.php （必需，其余三个不需要key）
export SEC_USER_AGENT="你的机构名 联系邮箱"   # 已有默认值，SEC要求格式见fetch_sec_edgar.py
export BLS_API_KEY=xxx     # 可选，不设置时PPI自动改为查询最近10年而非2010-2026
```

## 运行

```bash
python fetch_fred.py                                                    # ✅已验证 F03兜底/F05
python fetch_sec_edgar.py                                               # ✅已验证 F14/F15
python fetch_bls.py --dataset qcew --start-year 2014 --end-year 2026    # ✅已验证 F07 (2014年前该API无数据)
python fetch_bls.py --dataset ppi                                       # ✅已验证 F17
python fetch_eia.py --series retail-sales   # F03 分州电价，需EIA_API_KEY
python fetch_eia.py --series power-annual   # F06 分母，需EIA_API_KEY
```

## 已知细节

- BLS QCEW的`{year}/{qtr}/industry/518210.csv`端点**只覆盖到2014年**，更早年份返回404
  （已在`_http.py`里改为4xx不重试，避免浪费时间探测边界）
- BLS PPI v2 API 未注册key时单次查询最多10年，且会返回**区间最早的10年**而非最近10年，
  已在脚本里改为无key时默认查最近10年
- PPI序列`PCU335335`（电气设备大类）经验证无效，已从`PPI_SERIES`移除，只保留
  `PCU335311335311`（变压器制造业，已验证有效）
- SEC companyfacts原始JSON体积较大(3-5MB/家)，已加入`.gitignore`不提交，只提交提取后的CSV

## 跑完之后

1. 检查 `data/raw/{eia,fred,sec,bls}/` 下是否生成了 CSV 与对应 `_meta.json`
2. 跑 `src/clean/` 下对应的清洗脚本（尚未编写），产出 `data/processed/F*.csv`
3. 把 `_meta.json` 里的 URL、访问日期汇总进 `docs/SOURCES.md`
