#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WorldLink サポートユニット最適化計算ツール - Streamlit版

CSV読み込み or 直接入力に対応したStreamlitアプリ
"""

import streamlit as st
import pandas as pd
import numpy as np
import support_calculator as sc
import pulp as pl
from io import StringIO

# ページ設定
st.set_page_config(
    page_title="WorldLink サポート最適化",
    page_icon="🎮",
    layout="wide"
)

# タイトル表示
st.title("WorldLink サポートユニット最適化計算ツール")
st.markdown("所持するカードとアイテムから、最も効率的な強化プランを算出します。")

# タブ設定
tab1, tab2 = st.tabs(["CSVファイル読み込み", "直接入力"])

# CSVファイル読み込みタブ
with tab1:
    st.header("CSVファイルからデータを読み込む")
    
    st.markdown("### カード情報")
    card_file = st.file_uploader("カード一覧CSVをアップロード", type="csv", help="フォーマット: name,rare,mas,skill,wl")
    
    st.markdown("### アイテム情報")
    item_file = st.file_uploader("アイテム一覧CSVをアップロード", type="csv", help="フォーマット: item,amount")
    
    if card_file and item_file:
        cards_df = pd.read_csv(card_file)
        items_df = pd.read_csv(item_file)
        
        st.success("ファイルの読み込みが完了しました！")
        
        with st.expander("読み込んだデータの確認"):
            st.write("カード一覧：")
            st.dataframe(cards_df)
            st.write("アイテム一覧：")
            st.dataframe(items_df)

# 直接入力タブ
with tab2:
    st.header("データを直接入力する")
    
    st.markdown("### アイテム情報")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        shard = st.number_input("想いのカケラ", min_value=0, value=0)
    with col2:
        crystal = st.number_input("想いの純結晶", min_value=0, value=0)
    with col3:
        med_skill = st.number_input("スキルスコア中級", min_value=0, value=0)
    with col4:
        lge_skill = st.number_input("スキルスコア上級", min_value=0, value=0)
    
    st.markdown("### カード情報")
    st.markdown("最大20枚まで入力できます。必要な分だけ入力してください。")
    
    # カードデータ用のリスト
    cards_data = []
    
    # レア度選択肢
    rarity_options = {"☆4": "4", "バースデー": "BD"}
    
    # 20枚分のカード入力フォームを作成
    cards_input = []
    for i in range(20):
        with st.expander(f"カード {i+1}", expanded=True if i < 5 else False):
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                name = st.text_input("カード名", key=f"name_{i}")
            with col2:
                rare = st.selectbox("レア度", list(rarity_options.keys()), key=f"rare_{i}")
            with col3:
                mas = st.number_input("マスターランク", min_value=0, max_value=5, key=f"mas_{i}")
            with col4:
                skill = st.number_input("スキルレベル", min_value=1, max_value=4, key=f"skill_{i}")
            with col5:
                wl = st.checkbox("WL限定", key=f"wl_{i}")
            
            if name:  # 名前が入力されている場合のみデータに追加
                cards_input.append({
                    "name": name,
                    "rare": rarity_options[rare],
                    "mas": mas,
                    "skill": skill,
                    "wl": 1 if wl else 0
                })

    direct_input_ready = len(cards_input) > 0

# 実行ボタン
run_button = st.button("最適化を実行", type="primary", disabled=not ((card_file and item_file) or direct_input_ready))

# 実行処理
if run_button:
    try:
        with st.spinner("最適化計算中..."):
            # データ準備
            if tab1._active and card_file and item_file:
                # CSVから読み込む場合
                cards_df = pd.read_csv(card_file)
                
                # アイテム情報を辞書形式に変換
                items_df = pd.read_csv(item_file)
                item_dict = dict(zip(items_df["item"], items_df["amount"]))
                
                # 各アイテムの数を取得
                shard = int(item_dict["想いのカケラ"])
                crystal = int(item_dict["想いの純結晶"])
                med_skill = int(item_dict["スキルスコア中級"])
                lge_skill = int(item_dict["スキルスコア上級"])
                
            else:
                # 直接入力の場合
                cards_df = pd.DataFrame(cards_input)
            
            # カケラとスキルスコアの上限を計算
            shards_limit = shard + 2000 * crystal
            score_limit = med_skill * sc.MED_SK + lge_skill * sc.LGE_SK
            
            # 強化候補の生成
            candidates_df = sc.generate_candidates(cards_df)
            
            # 最適化問題を解く
            prob, x, selected = sc.solve_optimization(candidates_df, shards_limit, score_limit)
            
            # --- 使用量計算 ---
            total_mr = selected.cost_mr.sum()
            total_skl = selected.cost_skl.sum()

            # スキルスコアを優先的に充当し、足りない分だけカケラ補填
            skill_paid = min(total_skl, score_limit)
            shard_on_skl = max(0, total_skl - score_limit)

            total_shards_used = total_mr + shard_on_skl
            
            # 結果表示
            st.success("最適化が完了しました！")
            
            # 結果サマリー
            st.header("最適化結果")
            
            # 主要指標を表示
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("最終倍率", f"{prob.objective.value():.2f}%")
            with col2:
                st.metric("カケラ使用量", f"{total_shards_used} / {shards_limit}")
            with col3:
                st.metric("スキルスコア使用量", f"{skill_paid} / {score_limit}")
            
            # 詳細結果
            st.subheader("サポートユニット詳細")
            
            # 結果のダウンロードボタン
            csv = selected.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="CSVとしてダウンロード",
                data=csv,
                file_name="best_plan.csv",
                mime="text/csv"
            )
            
            # データフレームを表示
            st.dataframe(selected)
            
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")

# 使い方ガイド
with st.expander("使い方ガイド"):
    st.markdown("""
    ### このアプリについて
    
    WorldLinkのサポートユニットを最適化するためのMILP（混合整数線形計画法）ソルバーです。
    所持するカードとアイテムから、最も効率的な強化プランを算出します。
    
    ### 使い方
    
    #### CSVファイル読み込み
    1. `card_list.csv` と `item_list.csv` をアップロードしてください。
    2. CSVファイルのフォーマットは以下の通りです：
       - カード一覧: `name,rare,mas,skill,wl`
       - アイテム一覧: `item,amount`
    
    #### 直接入力
    1. アイテム情報（カケラ、純結晶、スキルスコア）を入力してください。
    2. カード情報を最大20枚まで入力できます。
    3. 入力後、「最適化を実行」ボタンをクリックしてください。
    
    ### 注意事項
    
    - 最適化計算には数秒～数十秒かかることがあります。
    - 入力データによっては最適解が得られない場合があります。
    """)

# フッター
st.markdown("---")
st.markdown("WorldLink サポートユニット最適化計算ツール - Streamlit版")
