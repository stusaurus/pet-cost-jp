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
- `scripts/analytics_runtime.js`: GA4イベント計測

将来の `baby-cost-jp` / `food-cost-jp` では、共通ロジックを流用しつつカテゴリー設定と分類器を差し替える想定です。

## 必要なRepository secrets
Settings → Secrets and variables → Actions で以下を登録します。

- `RAKUTEN_APPLICATION_ID`
- `RAKUTEN_ACCESS_KEY`
- `RAKUTEN_AFFILIATE_ID`

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
GitHub Actionsがテスト → 楽天データ取得 → 静的サイト生成 → GitHub Pages公開を行います。毎日06:20 JSTにも自動更新します。
