#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WorldLink サポートユニット最適化計算ツール

このプログラムは、WorldLinkのサポートユニットを最適化するためのMILP（混合整数線形計画法）ソルバーです。
所持するカードとアイテムから、最も効率的な強化プランを算出します。
"""

import pandas as pd
import pulp as pl

# ---------------- 定数設定 ----------------
# 基本ボーナス値（カードレア度別）
BASE_BONUS = {"4": 12.5, "BD": 10.0}

# WorldLink限定カードの追加ボーナス
WL_BONUS = 20.0

# マスターランクによるボーナス（レア度別、インデックスはマスターランクに対応）
MR_BONUS = {
    "4": [0, 0.5, 1.0, 1.5, 2.0, 2.5],     # ☆４
    "BD": [0, 0.4, 0.8, 1.2, 1.6, 2.0]      # バースデー
}

# スキルレベルによるボーナス（レア度別、インデックスはスキルレベルに対応）
SKL_BONUS = {
    "4": [0, 0, 0.25, 1.0, 2.5],           # ☆４（レベル1から1スタート、位置1がレベル2）
    "BD": [0, 0, 0.20, 0.8, 2.0]            # バースデー
}

# マスターランク強化に必要なカケラコスト（レア度別、インデックスはマスターランクに対応）
MR_COST = {
    "4": [0, 2000, 4000, 6000, 8000, 10000],  # ☆４
    "BD": [0, 1000, 2000, 3000, 4000, 5000]    # バースデー
}

# スキルレベル強化に必要なカケラコスト（レア度別、インデックスはスキルレベルに対応）
SKL_COST = {
    "4": [0, 0, 1000, 4000, 10000],           # ☆４
    "BD": [0, 0, 500, 2000, 5000]              # バースデー
}

# スキルスコアのカケラ換算値
MED_SK = 50   # スキルスコア中級1個 = カケラ50個分
LGE_SK = 250  # スキルスコア上級1個 = カケラ250個分


def load_data():
    """
    カードとアイテムのデータを読み込む関数
    
    Returns:
        tuple: (cards_df, shards_limit, score_limit) - カード情報のデータフレーム、カケラ上限、スキルスコア上限
    """
    # カード情報の読み込み
    cards = pd.read_csv("card_list.csv")  # name, rare, mas, skill, wl
    
    # アイテム情報の読み込み
    items = pd.read_csv("item_list.csv")  # item, amount
    
    # アイテム情報を辞書形式に変換
    item_dict = dict(zip(items["item"], items["amount"]))
    
    # 各アイテムの数を取得
    shard = int(item_dict["想いのカケラ"])
    crystal = int(item_dict["想いの純結晶"])
    med = int(item_dict["スキルスコア中級"])
    lge = int(item_dict["スキルスコア上級"])
    
    # カケラとスキルスコアの上限を計算
    shards_limit = shard + 2000 * crystal
    score_limit = med * MED_SK + lge * LGE_SK
    
    return cards, shards_limit, score_limit

def generate_candidates(cards_df):
    """
    カードの強化候補を生成する関数
    
    Args:
        cards_df (pd.DataFrame): カード情報のデータフレーム
    
    Returns:
        pd.DataFrame: 強化候補のデータフレーム
    """
    candidates = []
    
    # 各カードについて強化候補を生成
    for idx, card in cards_df.iterrows():
        # 現在の状態を取得
        rare = card.rare
        current_mas = card.mas
        current_skill = card.skill
        is_wl = bool(card.wl)
        
        # 可能な全ての強化パターンを生成
        for target_mas in range(current_mas, 6):
            for target_skill in range(current_skill, 5):  # スキルレベルは1〜4
                # 強化候補を生成
                candidates.append({
                    'cid': idx,                      # カードID
                    'name': card["name"],            # カード名
                    'wl': is_wl,                    # WL限定フラグ
                    'mas_tgt': target_mas,           # 強化後のマスターランク
                    'skl_tgt': target_skill,         # 強化後のスキルレベル
                    # 強化後の倍率
                    'value': (BASE_BONUS[rare] 
                              + (WL_BONUS if is_wl else 0)
                              + MR_BONUS[rare][target_mas]
                              + SKL_BONUS[rare][target_skill]),
                    # マスターランク強化に必要なカケラ
                    'cost_mr': MR_COST[rare][target_mas] - MR_COST[rare][current_mas],
                    # スキルレベル強化に必要なカケラ
                    'cost_skl': SKL_COST[rare][target_skill] - SKL_COST[rare][current_skill]
                })
    
    # データフレームに変換
    return pd.DataFrame(candidates)


def solve_optimization(candidates_df, shards_limit, score_limit):
    """
    MILPを使用して最適化問題を解く関数
    
    Args:
        candidates_df (pd.DataFrame): 強化候補のデータフレーム
        shards_limit (int): カケラの上限
        score_limit (int): スキルスコア（カケラ換算）の上限
    
    Returns:
        tuple: (最適計画問題, 変数辞書, 選択された候補)
    """
    # MILP問題の初期化
    prob = pl.LpProblem("WorldLink_Support_Optimization", pl.LpMaximize)
    
    # 二値変数を定義（各候補について選択するかどうか）
    x = {i: pl.LpVariable(f"x{i}", 0, 1, cat="Binary") for i in candidates_df.index}
    
    # 目的関数: 倍率の合計を最大化
    prob += pl.lpSum(candidates_df.value[i] * x[i] for i in candidates_df.index)
    
    # 制約条件1: 選択するカードはサポートユニット最大枚数の20枚
    prob += pl.lpSum(x[i] for i in candidates_df.index) == 20
    
    # 制約条件2: 各カードは最大１つの強化案しか選択できない
    for card_id, group in candidates_df.groupby("cid"):
        prob += pl.lpSum(x[i] for i in group.index) <= 1
    
    # 制約条件3: カケラ使用量の上限
    prob += pl.lpSum(candidates_df.cost_mr[i] * x[i] for i in candidates_df.index) <= shards_limit
    
    # 制約条件4: スキルスコア使用量の上限
    prob += pl.lpSum(candidates_df.cost_skl[i] * x[i] for i in candidates_df.index) <= score_limit
    
    # 最適化問題を解く
    prob.solve(pl.PULP_CBC_CMD(msg=False))
    
    # 最適解が得られたか確認
    if pl.LpStatus[prob.status] != "Optimal":
        raise ValueError(f"最適解が得られませんでした: {pl.LpStatus[prob.status]}")
    
    # 選択された候補を取得
    selected = candidates_df[[pl.value(x[i]) > 0.5 for i in candidates_df.index]]
    
    return prob, x, selected


def save_and_print_results(prob, selected_candidates, shards_limit, score_limit):
    """
    最適化結果を保存し、出力する関数
    
    Args:
        prob (pl.LpProblem): 最適化された計画問題
        selected_candidates (pd.DataFrame): 選択された強化候補
        shards_limit (int): カケラの上限
        score_limit (int): スキルスコア（カケラ換算）の上限
    """
    # 結果をCSVファイルに保存
    selected_candidates.to_csv("best_plan.csv", index=False, encoding="utf-8-sig")
    
    # カケラ使用量の計算（スキルスコア使用後の残りをカケラで支払う）
    total_skill_cost = selected_candidates.cost_skl.sum()
    skill_cost_paid = min(total_skill_cost, score_limit)
    remaining_skill_cost = max(0, total_skill_cost - score_limit)
    
    # 合計カケラ使用量
    total_shards_used = selected_candidates.cost_mr.sum() + remaining_skill_cost
    
    # 結果を出力
    print(f"★ 最終倍率 : {prob.objective.value():.2f} %")
    print(f"★ カケラ    : {total_shards_used:.0f} / {shards_limit}")
    print(f"★ スコア    : {skill_cost_paid:.0f} / {score_limit}")


def main():
    """
    メイン関数
    """
    # データの読み込み
    cards_df, shards_limit, score_limit = load_data()
    
    # 強化候補の生成
    candidates_df = generate_candidates(cards_df)
    
    # 最適化問題を解く
    prob, x, selected = solve_optimization(candidates_df, shards_limit, score_limit)
    
    # 結果の保存と出力
    save_and_print_results(prob, selected, shards_limit, score_limit)


if __name__ == "__main__":
    main()
