# WorldLink Support Calculator

ワールドリンクのサポートユニット強化可能性計算ツール

## 概要
WorldLinkのサポートユニットを構成するカードの現在倍率を計算し、所持する強化アイテム（想いのカケラ、想いの純結晶、スキルスコア中級・上級）で最適に強化した場合の倍率上昇プランを提案します。

## ファイル構成
- `support_calculator.py`: メインの最適化プログラム
- `current_rate_calculator.py`: 現在倍率のみを計算するスクリプト
- `card_list.csv`: カード情報（name, rare, mas, skill, wl）
- `item_list.csv`: アイテム情報（item, amount）
- `.gitignore`: Git管理から除外するファイル
- `README.md`: 本ファイル

## 依存関係
- Python 3.7以上
- pandas
- numpy

## インストール
```bash
pip install pandas numpy
```

## 使い方
1. `card_list.csv`および`item_list.csv`を適宜編集
2. 以下のコマンドを実行
```bash
python support_calculator.py
```

## ライセンス
MIT
