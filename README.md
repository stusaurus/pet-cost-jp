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

## 比較画面と検証

条件 → 最安の結論と計算根拠 → 同じ尺度のTOP3 → 3つの選び方 → 商品一覧 → 店頭比較の順に表示します。
`assets/comparison.css` が共通スタイルで、生成HTMLにインライン化します。旧版の装飾CSSは撤去しました。
中央値は偶数件の場合、中央2件の平均です。送料別の商品は送料を加算せず、その旨を表示します。

既存の `homepage_editorial_click` / `daily_spotlight_click` も維持しています。統合したカテゴリ入口で両方を送ります。
新しい `comparison_angle_select` は選び方の変更を計測し、`angle_role=unit|total|bulk` と現在の条件・商品IDを送ります。
条件変更は既存 `comparison_filter` に結果件数・最安単価・中央値を追加。店頭比較の自動再計算ではイベントを再送しません。
`?test=1` で運営者検証の `operator_test=1` を付け、`?test=0` で解除できます。

```sh
python -m unittest discover -s tests -p 'test_*.py'
npm ci --ignore-scripts
npm test
python scripts/audit_products.py
```

`npm test` はコミット済みの商品データを再描画して、全カテゴリの全表示フィルター・順位・理由・中央値・3つの選び方・店頭比較・GA4送信をDOMで検証します。
APIを呼ばず画面だけ生成する場合は `python scripts/build_site.py --reuse-data`。取得日時は既存データのままです。
通常の本番ビルドは引き続きAPIから取得します。本番Actionsは新しく取得したデータに対して `PET_COST_TEST_SITE=1 npm test` を実行し、品質監査後に公開します。
