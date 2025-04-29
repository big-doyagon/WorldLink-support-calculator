#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WorldLink サポートユニット最適化計算ツール  - Streamlit 版
（2025-04-29 仕様書改訂対応）

変更点
-------
* CSV アップロードは **サイドバー** に移動し、アップロードは任意
* CSV のフォーム反映はボタン操作で実行
* アップロードがない場合や片方のみでも動作
* メインエリアは 1 ページ構成でフォームと結果表示
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import support_calculator as sc

# --------------------------------------------------
# ページ設定
# --------------------------------------------------
st.set_page_config(
    page_title="ワールドリンク サポートユニット最適化",
    page_icon="🎮",
    layout="wide",
)

# --------------------------------------------------
# 定数
# --------------------------------------------------
RARITY_LABEL2CODE = {"☆4": "4", "BD/AN": "BD"}
MIN_CARDS = 20
MAX_CARDS = 100

# --------------------------------------------------
# サイドバー – CSV アップロード（任意）
# --------------------------------------------------
st.sidebar.header("CSV ファイル読み込み（任意）")
card_file = st.sidebar.file_uploader("カード一覧 CSV (name,rare,mas,skill,wl)", type="csv")
item_file = st.sidebar.file_uploader("アイテム一覧 CSV (item,amount)", type="csv")

if st.sidebar.button("CSV をフォームに反映", type="primary"):
    try:
        # カード CSV があれば反映
        if card_file:
            cards_df_uploaded = pd.read_csv(card_file)
            n = len(cards_df_uploaded)
            count = max(n, MIN_CARDS)
            st.session_state.card_count = min(count, MAX_CARDS)
            for i in range(st.session_state.card_count):
                if i < n:
                    row = cards_df_uploaded.iloc[i]
                    st.session_state[f"name_{i}"] = str(row.get("name", f"Card {i+1}"))
                    st.session_state[f"rare_{i}"] = (
                        {v:k for k,v in RARITY_LABEL2CODE.items()}
                        .get(str(row.get("rare", "4")).strip(), "☆4")
                    )
                    st.session_state[f"mas_{i}"] = int(row.get("mas", 0))
                    st.session_state[f"skill_{i}"] = int(row.get("skill", 1))
                    st.session_state[f"wl_{i}"] = bool(row.get("wl", 0))
                else:
                    st.session_state.setdefault(f"name_{i}", f"Card {i+1}")
                    st.session_state.setdefault(f"rare_{i}", "☆4")
                    st.session_state.setdefault(f"mas_{i}", 0)
                    st.session_state.setdefault(f"skill_{i}", 1)
                    st.session_state.setdefault(f"wl_{i}", False)
        # アイテム CSV があれば反映
        if item_file:
            items_df_uploaded = pd.read_csv(item_file)
            item_map = dict(zip(items_df_uploaded["item"], items_df_uploaded["amount"]))
            st.session_state["shard"] = int(item_map.get("想いのカケラ", 0))
            st.session_state["crystal"] = int(item_map.get("想いの純結晶", 0))
            st.session_state["med_skill"] = int(item_map.get("スキルスコア中級", 0))
            st.session_state["lge_skill"] = int(item_map.get("スキルスコア上級", 0))
        st.sidebar.success("CSV をフォームに反映しました！")
    except Exception as e:
        st.sidebar.error(f"CSV の反映でエラー: {e}")

# --------------------------------------------------
# メインエリア – 入力フォーム
# --------------------------------------------------
st.title("ワールドリンク サポートユニット最適化計算ツール")
st.caption("所持カードとアイテム数から、最も効率的な強化プランを算出します。")

# アイテム数入力
st.subheader("アイテム数入力")
col1, col2, col3, col4 = st.columns(4)
with col1:
    shard = st.number_input("想いのカケラ", min_value=0, key="shard")
with col2:
    crystal = st.number_input("想いの純結晶", min_value=0, key="crystal")
with col3:
    med_skill = st.number_input("スキルスコア中級", min_value=0, key="med_skill")
with col4:
    lge_skill = st.number_input("スキルスコア上級", min_value=0, key="lge_skill")

# カード入力フォーム
st.subheader("カード入力フォーム")
if "card_count" not in st.session_state:
    st.session_state.card_count = MIN_CARDS
count = st.number_input(
    "入力欄の枚数", min_value=MIN_CARDS, max_value=MAX_CARDS, key="card_count",
    help="最低 20 枚、最大 100 枚まで指定できます。"
)
# st.info(f"現在の入力欄数: {count} 枚")
cards_input: list[dict] = []
for i in range(count):
    with st.expander(f"カード {i+1}", expanded=True):
        c1, c2, c3, c4, c5 = st.columns([3,1,1,1,1])
        with c1:
            name = st.text_input("カード名（自由入力）", key=f"name_{i}")
        with c2:
            rare = st.selectbox("レアリティ", list(RARITY_LABEL2CODE.keys()), key=f"rare_{i}")
        with c3:
            mas = st.number_input("マスターランク", min_value=0, max_value=5, key=f"mas_{i}")
        with c4:
            skill = st.number_input("スキルレベル", min_value=1, max_value=4, key=f"skill_{i}")
        with c5:
            wl = st.checkbox("WL 限定", key=f"wl_{i}")
        cards_input.append({
            "name": name or f"Card {i+1}",
            "rare": RARITY_LABEL2CODE[rare],
            "mas": mas,
            "skill": skill,
            "wl": int(wl),
        })

# データ保存ボタン
if st.button("入力データを CSV で保存"):
    df_cards = pd.DataFrame(cards_input)
    st.download_button("カード一覧をダウンロード", df_cards.to_csv(index=False).encode("utf-8-sig"), "card_list.csv", "text/csv")
    df_items = pd.DataFrame([
        {"item":"想いのカケラ","amount":shard},
        {"item":"想いの純結晶","amount":crystal},
        {"item":"スキルスコア中級","amount":med_skill},
        {"item":"スキルスコア上級","amount":lge_skill},
    ])
    st.download_button("アイテム一覧をダウンロード", df_items.to_csv(index=False).encode("utf-8-sig"), "item_list.csv", "text/csv")

# 最適化実行
if st.button("🔍 最適化を実行", type="primary"):
    try:
        with st.spinner("最適化計算中..."):
            cards_df = pd.DataFrame(cards_input)
            shards_limit = shard + 2000 * crystal
            score_limit = med_skill * sc.MED_SK + lge_skill * sc.LGE_SK
            prob, x, selected = sc.solve_optimization(sc.generate_candidates(cards_df), shards_limit, score_limit)
            total_mr = selected.cost_mr.sum()
            total_skl = selected.cost_skl.sum()
            skill_paid = min(total_skl, score_limit)
            shard_on_skl = max(0, total_skl - score_limit)
            total_shards = total_mr + shard_on_skl
        st.success("最適化が完了しました！")
        st.metric("最終倍率", f"{prob.objective.value():.2f}%")
        m1, m2, m3 = st.columns(3)
        m1.metric("カケラ使用量", f"{total_shards} / {shards_limit}")
        m2.metric("スキルスコア使用量", f"{skill_paid} / {score_limit}")
        m3.metric("選択カード数", len(selected))
        st.subheader("サポートユニット詳細")
        st.dataframe(selected, use_container_width=True)
        st.download_button("結果を CSV でダウンロード", selected.to_csv(index=False).encode("utf-8-sig"), "best_plan.csv", "text/csv")
    except Exception as e:
        st.error(f"最適化中にエラーが発生しました: {e}")

st.markdown("---")
st.caption("© 2025 WorldLink Support Optimizer")
