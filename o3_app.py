#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WorldLink サポートユニット最適化 ― Streamlit GUI
------------------------------------------------
■ 画面構成
    ├── 左：入力（CSVアップロード / 直接入力タブ）
    └── 右：結果表示
■ 必要ファイル
    ・support_calculator.py  （同じフォルダに配置）
"""

import io
import pandas as pd
import streamlit as st
from typing import Dict, Tuple

# 既存ロジックをインポート
import support_calculator as sc            # :contentReference[oaicite:2]{index=2}&#8203;:contentReference[oaicite:3]{index=3}

# ------------------------------------------------------------
# 共通ユーティリティ
# ------------------------------------------------------------
ITEM_LABELS = [
    "想いのカケラ",
    "想いの純結晶",
    "スキルスコア中級",
    "スキルスコア上級",
]


def calc_resources(items: Dict[str, int]) -> Tuple[int, int]:
    """カケラ上限とスキルスコア上限を計算"""
    shard = int(items["想いのカケラ"])
    crystal = int(items["想いの純結晶"])
    med = int(items["スキルスコア中級"])
    lge = int(items["スキルスコア上級"])

    shards_limit = shard + 2000 * crystal
    score_limit = med * sc.MED_SK + lge * sc.LGE_SK
    return shards_limit, score_limit


def run_optimization(cards_df: pd.DataFrame, items: Dict[str, int]):
    """最適化を実行し、結果 DF とメタデータを返す"""
    shards_limit, score_limit = calc_resources(items)
    # 候補生成
    candidates_df = sc.generate_candidates(cards_df)
    # 実行枚数が 20 枚未満の場合はエラー
    if len(candidates_df["cid"].unique()) < 20:
        st.error("カードは最低 20 枚必要です。")
        return None, None

    # 最適化
    try:
        prob, _, selected = sc.solve_optimization(
            candidates_df, shards_limit, score_limit
        )
    except ValueError as e:
        st.error(str(e))
        return None, None

    # 追加メタ計算
    total_mr = selected.cost_mr.sum()
    total_skl = selected.cost_skl.sum()
    skill_paid = min(total_skl, score_limit)
    shard_on_skl = max(0, total_skl - score_limit)
    total_shards_used = total_mr + shard_on_skl

    metrics = {
        "最終倍率 %": f"{prob.objective.value():.2f}",
        "カケラ使用量": f"{total_shards_used} / {shards_limit}",
        "スキルスコア使用量": f"{skill_paid} / {score_limit}",
    }
    return selected, metrics


# ------------------------------------------------------------
# Streamlit 画面
# ------------------------------------------------------------
st.set_page_config(page_title="WorldLink Support Optimizer", layout="wide")
st.title("WorldLink サポートユニット最適化ツール")

left, right = st.columns(2)

with left:
    tabs = st.tabs(["📂 CSV ファイル読み込み", "⌨️ 直接入力"])

    # ---------- タブ① : CSV アップロード ----------
    with tabs[0]:
        st.subheader("カード一覧 CSV")
        card_file = st.file_uploader(
            "カード一覧 (.csv)", type="csv", key="card_csv"
        )
        st.subheader("アイテム一覧 CSV（任意）")
        item_file = st.file_uploader(
            "アイテム一覧 (.csv)", type="csv", key="item_csv"
        )

        if st.button("最適化を実行", key="run_csv"):
            if card_file is None:
                st.error("カード CSV を選択してください。")
            else:
                cards_df = pd.read_csv(card_file)
                # アイテム
                if item_file:
                    items_df = pd.read_csv(item_file)
                    items = dict(zip(items_df["item"], items_df["amount"]))
                else:
                    # 未アップロードの場合は 0 で初期化
                    items = {label: 0 for label in ITEM_LABELS}

                selected, metrics = run_optimization(cards_df, items)
                st.session_state["result"] = (selected, metrics, cards_df, items)

    # ---------- タブ② : 直接入力 ----------
    with tabs[1]:
        st.subheader("カード一覧")
        n_cards = st.number_input("カード枚数", 20, 100, 20, step=1, key="n_cards")
        card_inputs = []
        for i in range(n_cards):
            with st.expander(f"カード {i+1}", expanded=i < 3):
                name = st.text_input("カード名", key=f"name_{i}")
                rare = st.selectbox("レアリティ", ["4", "BD"], key=f"rare_{i}")
                mas = st.selectbox("マスターランク", list(range(6)), key=f"mas_{i}")
                skl = st.selectbox("スキルレベル", list(range(1, 5)), key=f"skl_{i}")
                wl = st.checkbox("WL限定", key=f"wl_{i}")
                card_inputs.append(
                    {"name": name, "rare": rare, "mas": mas, "skill": skl, "wl": wl}
                )

        st.subheader("アイテム数")
        items = {
            label: st.number_input(label, 0, 999_999, 0, step=100, key=f"item_{idx}")
            for idx, label in enumerate(ITEM_LABELS)
        }

        if st.button("最適化を実行", key="run_manual"):
            cards_df = pd.DataFrame(card_inputs)
            # 無入力行を除去
            cards_df = cards_df[cards_df["name"].str.strip() != ""]
            selected, metrics = run_optimization(cards_df, items)
            st.session_state["result"] = (selected, metrics, cards_df, items)

    # ---------- 入力内容のダウンロード ----------
    if "result" in st.session_state:
        _, _, cards_df_dl, items_dl = st.session_state["result"]
        buff1 = io.BytesIO()
        cards_df_dl.to_csv(buff1, index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 現状カード一覧をダウンロード",
            data=buff1.getvalue(),
            file_name="card_list_current.csv",
            mime="text/csv",
        )

        item_df_dl = pd.DataFrame(
            [{"item": k, "amount": v} for k, v in items_dl.items()]
        )
        buff2 = io.BytesIO()
        item_df_dl.to_csv(buff2, index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 現状アイテム一覧をダウンロード",
            data=buff2.getvalue(),
            file_name="item_list_current.csv",
            mime="text/csv",
        )

with right:
    st.header("最適化結果")
    if "result" in st.session_state:
        selected, metrics, _, _ = st.session_state["result"]
        if selected is not None:
            # メトリクス
            st.metric("最終倍率 (%)", metrics["最終倍率 %"])
            st.metric("カケラ使用量", metrics["カケラ使用量"])
            st.metric("スキルスコア使用量", metrics["スキルスコア使用量"])
            # 結果テーブル
            st.dataframe(
                selected[["name", "wl", "mas_tgt", "skl_tgt", "value"]],
                hide_index=True,
            )
        else:
            st.info("左側で最適化を実行してください。")
    else:
        st.info("左側で最適化を実行してください。")
