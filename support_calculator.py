import pandas as pd
import pulp as pl

# ---------------- 定数 ----------------
BASE_BONUS = {"4": 12.5, "BD": 10.0}
WL_BONUS   = 20.0
MR_BONUS   = {"4": [0, 0.5, 1.0, 1.5, 2.0, 2.5],
              "BD": [0, 0.4, 0.8, 1.2, 1.6, 2.0]}
SKL_BONUS  = {"4" : [0, 0, 0.25, 1.0, 2.5],
              "BD": [0, 0, 0.20, 0.8, 2.0]}
MR_COST  = {"4": [0, 2000, 4000, 6000, 8000, 10000],
            "BD": [0, 1000, 2000, 3000, 4000, 5000]}
SKL_COST = {"4": [0, 0, 1000, 4000, 10000],
            "BD": [0, 0,  500, 2000,  5000]}
MED_SK, LGE_SK = 50, 250

# ---------------- データ読込 ----------------
cards = pd.read_csv("card_list.csv")          # name, rare, mas, skill, wl
items = pd.read_csv("item_list.csv")          # item, amount

item_dict = dict(zip(items["item"], items["amount"]))
shard   = int(item_dict["想いのカケラ"])
crystal = int(item_dict["想いの純結晶"])
med     = int(item_dict["スキルスコア中級"])
lge     = int(item_dict["スキルスコア上級"])

SHARDS_LIMIT = shard + 2000 * crystal
SCORE_LIMIT  = med*MED_SK + lge*LGE_SK

# ---------------- 候補列挙 ----------------
cand = []
for idx, r in cards.iterrows():
    rare, m0, s0 = r.rare, r.mas, r.skill
    for m in range(m0, 6):
        for s in range(s0, 5):               # 1〜4
            cand.append(dict(
                cid       = idx,
                name      = r["name"],
                wl        = bool(r.wl),
                mas_tgt   = m,
                skl_tgt   = s,
                value     =  (BASE_BONUS[rare]
                              + (WL_BONUS if r.wl else 0)
                              + MR_BONUS[rare][m]
                              + SKL_BONUS[rare][s]),
                cost_mr   = MR_COST[rare][m]  - MR_COST[rare][m0],
                cost_skl  = SKL_COST[rare][s] - SKL_COST[rare][s0])
            )
cand = pd.DataFrame(cand)

# ---------------- MILP ----------------
prob = pl.LpProblem("WL_support_opt", pl.LpMaximize)
x = {i: pl.LpVariable(f"x{i}", 0, 1, cat="Binary") for i in cand.index}

prob += pl.lpSum(cand.value[i] * x[i] for i in cand.index)          # 目的
prob += pl.lpSum(x[i] for i in cand.index) == 20                    # 20枚
for cid, g in cand.groupby("cid"):                                  # 1カード1案
    prob += pl.lpSum(x[i] for i in g.index) <= 1

# カケラとスキルスコアの上限
prob += pl.lpSum(cand.cost_mr[i] * x[i] for i in cand.index) <= SHARDS_LIMIT  # MR カケラ上限
prob += pl.lpSum(cand.cost_skl[i] * x[i] for i in cand.index) <= SCORE_LIMIT  # スキルスコア上限（ここだけで払う）

# 解く
prob.solve(pl.PULP_CBC_CMD(msg=False))
assert pl.LpStatus[prob.status] == "Optimal"

# 最適解を出力
sel = cand[[pl.value(x[i]) > .5 for i in cand.index]]
sel.to_csv("best_plan.csv", index=False, encoding="utf-8-sig")

print(f"★ 最終倍率 : {prob.objective.value():.2f} %")
print(f"★ カケラ    : {sel.cost_mr.sum() + max(0, sel.cost_skl.sum()-SCORE_LIMIT)} / {SHARDS_LIMIT}")
print(f"★ スコア    : {min(sel.cost_skl.sum(), SCORE_LIMIT)} / {SCORE_LIMIT}")
