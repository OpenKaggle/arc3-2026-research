# ARC3 24h 基线回执对账（2026-10-15 晚，主工作流）

- 作者：主工作流会话（worker c1c38a39 / MacBook-Pro-7.local）。写入时间：2026-10-15T11:42:39Z。
- 类型：附加对账备忘；不修改、不覆盖任何既有回执字节；全部原件保留。
- 范围：①rev2 三副本厘清与 canonical 采用；②r1_quickcheck 辅助证据定性；③lf52 事故闭案事项处置；④R1 重跑守卫升级与快照。

## 1. Rev2 副本图（receipts/24h_baseline/，R1 前失败运行）

| 文件 | sha256 | 状态 |
|---|---|---|
| baseline_24h_result.json（rev1, as-written） | 387bd8ed… | 保留为记录；当前状态由 rev2 表述（不覆盖） |
| baseline_24h_result_rev2.json | cade093c… | **canonical rev2**（本工作流 10:45:40Z 写入） |
| …_rev2_20261015T104540Z.json | cade093c… | canonical 的逐字节副本 |
| …_rev2_20261015T103353Z.json | 660f014d… | 修复线程草稿（10:33:53Z），保留为历史 |
| gate_fold_2026-10-15.json | 85be4cc7… | 闸门折叠（判决不变） |

差异（canonical vs 660f014d 草稿，F）：
- lf52/baseline 标签：canonical `done→capped` + label_note（与后编辑 runner 字节一致；内容字段不变）；草稿保留 `done`。
- canonical 含 `revision{}` 块（60 行折叠来源、last-row-per-(policy,game) 规则、源 sha efe67622、folded_rows=60）与 `budget.total_steps_all_policies=2393000`；草稿仅 `revision: 2`。
- runner_sha256：canonical 记 `060e87ad…`（运行时 as-written；谱系注：resume 时磁盘字节为 `45680aad…`）；草稿记 `45680aad…`。
- 全部变体闸门判决一致：baseline 3 关 vs best anchor 8 关 → FAILED（R1 前结论；操作态为 R1 重跑）。

采用决定：**canonical = cade093c**（修正超集；标签与实况对齐）。rev2 无需再改；R1 折叠只写 `receipts/24h_baseline_r1/`。

## 2. r1_quickcheck_2026-10-15/（非闸门辅助证据）

- 内容：lp85、sp80 各 2 pass × 2500 步（quick_mode）；结果 json sha `22d8843a…`（10:44:14Z）。
- 结果（F）：同游戏两 pass 链头逐位一致；0 非法 / 0 崩溃 / 0 关（2500 步上限内）；总墙 46.6s。
- 定性：R1 坐标修复的机制冒烟（点击主导的验证集游戏），**非闸门声明**、不进入折叠；官方 R1 证据仅 `receipts/24h_baseline_r1/`。

## 3. lf52 事故闭案事项处置

来源：`receipts/24h_baseline/incident_lf52_indexerror_2026-10-15_closure.json`（sha `f2f980bc…`；保活机修复线程）。
- 「archive-sentinel 子串假通过」补丁：**作废**。d7e900fd 已于 10-15 晚重排为双有效态守卫（不再含旧子串条件）；已核对现行 AUDIT_STATE（stage=24H_BASELINE_R1_RERUN_IN_PROGRESS）下静默。
- 「重跑遮蔽风险」：按设计规避——R1 输出隔离于 `receipts/24h_baseline_r1/`；保活机 fdc77cc5 与折叠唤醒机 c156da48 只读该目录；旧目录 complete 回执不参与 R1 谓词。
- 「sleep/墙钟语义」：系统级 `caffeinate -ims`（pid 63385，约 03:53 CST 起）+ 新增 R1 绑定 `caffeinate -ims -w 4562`（pid 55891，19:41 CST）；主机 AC 供电。未来 harness 设计项：CPU-time 预算守卫（已记录，未实施）。
- 「rev2 采用决策」：见 §1。

## 4. R1 重跑快照（截至撰写）

- pid 4562，10:49:36Z 启动；10 baseline 行；baseline levels=1（r11l，较修复前 0 为新增）；0 非法 / 0 崩溃；lf52 进行中（chain 持续增长，>2.09MB）。
- 保活机 fdc77cc5 本小时升级：陈旧判定改用 progress.jsonl / chain_*.txt / run.log 之最新 mtime（长单局不误报）；实机模拟 exit 0。
- 完成后一键折叠：`cd arc3_2026 && starter/.venv/bin/python starter/scripts/fold_24h_receipt.py --dir receipts/24h_baseline_r1 --label r1`。

## 5. 本备忘冻结输入哈希

rev1 `387bd8ed…`；rev2 canonical `cade093c…`；rev2 草稿 `660f014d…`；gate_fold `85be4cc7…`；progress `efe67622…`；incident `dccbea6e…`；closure `f2f980bc…`；seal 草案 `5b2d2179…`（历史保留）；R1 决策 `58af1eab…`；static `2e536dc4…`；replay `ac66d079…`；fix-verify `4eb70b71…`；diff `0723cdfe…`；baseline_v2 `f6a2bbb2…`；runner `f4c574ed…`；折叠工具 `9b042afd…`；诊断备忘 `86598408…`。
