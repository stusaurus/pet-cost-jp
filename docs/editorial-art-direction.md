# ペット暮らしの編集イラストシリーズ

## 判断と画風

既存の `assets/pet-home-morning.webp` は自然な犬猫の描写・朝の光・柔らかい質感が十分に整っているため維持。ボトルネックは `care_art()` の矩形・粒・トレーの簡易inline SVGだった。

上質な暮らし誌の編集イラストとして、デジタルガッシュ／色鉛筆の微細な質感、生成りの壁、明るい木の床、左上からの朝の光、セージ・淡いブルー・ウォームグレーを共有。犬猫は主画像の自然な体型と毛色を参照し、擬人化・大きな目・排泄シーン・商品広告・メーカー意匠の模倣を避けた。

## 資産と用途

正式資産は `assets/illustrations/` に18点、WebP・透過アルファ付きで保存。

- `scene-*.webp` 3点: ホームの3用品カード。犬猫と清潔な用品がある小さな暮らしの場面。
- `key-*.webp` 3点: 同じ原画から背景の余白を減らした自然な派生構図。カテゴリ上部専用。
- `filter-sheet-*.webp` 3点: 折り・厚み・不織布の柔らかさ。共通の描画尺度を保ち、相対的なサイズ差を表現。実寸図ではない。
- `filter-litter-*.webp` 6点: 紙の繊維、おからの細かな粒、木質、鉱物、混合、システム用の粒。形状・組成・性能を保証するものではない。
- `filter-system-*.webp` 3点: 汎用の本体と下部トレー・交換シートの関係を別構図で描く。メーカー別の形や寸法ではなく、対応ラベルは既存データで判断する。

生成は内蔵画像生成ツールを使用。3場面＋3アトラスの少数の原画から書き出した。猫砂は透過余白と画材感を確認するため1回修正。正式18資産の合計298,388 bytes（約291KiB）、最大29,972 bytes。ホームで追加する3画像は合計79,032 bytes。主画像247,258 bytesは変更なし。

原画の切り出し・縮小・WebP書き出しだけを `scripts/prepare_editorial_art.py` で実施。画素の描き足し、背景除去、色変更は行わず生成アルファを保持。寸法・出典・クロップ領域・実容量は `assets/illustrations/manifest.json` に記録。制作スクリプトはオフライン用で、通常のビルド・商品処理には実行されない。

## 実装の境界

`care_art()` は専用画像を返す関数へ変更し、ホーム・カテゴリ上部・条件カードの全呼び出しで簡易SVGを撤去。`icon()` のナビ、価格、数量、監査、単価、買い方、開始案内は操作記号として線画SVGを維持。

カードの配置、列数、余白、文言、選択ラベル、比較・使用量・楽天・GA4ロジックは変更なし。画像は空alt・aria-hiddenで既存の操作名を保ち、width/heightと4:3の比率を予約してCLSを抑える。未指定・将来追加条件には中立的なカテゴリ図版を使い、未知の素材を推測した絵にしない。

## プロンプトとモード

参照画像は既存主画像と承認したシーツ場面。すべて参照／編集対象の役割を明示。以下は最終制作に使用したプロンプトセット（内蔵ツールモード、CLI不使用）。

### scene_sheet

```text
Use case: illustration-story.
Asset type: finished editorial illustration for a small pet lifestyle category card, one single scene, landscape 4:3 composition.
Input Image 1 is a STYLE, PALETTE and ANIMAL reference only, NOT an edit target. Keep the existing original unchanged. Create a new complementary scene in the same home and morning light.
Primary request: An exquisite intimate vignette of a clean indoor dog toilet corner, an ivory and sage low-profile pet tray holding an unfolded disposable white absorbent pee pad, and the same naturally proportioned small tan-and-white terrier from the reference peacefully lying beside it, NOT on the pad. The pad is a recognisable quilted soft fabric-like nonwoven sheet with folded edges and pale blue backing. The dog is quietly relaxed, mouth closed, not mascot-like. A small neatly folded spare pad rests beside the tray. No elimination scene.
Style/medium: refined adult pet lifestyle magazine editorial illustration, visibly hand-painted digital gouache and finely restrained colored-pencil detail, soft imperfect contours, delicate paper grain, sophisticated tonal shading. More painterly than the reference, never photographic, never vector, never flat clip art.
Scene/backdrop: a little light oak floor and warm ivory plaster wall corner in the reference home, warm morning daylight from upper left. Only essentials; no plants or ornaments.
Composition: tray/pad and full dog occupy the central 85%, simple bold readable silhouettes at thumbnail scale, unobstructed clean pad, spacious quiet edges, the floor vignette softly feathers out to a genuinely transparent background. No rectangular backdrop boundary.
Palette: warm ivory, sage green, pale dusty blue, warm gray, restrained honey-brown dog, subtle mustard highlights. Low saturation; no heavy outlines, no gradients as graphic effects.
Constraints: natural canine anatomy, four plausible legs, believable tray and fabric. No person, no text, logos, brands, packaging, watermark, symbols, arrows, paw decorations, cartoons or 3D render. Premium finished commissioned illustration. Genuine transparent canvas around the vignette.
```

### scene_litter

```text
Use case: illustration-story. Asset type: finished small editorial pet lifestyle category vignette, landscape 4:3. Input Image 1 is the existing hero STYLE/ANIMAL reference; Image 2 is the approved companion vignette STYLE/MATERIAL/LIGHT reference. These are reference-only, not edit targets. Match their warm morning light from upper left, light oak floor, ivory wall, soft digital gouache and colored pencil microtexture. Same home, same gray-white naturally proportioned cat as the hero; restrained warm ivory, sage green, pale dusty blue, warm gray, honey wood palette. Premium adult lifestyle magazine illustration, visible gentle brushwork and imperfect contours; not photo, vector, flat icon, cartoon, mascot or 3D. One coherent scene occupying central85%, designed readable at small thumbnail scale. Soft irregular vignette boundary, truly transparent canvas outside it. No people, text, logo, packaging, trademark, watermark, paws/stars/leaf decoration, excretion scene, giant eyes or exaggerated expressions. Primary request: a clean ordinary open cat litter tray, low warm-gray ceramic-like molded tray filled with soft ivory paper litter pellets, naturally living in a clean home corner. The same gray-white cat lies relaxed immediately beside the tray, full body and tail visible, paws outside it. A little wood floor and softly lit plaster wall only. Tray grain texture clearly visible, pale linen mat underneath tray, no scoop or catalog items. Distinguish ordinary filled litter tray from a double-deck system toilet. Animal anatomy believable. Make cat and tray balanced and legible with few objects.
```

### scene_system

```text
Use case: illustration-story. Asset type: finished small editorial pet lifestyle category vignette, landscape 4:3. Input Image 1 is the existing hero STYLE/ANIMAL reference; Image 2 is the approved companion vignette STYLE/MATERIAL/LIGHT reference. These are reference-only, not edit targets. Match their warm morning light from upper left, light oak floor, ivory wall, soft digital gouache and colored pencil microtexture. Same home, same gray-white naturally proportioned cat as the hero; restrained warm ivory, sage green, pale dusty blue, warm gray, honey wood palette. Premium adult lifestyle magazine illustration, visible gentle brushwork and imperfect contours; not photo, vector, flat icon, cartoon, mascot or 3D. One coherent scene occupying central85%, designed readable at small thumbnail scale. Soft irregular vignette boundary, truly transparent canvas outside it. No people, text, logo, packaging, trademark, watermark, paws/stars/leaf decoration, excretion scene, giant eyes or exaggerated expressions. Primary request: a clean generic double-deck cat system toilet with a top perforated tray containing a few natural beige pellets and a lower drawer pulled slightly forward so its clean soft white absorbent replacement sheet is subtly visible; a single folded spare white sheet beside the drawer. The same gray-white cat sits peacefully alongside, naturally alert, full body/tail, not using the toilet. Small light oak floor and ivory wall corner. Make the layered tray and lower replacement sheet recognisable without an exploded technical diagram. Generic unbranded design, never reproduce a commercial model; no packages. Peaceful natural morning light, honest illustrative concept rather than an advertisement.
```

### plate_sheet

```text
Use case: stylized-concept. Asset type: ONE coherent production illustration atlas for a pet lifestyle service's small condition-choice images. Input Image1 is a style/material/light reference ONLY, not an edit target. Match soft hand-painted digital gouache and colored-pencil paper grain, subtle natural outlines, delicate realistic material shading, the same refined warm morning light from upper left. Adult editorial illustration, NOT flat SVG, clip-art, cartoon, 3D or photograph. Warm ivory, sage, pale blue, warm gray, restrained mustard and natural wood hues, low saturation. Genuine transparent canvas, no opaque background, no panel frames, no text, digits, arrows, badges, logos, packages, trademarks or watermark. Each cell holds one clearly separate centred illustration with at least12% empty margin inside every cell so assets can be independently cropped; no objects cross between cells. Create a WIDE HORIZONTAL atlas of EXACTLY THREE equal-width cells in ONE ROW, left-to-right small regular pad, medium wide pad, large super-wide pad. Each shows one single clean disposable white quilted absorbent pet sheet in an identical three-quarter overhead perspective and COMMON SCALE, including a naturally slightly folded corner, pale blue backing edge, soft nonwoven cotton-like texture, fine quilting and realistic thickness. Not towels, cushions, pads in a stack or bound notebooks. The first pad occupies about45% of its cell width, the second about65%, the third about85%, so size difference is immediately clear. All fully visible; same shape proportions, same material, no dog or tray. Keep shadows very soft and contained. Avoid graphic rectangles: render actual flexible soft paper fabric edges and folds with exquisite detail. The three illustrations must be equally artistically finished. This is conceptual size comparison not an accurate dimension drawing.
```

### plate_litter

```text
Use case: stylized-concept. Asset type: ONE coherent production illustration atlas for a pet lifestyle service's small condition-choice images. Input Image1 is a style/material/light reference ONLY, not an edit target. Match soft hand-painted digital gouache and colored-pencil paper grain, subtle natural outlines, delicate realistic material shading, the same refined warm morning light from upper left. Adult editorial illustration, NOT flat SVG, clip-art, cartoon, 3D or photograph. Warm ivory, sage, pale blue, warm gray, restrained mustard and natural wood hues, low saturation. Genuine transparent canvas, no opaque background, no panel frames, no text, digits, arrows, badges, logos, packages, trademarks or watermark. Each cell holds one clearly separate centred illustration with at least12% empty margin inside every cell so assets can be independently cropped; no objects cross between cells. Create a LANDSCAPE 3-column × 2-row atlas of EXACTLY SIX separate little close-up still-life material studies, read left-to-right top row then bottom row. No bowls or trays; each is a small loose pile of a dozen or so pieces, with two larger detailed foreground pieces, common visual size and same overhead three-quarter viewpoint. TOP LEFT: recycled paper litter, fibrous ivory irregular short compressed paper cylinders with porous rough rolled paper fibers and broken ends; TOP MIDDLE: okara/soy pulp litter, warm creamy pale-yellow slender crumbly extruded pellets, finer granular texture, distinctly different from paper; TOP RIGHT: natural wood/hinoki pellets, amber tan short thick cylindrical pieces with visible compressed wood fibers and woody end grain. BOTTOM LEFT: mineral/bentonite litter, cool warm-gray irregular angular tiny granules, matte gritty stony texture, NOT large gemstones. BOTTOM MIDDLE: mixed-material litter, clearly separated combination of ivory paper fibers, tan woody pieces and gray mineral grit in one modest pile, no assumption of precise composition. BOTTOM RIGHT: litter for a system toilet, a modest cluster of coarse beige oval porous non-clumping pellets with visible tiny pores; represent generic intended use without material or compatibility claims. No flowers, beans as foods, plant leaves, scoops or pets. Clearly render six distinct tactile textures; each pile occupies the central75% of its own cell. Avoid simplistic geometric grains.
```

### plate_system

```text
Use case: stylized-concept. Asset type: ONE coherent production illustration atlas for a pet lifestyle service's small condition-choice images. Input Image1 is a style/material/light reference ONLY, not an edit target. Match soft hand-painted digital gouache and colored-pencil paper grain, subtle natural outlines, delicate realistic material shading, the same refined warm morning light from upper left. Adult editorial illustration, NOT flat SVG, clip-art, cartoon, 3D or photograph. Warm ivory, sage, pale blue, warm gray, restrained mustard and natural wood hues, low saturation. Genuine transparent canvas, no opaque background, no panel frames, no text, digits, arrows, badges, logos, packages, trademarks or watermark. Each cell holds one clearly separate centred illustration with at least12% empty margin inside every cell so assets can be independently cropped; no objects cross between cells. Create a WIDE HORIZONTAL atlas of EXACTLY THREE equal-width cells in ONE ROW. Three distinct editorial concept studies about matching a replacement absorbent SHEET to a GENERIC two-tier cat toilet BODY, NOT depictions of any manufacturer's model, package or brand. The labels identifying compatible series will be real HTML outside the art; NEVER draw commercial design differences or imply that the drawing establishes manufacturer compatibility. All three use the same unbranded ivory and muted sage neutral toilet body with upper perforated layer and lower removable clean pad drawer, no animals, no room. LEFT CELL: a gentle front-three-quarter view, lower tray partly pulled forward with a soft white quilted sheet sitting properly in it. MIDDLE CELL: a slightly more overhead opposite-three-quarter viewpoint, detached lower tray with white pad beside the generic body. RIGHT CELL: a small overhead study of one generic matching lower drawer and two softly folded spare white sheets beside it, top body subtly behind. Common visual scale and detail; each study occupies75% of its cell with soft contained shadows. All emphasize checking one's existing BODY for fit, not sheet sizing or guarantees. Fine paper-fabric pad folds, thickness, tactile matte body surface. No exploded diagram, arrows, numbers, manufacturer shapes, branding, colored coding or copied products.
```

### plate_litter_refinement

```text
Use case: style-transfer. Input Image1 is EDIT TARGET, a six-cell cat-litter material atlas. Input Image2 is STYLE reference only.
Change only the rendering medium and background of Image1: preserve EXACTLY six piles in the same 3-column ×2-row positions and order, their shapes, material identities and distinct sizes. They are top row paper fibrous ivory pellets / okara pale yellow crumbly pellets / tan woody pellets; bottom row gray mineral grit / mixed pile / beige porous system-toilet pellets.
Remove ALL large blurred backdrop gradients and vignette haze. Genuine fully transparent empty canvas around each pile and in the gutters. Only a tiny soft contained contact shadow, not a wide glow. No background color.
Redraw the surfaces as exquisite softly hand-painted editorial gouache and colored-pencil material studies matching Image2's fine dry brush and paper grain, less photographic, no 3D render, no heavy outlined flat shapes. Preserve tactile fibrous paper, finely crumbly okara, compressed wood fibers, small gray stony grains, and porous coarse pellets. Maintain the restrained warm ivory/ochre/sage/warm gray palette and warm upper-left daylight. No text, labels, digits, borders, symbols, food, pets or added objects. Keep every entire pile well inside its cell and leave transparent gutters so six assets can be cropped independently. Preserve this exact layout.
```

