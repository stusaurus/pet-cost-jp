# pet-cost-jp

うちで使えるペット用品を、うちの条件・使用量で比べるGitHub Pagesサイトです。サイズ・素材・トイレ本体を先に選び、その中で単価・今回の出費・買う量・持つ期間を比較します。

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

用品 → 「使っているサイズ・素材・本体は？」 → 条件内の最安と根拠 → TOP3と買い方 → 商品一覧の順に表示します。初回は条件を選ぶまで価格の結論を表示せず、次回は端末に保存した条件を復元します。素材を問わず見る操作は、猫砂の補助選択として残しています。

任意の「うちの使用量で見る」は、ペットシーツ＝枚/日、猫砂＝L/月、システムトイレシート＝枚/週。購入数量 ÷ 使用量から持つ期間、単価 × 使用量から30日分の費用を計算し、最安・TOP3・各買い方・全商品に反映します。1週間＝7日、1か月＝30日で統一し、週1枚・20枚・1,750円なら約20週間分 / 30日分約375円です。新しい袋を使い始めた場合の計算であり、現在の残量・交換頻度の推奨・将来の購入日を推定しません。

条件・使用量は `pet_cost_household_v1` としてlocalStorageに保存します。保存を利用できなくても比較は動作します。使用量は空欄で利用でき、消すと単価だけの表示へ戻ります。使用量の数値は新設GA4イベントへ送信しません。

買い方は「長く使って安く」「今日は出費を抑える」「買い足す回数を減らす」。店頭比較は、選んだ条件の商品を店で見つけた場合の補助機能です。トップの現在価格差は副次的な開閉欄に移し、猫砂の代表例は紙だけで比較します。
`assets/comparison.css` が共通スタイルで、生成HTMLにインライン化します。旧版の装飾CSSは撤去しました。
暮らしのデザインでは、生成り・セージを共通の基調とし、猫砂は土色、トイレシートは落ち着いた青緑で区別します。主画像は `assets/pet-home-morning.webp`。用品・素材の小さなSVGは装飾で、実寸や全機種適合を示しません。数値・単価バーは従来の計算に連動し、選択応答のみ170〜180ms、reduced-motionでは動きを止めます。
トップの3つの短い信頼表示から、比較基準を開けます。最安の数量式は常に表示し、詳しい判定方針は開閉欄に統合。品質やペットとの相性の保証、過去価格・値下げの主張はしません。GA4イベント名・パラメータはこのデザイン変更で追加・削除していません。
中央値は偶数件の場合、中央2件の平均です。送料別の商品は送料を加算せず、その旨を表示します。

既存の `homepage_editorial_click` / `daily_spotlight_click` も維持し、価格差欄のカテゴリ入口で両方を送ります。
新しい `comparison_angle_select` は選び方の変更を計測し、`angle_role=unit|total|bulk` と現在の条件・商品IDを送ります。
条件変更は既存 `comparison_filter` に結果件数・最安単価・中央値を追加。店頭比較の自動再計算ではイベントを再送しません。
`?test=1` で運営者検証の `operator_test=1` を付け、`?test=0` で解除できます。
`pet_category_select` は「何を使っていますか？」の入口、`pet_usage_change` は使用量の反映・解除を計測します。後者の値は `usage_period=day|week|month`、`usage_enabled`、カテゴリ・条件のみで、使用量そのものは含めません。復元・入力中・条件変更による再計算では重複送信しません。

```sh
python -m unittest discover -s tests -p 'test_*.py'
npm ci --ignore-scripts
npm test
python scripts/audit_products.py
```

`npm test` はコミット済みの商品データを再描画して、全カテゴリの全表示フィルター・順位・理由・中央値・3つの選び方・店頭比較・GA4送信をDOMで検証します。
APIを呼ばず画面だけ生成する場合は `python scripts/build_site.py --reuse-data`。取得日時は既存データのままです。
通常の本番ビルドは引き続きAPIから取得します。本番Actionsは新しく取得したデータに対して `PET_COST_TEST_SITE=1 npm test` を実行し、品質監査後に公開します。
