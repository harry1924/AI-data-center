# fetch 脚本使用说明

这四个脚本对应文档"阶段一：可 API 直取"(T1-T5)，全部指向免费公开 API，
逻辑已写好并通过 `python3 -m py_compile` 语法检查，但**尚未在真实网络环境中跑通**——
执行本任务的沙盒对 `api.eia.gov` / `fred.stlouisfed.org` / `data.sec.gov` / `api.bls.gov`
的出站请求被代理策略拦截（403 policy denial，2026-08-16 实测）。请在有出站网络权限的机器
（例如本地终端跑的 Claude Code CLI，或任何普通开发机）上执行。

## 运行前准备

```bash
export EIA_API_KEY=xxx     # https://www.eia.gov/opendata/register.php
export FRED_API_KEY=xxx    # https://fred.stlouisfed.org/docs/api/api_key.html
export BLS_API_KEY=xxx     # https://data.bls.gov/registrationEngine/ (QCEW不需要，PPI建议申请)
export SEC_USER_AGENT="你的机构名 联系邮箱"   # SEC要求，见 fetch_sec_edgar.py
```

## 运行

```bash
python fetch_eia.py --series retail-sales   # F03 分州电价
python fetch_eia.py --series power-annual   # F06 分母
python fetch_fred.py                        # F03兜底 / F05 全国电价
python fetch_sec_edgar.py                   # F14/F15 四大厂商资本开支
python fetch_bls.py --dataset qcew --start-year 2010 --end-year 2026   # F07
python fetch_bls.py --dataset ppi                                       # F17
```

## 跑完之后

1. 检查 `data/raw/{eia,fred,sec,bls}/` 下是否生成了 CSV 与对应 `_meta.json`
2. 核对 `fetch_bls.py` 里 `PPI_SERIES` 的 series id 是否与 BLS PPI 数据库当前口径一致
   （BLS 偶尔调整行业分类代码，脚本里标注的是撰写时的最佳猜测，未经实际请求验证）
3. 跑 `src/clean/` 下对应的清洗脚本，产出 `data/processed/F*.csv`
4. 把 `_meta.json` 里的 URL、访问日期汇总进 `docs/SOURCES.md`
