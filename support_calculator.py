# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import sys

# 標準出力の文字コードをUTF-8に設定
sys.stdout.reconfigure(encoding='utf-8')

# グローバル変数
WL_BONUS = 20.0  # WL限定メンバーの追加ボーナス（%）

# レアリティに基づく基本倍率
def get_base_rate(rare):
    if rare == 4:  # ☆4
        return 12.5
    elif rare == "BD":  # バースデー
        return 10.0
    else:
        return 0.0

# マスターランクによるボーナス
def get_master_rank_bonus(rare, rank):
    if rare == 4:  # ☆4
        return 0.5 * rank
    elif rare == "BD":  # バースデー
        return 0.4 * rank
    else:
        return 0.0

# スキルレベルによるボーナス
def get_skill_level_bonus(rare, level):
    if rare == 4:  # ☆4
        if level == 1:
            return 0.0
        elif level == 2:
            return 0.25
        elif level == 3:
            return 1.0
        elif level == 4:
            return 2.5
    elif rare == "BD":  # バースデー
        if level == 1:
            return 0.0
        elif level == 2:
            return 0.2
        elif level == 3:
            return 0.8
        elif level == 4:
            return 2.0
    return 0.0

# カードの倍率を計算
def calculate_card_rate(name, rare, master_rank, skill_level, is_wl):
    # 基本倍率
    base_rate = get_base_rate(rare)
    
    # WL限定メンバーかチェック（wl列が1の場合）
    wl_bonus = WL_BONUS if is_wl == 1 else 0.0
    
    # マスターランクボーナス
    master_bonus = get_master_rank_bonus(rare, master_rank)
    
    # スキルレベルボーナス
    skill_bonus = get_skill_level_bonus(rare, skill_level)
    
    # 合計倍率
    total_rate = base_rate + wl_bonus + master_bonus + skill_bonus
    
    return total_rate

# マスターランク強化に必要なカケラの量
def get_master_rank_cost(rare, current_rank, target_rank):
    if current_rank >= target_rank:
        return 0
    
    costs = {
        4: [0, 2000, 4000, 6000, 8000, 10000],  # ☆4
        "BD": [0, 1000, 2000, 3000, 4000, 5000]  # バースデー
    }
    
    # rareが文字列型の場合は適切な型に変換
    if isinstance(rare, str) and rare != "BD":
        rare = int(rare)
    
    return costs[rare][target_rank] - costs[rare][current_rank]

# スキルレベル強化に必要なカケラの量
def get_skill_level_cost(rare, current_level, target_level):
    if current_level >= target_level:
        return 0
    
    costs = {
        4: [0, 0, 1000, 4000, 10000],  # ☆4（インデックス1から始まる）
        "BD": [0, 0, 500, 2000, 5000]  # バースデー（インデックス1から始まる）
    }
    
    # rareが文字列型の場合は適切な型に変換
    if isinstance(rare, str) and rare != "BD":
        rare = int(rare)
    
    return costs[rare][target_level] - costs[rare][current_level]

# カードリストを読み込む
def load_cards():
    cards_df = pd.read_csv('card_list.csv')
    
    # データ型を適切に変換
    # rare列を整数型または文字列型に変換する
    cards_df['rare'] = cards_df['rare'].apply(lambda x: x if x == 'BD' else int(x))  # BDは文字列、それ以外は数値として扱う
    cards_df['wl'] = cards_df['wl'].astype(int)  # wl列を整数型に変換
    
    # 各カードの現在の倍率を計算
    cards_df['current_rate'] = cards_df.apply(
        lambda row: calculate_card_rate(row['name'], row['rare'], row['mas'], row['skill'], row['wl']), 
        axis=1
    )
    
    return cards_df

# 強化シミュレーション
def simulate_upgrades(cards_df, fragments, skill_mid, skill_high):
    # 強化プランを保存するリスト
    upgrade_plans = []
    
    # 各カードに対して強化シミュレーション
    for index, card in cards_df.iterrows():
        name = card['name']
        rare = card['rare']
        current_mas = card['mas']
        current_skill = card['skill']
        current_rate = card['current_rate']
        
        # 可能な強化の組み合わせ
        for target_mas in range(current_mas, 6):
            for target_skill in range(current_skill, 5):
                # 強化に必要なカケラ量を計算
                mas_cost = get_master_rank_cost(rare, current_mas, target_mas)
                skill_cost = get_skill_level_cost(rare, current_skill, target_skill)
                
                # スキルスコアでのコスト削減を考慮
                skill_fragments_equiv = 0
                remaining_skill_cost = skill_cost
                
                # スキルスコア上級を使用
                skill_high_used = min(skill_high, remaining_skill_cost // 250)
                remaining_skill_cost -= skill_high_used * 250
                skill_fragments_equiv += skill_high_used * 250
                
                # スキルスコア中級を使用
                skill_mid_used = min(skill_mid, remaining_skill_cost // 50)
                remaining_skill_cost -= skill_mid_used * 50
                skill_fragments_equiv += skill_mid_used * 50
                
                # 残りの必要なカケラ
                total_fragments_needed = mas_cost + remaining_skill_cost
                
                # 十分なカケラがあるか確認
                if total_fragments_needed <= fragments:
                    # 強化後の倍率を計算
                    is_wl = card['wl']
                    new_rate = calculate_card_rate(name, rare, target_mas, target_skill, is_wl)
                    rate_increase = new_rate - current_rate
                    
                    # 強化プランを追加
                    if rate_increase > 0:
                        upgrade_plans.append({
                            'index': index,
                            'name': name,
                            'rare': rare,
                            'current_mas': current_mas,
                            'current_skill': current_skill,
                            'target_mas': target_mas,
                            'target_skill': target_skill,
                            'fragments_needed': total_fragments_needed,
                            'skill_fragments_equiv': skill_fragments_equiv,
                            'skill_high_used': skill_high_used,
                            'skill_mid_used': skill_mid_used,
                            'current_rate': current_rate,
                            'new_rate': new_rate,
                            'rate_increase': rate_increase,
                            'efficiency': rate_increase / (total_fragments_needed + 0.001)  # 0除算を防ぐ
                        })
    
    # 効率順にソート
    if upgrade_plans:
        upgrade_plans = sorted(upgrade_plans, key=lambda x: x['efficiency'], reverse=True)
    
    return upgrade_plans

# 上位20枚のカードを取得する関数
def get_top_20_cards(cards_df):
    # カードの現在の倍率を計算
    card_rates = []
    for idx, card in cards_df.iterrows():
        name = card['name']
        rare = card['rare']
        mas = card['mas']
        skill = card['skill']
        wl = card['wl']
        rate = calculate_card_rate(name, rare, mas, skill, wl)
        card_rates.append((idx, rate))
    
    # 倍率順にソート
    card_rates.sort(key=lambda x: x[1], reverse=True)
    
    # 上位20枚のインデックスを返す
    top_20_indices = [idx for idx, _ in card_rates[:20]]
    return top_20_indices

# 最適な強化プランを選択
# 最適な強化プランを選択（効率閾値を考慮）
def select_optimal_upgrades(cards_df, upgrade_plans, fragments, skill_mid, skill_high):
    if not upgrade_plans:
        return [], fragments, skill_mid, skill_high
    
    # 効率の良いプランだけを選択するための閾値を設定
    # 0.0001は1フラグメントあたりの倍率上昇が0.01%以上のプランを意味する
    EFFICIENCY_THRESHOLD = 0.0001
    
    selected_plans = []
    remaining_fragments = fragments
    remaining_skill_mid = skill_mid
    remaining_skill_high = skill_high
    
    # カードをコピーして強化後の状態をシミュレート
    updated_cards = cards_df.copy()
    
    # 効率の良い順に強化プランを適用
    while upgrade_plans and (remaining_fragments > 0 or remaining_skill_mid > 0 or remaining_skill_high > 0):
        # 現在の上位20枚を取得
        top_20_indices = get_top_20_cards(updated_cards)
        
        best_plan = None
        best_index = -1
        
        # 残りのリソースで実行可能で、上位20枚に入る（または強化後に入る）カードの中で
        # 効率閾値を超えている最も効率の良いプランを見つける
        filtered_plans = []
        for i, plan in enumerate(upgrade_plans):
            card_index = plan['index']
            total_fragments = plan['fragments_needed']
            skill_mid_used = plan['skill_mid_used']
            skill_high_used = plan['skill_high_used']
            
            # リソースが足りない場合はスキップ
            if (total_fragments > remaining_fragments or
                skill_mid_used > remaining_skill_mid or
                skill_high_used > remaining_skill_high):
                continue
            
            # 効率が閾値を下回る場合はスキップ（効率の悪い強化をしない）
            if plan['efficiency'] < EFFICIENCY_THRESHOLD:
                continue
                
            # この強化プランを適用した場合に、そのカードが上位20枚に入るかシミュレーション
            temp_cards = updated_cards.copy()
            temp_cards.at[card_index, 'mas'] = plan['target_mas']
            temp_cards.at[card_index, 'skill'] = plan['target_skill']
            
            future_top_20 = get_top_20_cards(temp_cards)
            
            # 強化後に上位20枚に入る場合のみ、有効なプランとして追加
            if card_index in future_top_20:
                filtered_plans.append((i, plan))
        
        # 効率でソート
        if filtered_plans:
            filtered_plans.sort(key=lambda x: x[1]['efficiency'], reverse=True)
            best_index, best_plan = filtered_plans[0]
        else:
            # 有効なプランがない場合は終了（効率の悪いプランや上位20枚に入らないプランは実行しない）
            break
        
        # 選択したプランを適用
        card_index = best_plan['index']
        updated_cards.at[card_index, 'mas'] = best_plan['target_mas']
        updated_cards.at[card_index, 'skill'] = best_plan['target_skill']
        
        # リソースを減らす
        remaining_fragments -= best_plan['fragments_needed']
        remaining_skill_mid -= best_plan['skill_mid_used']
        remaining_skill_high -= best_plan['skill_high_used']
        
        # 選択したプランを記録
        selected_plans.append(best_plan)
        
        # 使用したプランを削除
        upgrade_plans.pop(best_index)
        
        # 更新されたカードの情報に基づいて新しいアップグレードプランを再計算
        new_plans = simulate_upgrades(updated_cards, remaining_fragments, remaining_skill_mid, remaining_skill_high)
    
    return selected_plans, remaining_fragments, remaining_skill_mid, remaining_skill_high

# メイン処理
def main():
    print("===== ワールドリンク サポートユニット最適化ツール =====")
    print("※ 効率の悪い強化は実行せず、リソースを温存します")
    
    # カードリストを読み込む
    print("カードリストを読み込んでいます...")
    cards_df = load_cards()
    print(f"合計 {len(cards_df)} 枚のカードを読み込みました。")
    
    # 強化アイテム状況をファイルから読み込む
    print("\n===== 強化アイテムの状況を読み込んでいます =====")
    try:
        # item_list.csvからアイテム情報を読み込む
        items_df = pd.read_csv('item_list.csv')
        
        # 各アイテムの数を取得
        fragments = items_df.loc[items_df['item'] == '想いのカケラ', 'amount'].values[0]
        pure_crystal = items_df.loc[items_df['item'] == '想いの純結晶', 'amount'].values[0]
        skill_mid = items_df.loc[items_df['item'] == 'スキルスコア中級', 'amount'].values[0]
        skill_high = items_df.loc[items_df['item'] == 'スキルスコア上級', 'amount'].values[0]
        
        print(f"想いのカケラの数: {fragments}")
        print(f"想いの純結晶の数: {pure_crystal}")
        print(f"スキルスコア中級の数: {skill_mid}")
        print(f"スキルスコア上級の数: {skill_high}")
    except Exception as e:
        print(f"アイテムリストの読み込みに失敗しました: {e}")
        print("item_list.csvファイルは以下の形式で作成してください:")
        print("item,amount")
        print("想いのカケラ,[個数]")
        print("想いの純結晶,[個数]")
        print("スキルスコア中級,[個数]")
        print("スキルスコア上級,[個数]")
        sys.exit(1)
    
    # 純結晶をカケラに換算
    fragments += pure_crystal * 2000
    
    # 現在のサポートユニット倍率を計算
    current_top20 = cards_df.nlargest(20, 'current_rate')
    current_total_rate = current_top20['current_rate'].sum()
    
    print(f"\n現在のサポートユニット倍率: {current_total_rate:.2f}%")
    
    # 強化シミュレーション
    print("\n強化シミュレーションを実行中...")
    upgrade_plans = simulate_upgrades(cards_df, fragments, skill_mid, skill_high)
    
    if not upgrade_plans:
        print("強化可能なカードはありません。")
        return
    
    # 最適な強化プランを選択
    optimal_plans, remaining_fragments, remaining_skill_mid, remaining_skill_high = select_optimal_upgrades(
        cards_df, upgrade_plans, fragments, skill_mid, skill_high
    )
    
    if not optimal_plans:
        print("最適な強化プランは見つかりませんでした。")
        return
    
    # 強化後のカードデータ
    updated_cards = cards_df.copy()
    for plan in optimal_plans:
        card_index = plan['index']
        updated_cards.at[card_index, 'mas'] = plan['target_mas']
        updated_cards.at[card_index, 'skill'] = plan['target_skill']
        updated_cards.at[card_index, 'current_rate'] = plan['new_rate']
    
    # 強化後のサポートユニット倍率を計算
    updated_top20 = updated_cards.nlargest(20, 'current_rate')
    updated_total_rate = updated_top20['current_rate'].sum()
    
    # 結果を表示
    print("\n===== 最適な強化プラン =====")
    used_fragments = fragments - remaining_fragments
    used_skill_mid = skill_mid - remaining_skill_mid
    used_skill_high = skill_high - remaining_skill_high
    
    print(f"使用したアイテム: カケラ {used_fragments}個, スキルスコア中級 {used_skill_mid}個, スキルスコア上級 {used_skill_high}個")
    print(f"残りのアイテム: カケラ {remaining_fragments}個, スキルスコア中級 {remaining_skill_mid}個, スキルスコア上級 {remaining_skill_high}個")
    print(f"強化前の倍率: {current_total_rate:.2f}%")
    print(f"強化後の倍率: {updated_total_rate:.2f}%")
    print(f"倍率の増加: {updated_total_rate - current_total_rate:.2f}%")
    
    # 使用効率の計算
    if used_fragments > 0 or used_skill_mid > 0 or used_skill_high > 0:
        fragment_equivalent = used_fragments + used_skill_mid * 300 + used_skill_high * 3000
        rate_per_fragment = (updated_total_rate - current_total_rate) / fragment_equivalent * 10000
        print(f"強化効率: {rate_per_fragment:.4f}%/万カケラ")
    
    # 強化プランの詳細
    print("\n===== 強化プランの詳細 =====")
    for i, plan in enumerate(optimal_plans, 1):
        print(f"{i}. {plan['name']} ({plan['rare']})") 
        print(f"   マスターランク: {plan['current_mas']} → {plan['target_mas']}") 
        print(f"   スキルレベル: {plan['current_skill']} → {plan['target_skill']}")
        print(f"   倍率: {plan['current_rate']:.2f}% → {plan['new_rate']:.2f}% (+{plan['rate_increase']:.2f}%)") 
        print(f"   必要なカケラ: {plan['fragments_needed']}個")
        print(f"   使用するスキルスコア: 中級 {plan['skill_mid_used']}個, 上級 {plan['skill_high_used']}個")
        
    # 全カードの最終状態を表示
    print("\n===== 全カードの最終状態 =====")
    print("名前                    レア度  マスターランク  スキルレベル   倍率    (増加分)   部隊入り")
    print("-" * 90)
    
    # カードを強化後の倍率で降順にソート
    cards_with_upgrade = cards_df.copy()
    
    # 強化されたカードの情報を更新
    for plan in optimal_plans:
        card_idx = cards_df[cards_df['name'] == plan['name']].index[0]
        cards_with_upgrade.at[card_idx, 'mas'] = plan['target_mas']
        cards_with_upgrade.at[card_idx, 'skill'] = plan['target_skill']
    
    # 各カードの強化後の倍率を計算
    updated_rates = []
    for idx, card in cards_with_upgrade.iterrows():
        name = card['name']
        rare = card['rare']
        mas = card['mas']
        skill = card['skill']
        wl = card['wl']
        
        original_card = cards_df.iloc[idx]
        original_mas = original_card['mas']
        original_skill = original_card['skill']
        
        # 現在と強化後の倍率を計算
        original_rate = calculate_card_rate(name, rare, original_mas, original_skill, wl)
        updated_rate = calculate_card_rate(name, rare, mas, skill, wl)
        
        increase = updated_rate - original_rate
        updated_rates.append({
            'name': name,
            'rare': rare,
            'mas': mas,
            'skill': skill,
            'wl': wl,
            'rate': updated_rate,
            'increase': increase,
            'original_mas': original_mas,
            'original_skill': original_skill,
            'original_rate': original_rate
        })
    
    # 強化後の倍率で降順にソート
    updated_rates.sort(key=lambda x: x['rate'], reverse=True)
    
    # 上位20枚を取得
    top_20_cards = [r['name'] for r in updated_rates[:20]]
    
    # 表示
    for i, card in enumerate(updated_rates):
        name_display = card['name'][:20].ljust(20)
        if len(card['name']) > 20:
            name_display += '...'
        else:
            name_display += ' ' * 3
            
        upgraded = card['increase'] > 0
        in_team = "★" if i < 20 else ""
        
        print(f"{name_display} {card['rare']}    {card['mas']}          {card['skill']}        {card['rate']:.2f}%"  + 
              (f"  (+{card['increase']:.2f}%)" if upgraded else '') + f"   {in_team}")
    
    print("\nプログラムを終了します...")



if __name__ == "__main__":
    main()
