# WorldLink Support Calculator

ワールドリンクのサポートユニット強化最適化計算ツール

## 概要
WorldLinkのサポートユニットを構成するカードの最適な強化プランを数理最適化手法を用いて計算します。所持する強化アイテム（想いのカケラ、想いの純結晶、スキルスコア中級・上級）の制約の中で、最終的なサポートユニットの合計倍率を最大化するプランを対話的に生成します。

## アルゴリズム
本ツールは混合整数線形計画法（MILP: Mixed Integer Linear Programming）を使用し、多次元ナップサック問題（MMKP: Multiple-choice Multidimensional Knapsack Problem）として定式化しています。これにより、全ての可能な強化の組み合わせの中から最適な解を高速に尋ねることができます。

## ファイル構成
- `support_calculator.py`: メインの最適化プログラム
- `card_list.csv`: カード情報（name, rare, mas, skill, wl）
- `item_list.csv`: アイテム情報（item, amount）
- `best_plan.csv`: 最適化結果の出力ファイル
- `README.md`: 本ファイル

## 依存関係
- Python 3.7以上
- pandas: データ処理用
- pulp: 数理最適化ライブラリ

## インストール
```bash
pip install pandas pulp
```

## 使い方
1. `card_list.csv`および`item_list.csv`を適宜編集
   - `card_list.csv`: カード名、レア度、現在のマスターランク、スキルレベル、WL限定フラグを記載
   - `item_list.csv`: 所持する強化アイテムの量を記載
2. 以下のコマンドを実行
```bash
python support_calculator.py
```
3. 結果がコンソールに表示され、`best_plan.csv`に保存されます

## 出力例
```
★ 最終倍率 : 325.45 %
★ カケラ    : 62850 / 69000
★ スコア    : 15850 / 15850
```

## 注意点
- カードの数が多い場合や強化パターンが多い場合でも、MILPアルゴリズムにより高速に最適解を対話的に尋ねます
- スキルスコアはカケラ換算で計算され、スキルレベル強化にのみ使用されます
