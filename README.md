# WorldLink Support Calculator

WorldLinkのサポートユニット強化最適化計算ツール（Streamlit版）

## 概要
Streamlitを用いたインタラクティブなWebアプリとして、所持カードと強化アイテム（想いのカケラ、想いの純結晶、スキルスコア中級・上級）を入力し、混合整数線形計画法（MILP）で最適な強化プランを算出します。

## ファイル構成
- `app.py`: Streamlitアプリ本体
- `support_calculator.py`: 最適化ロジック実装
- `streamlit_design.md`: UI/UX設計
- `how_to_calc.md`: 計算詳細
- `README.md`: 本ファイル

## 依存関係
- Python 3.7以上
- streamlit: Web UI
- pandas: データ処理
- pulp: 数理最適化

## インストール
```bash
pip install streamlit pandas pulp
```

## 起動方法
```bash
streamlit run app.py
```

## 使い方
1. サイドバーで所持アイテム数を入力（想いのカケラ、想いの純結晶、スキルスコア中級・上級）
2. 必要に応じてCSVファイルでカード一覧をアップロード（`card_list.csv`形式）
3. 所持カード情報を入力
4. 「最適化を実行」ボタンを押す
5. 最適化結果が表示され、CSVでダウンロード可能

## 出力例
```
★ 最終倍率 : 325.45% / 理論値: 370%
★ カケラ使用量 : 62850 / 69000
★ スキルスコア使用量（カケラ換算） : 15850 / 15850
```

## 注意事項
- アプリの利用による損害は開発者が責任を負いません
