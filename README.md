# pet-cost-jp

ペット用品を総額ではなく「1枚・1L」など同じ単位に揃えて比較する、GitHub Pages向けのコスパ比較サイトです。

## MVPカテゴリー
- ペットシーツ: 1枚あたり。レギュラー / ワイド / スーパーワイドを分離。
- 猫砂: 1Lあたり。kgのみの商品は推測換算せず除外。
- 猫用システムトイレシート: 1枚あたり。対応シリーズを分離。

## 設計
- `config/categories.json`: カテゴリー定義
- `scripts/common/quantity.py`: 単価計算用の数量解析
- `scripts/common/classify.py`: ペット用品固有の条件分類
- `scripts/common/rakuten.py`: 楽天API取得
- `scripts/common/engine.py`: 共通の正規化・ランキング
- `scripts/build_site.py`: 静的サイト生成
- `scripts/audit_products.py`: 公開直前の生成データ品質監査
- `scripts/analytics_runtime.js`: GA4イベント計測

将来の `baby-cost-jp` / `food-cost-jp` では、共通ロジックを流用しつつカテゴリー設定と分類器を差し替える想定です。

## 商品品質ルール
- 数量・容量が一意に確定できない選択式商品は掲載しない
- kgだけの猫砂をLへ推測換算しない
- ペットシーツはサイズを混在させない
- 猫砂は素材・用途を分け、混合素材は混合として扱う
- システムトイレシートは互換性を優先して分類する
- 中古・訳あり・アウトレット・定期便・ふるさと納税は比較対象外
- 同一商品ファミリーは「最安単価」と「最小総額」を最大2件まで残し、ランキング占有を防ぐ
- GitHub Actionsで生成後の単価・分類・URL・重複を再監査し、異常時はPagesへ公開しない

## 必要なRepository secrets
Settings → Secrets and variables → Actions で以下を登録します。

- `RAKUTEN_APPLICATION_ID`
- `RAKUTEN_ACCESS_KEY`
- `RAKUTEN_AFFILIATE_ID`

`RAKUTEN_APPLICATION_ID` と `RAKUTEN_ACCESS_KEY` はペットサイト用に登録した楽天Web Serviceアプリの値を使用し、`RAKUTEN_AFFILIATE_ID` は他サイトと共通で利用します。

GA4は日用品版と同じMeasurement IDを使用し、全イベントに `site_id=pet-cost-jp` を付与して判別します。

## GA4イベント
- `comparison_view`
- `comparison_filter`
- `unit_calculator_use`
- `affiliate_click`
- `product_result_click`
- `view_item_list`
- `select_item`

主要パラメータ: `site_id`, `category_id`, `item_id`, `item_name`, `merchant`, `unit_metric`, `unit_price`, `position`, `conversion_source`, `operator_test`

## 公開
GitHub Actionsがテスト → 楽天データ取得 → 静的サイト生成 → 商品品質監査 → GitHub Pages公開を行います。毎日06:20 JSTにも自動更新します。
