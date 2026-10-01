# ペット暮らしイラスト制作

正式資産：`assets/living/`。組み込みimagegenで制作。CLI/APIは使用していない。原画を切り出し・縮小・WebP化し、透過アルファを保持。コードで作画・背景除去はしていない。`scripts/prepare_living_art.py` に原画ファイル名と切り出し範囲、`assets/living/manifest.json` に寸法・容量を記録。

同じ朝の光、生成り・セージ・淡青・木の色、自然な動物、柔らかな毛並みと布。世界観用の画像と小さなSVG操作記号を区別。旧素材図版は説明用として維持。

## 最終プロンプトセット

### hero

```text
Use case: illustration-story. Premium adult pet lifestyle editorial illustration, original art direction. Soft digital gouache with delicate colored pencil and textured paper, painterly natural edges, sophisticated tactile animal fur and fabrics, not vector clipart or 3D. Natural animal anatomy and small normal eyes, no smiles, anthropomorphism or mascots. Morning light from upper left. Restrained warm ivory, sage green, dusty blue, warm grey, beige, muted mustard. No text, numbers, brands, packaging, arrows, paw decorations, frame lines or watermark. Asset type: complete new website main visual, landscape 3:2. A naturally proportioned small tan and white dog and a grey-white cat relaxing together on a woven cream rug in a quiet refined oak-floored home. A clean feeding corner with two ceramic bowls, a folded washable throw and one sage rope ring and soft felt ball integrated naturally into the room, no catalog lineup. Soft window shadows, tidy negative space, warm life and curiosity. No humans, toilet activity, excessive plants or commercial products. The animals are the visual focus. Opaque finished painting.
```

### entry

```text
Use case: illustration-story. Premium adult pet lifestyle editorial illustration, original art direction. Soft digital gouache with delicate colored pencil and textured paper, painterly natural edges, sophisticated tactile animal fur and fabrics, not vector clipart or 3D. Natural animal anatomy and small normal eyes, no smiles, anthropomorphism or mascots. Morning light from upper left. Restrained warm ivory, sage green, dusty blue, warm grey, beige, muted mustard. No text, numbers, brands, packaging, arrows, paw decorations, frame lines or watermark. Asset type: TWO separate large selection illustrations in one horizontal 2-cell atlas on genuinely transparent background. Exactly TWO equal square cells, generous 12% empty margins. LEFT a naturally proportioned small tan-white dog seated in slight three-quarter view on tiny woven rug, attentive quiet expression. RIGHT a naturally proportioned grey-white domestic cat seated in slight three-quarter view on same rug texture, calmly curious. Entire bodies and tails intact, same scale of visual weight, no props or room backdrop. No objects cross cells. These are companion pets, not character stickers. Visible painted gouache brushwork and colored-pencil hatching, clearly an illustration, not a photograph.
```

### category

```text
Use case: illustration-story. Premium adult pet lifestyle editorial illustration, original art direction. Soft digital gouache with delicate colored pencil and textured paper, painterly natural edges, sophisticated tactile animal fur and fabrics, not vector clipart or 3D. Natural animal anatomy and small normal eyes, no smiles, anthropomorphism or mascots. Morning light from upper left. Restrained warm ivory, sage green, dusty blue, warm grey, beige, muted mustard. No text, numbers, brands, packaging, arrows, paw decorations, frame lines or watermark. Asset type: SEVEN finished small pet-lifestyle category vignettes in a transparent atlas of FOUR columns TWO rows with EIGHT equal square cells; final cell EMPTY. Each has 12% transparent margin, objects contained in its cell, same visual scale. Row1 left to right: dog and ivory kibble bowl with an unbranded plain paper storage bag; cat and a shallow sage kibble bowl with same plain bag; clean absorbent puppy pad on a tray with tan dog nearby; clean sandy litter tray with grey-white cat nearby. Row2 left to right: unbranded two-tier cat toilet with lower clean sheet drawer visible and cat; tan dog softly playing beside sage rope ring and ball; grey-white cat gently reaching toward a feather-free cloth teaser and felt ball; EMPTY cell. Small everyday scenes with tiny oak floor patches, no large backgrounds. Real folds and fabric texture, natural animals, not photorealistic. Each distinct complete vignette. Visible painted gouache brushwork and colored-pencil hatching, clearly an illustration, not a photograph.
```

### play

```text
Use case: illustration-story. Premium adult pet lifestyle editorial illustration, original art direction. Soft digital gouache with delicate colored pencil and textured paper, painterly natural edges, sophisticated tactile animal fur and fabrics, not vector clipart or 3D. Natural animal anatomy and small normal eyes, no smiles, anthropomorphism or mascots. Morning light from upper left. Restrained warm ivory, sage green, dusty blue, warm grey, beige, muted mustard. No text, numbers, brands, packaging, arrows, paw decorations, frame lines or watermark. Asset type: SIX small tactile play concepts, genuinely transparent THREE columns TWO rows atlas, equal square cells with 12% margin. Row1: sage woven rope chewing ring; dusty-blue soft ball with subtle natural shadow; two-ended fabric rope for playing together. Row2: ivory puzzle feeder board with 3 simple sliding lids and kibble wells, no complex mechanisms; feather-free felt fabric cat teaser with wooden handle and string neatly contained; taupe fabric tunnel with a felt ball near its opening. All objects are finished hand-painted editorial illustrations with detailed fabric/wood texture, not flat symbols. No animals or hands. No claim of safe sizes; all generic unbranded concepts. No motion lines or arrows. Visible painted gouache brushwork and colored-pencil hatching, clearly an illustration, not a photograph.
```

### ages

```text
Use case: illustration-story. Premium adult pet lifestyle editorial illustration, original art direction. Soft digital gouache with delicate colored pencil and textured paper, painterly natural edges, sophisticated tactile animal fur and fabrics, not vector clipart or 3D. Natural animal anatomy and small normal eyes, no smiles, anthropomorphism or mascots. Morning light from upper left. Restrained warm ivory, sage green, dusty blue, warm grey, beige, muted mustard. No text, numbers, brands, packaging, arrows, paw decorations, frame lines or watermark. A genuinely transparent atlas of SIX independent pet age illustrations, strict THREE columns TWO rows with12%empty margins inside each cell, no animal crossing a cell boundary. Row1: tan-white puppy full seated pose, tan-white adult dog bust portrait, tan-white senior dog bust portrait subtle grey muzzle. Row2: grey-white kitten full seated pose, grey-white adult cat bust portrait, grey-white senior cat bust portrait subtle mature expression. Original fine gouache paint and colored pencil, naturally proportioned, no background or other objects. This atlas has ONLY SIX illustrations and no third row.
```

### sizes

```text
Use case: illustration-story. Premium adult pet lifestyle editorial illustration, original art direction. Soft digital gouache with delicate colored pencil and textured paper, painterly natural edges, sophisticated tactile animal fur and fabrics, not vector clipart or 3D. Natural animal anatomy and small normal eyes, no smiles, anthropomorphism or mascots. Morning light from upper left. Restrained warm ivory, sage green, dusty blue, warm grey, beige, muted mustard. No text, numbers, brands, packaging, arrows, paw decorations, frame lines or watermark. A genuinely transparent horizontal THREE-cell atlas, exactly three fully separated full-body standing dogs on common baseline. LEFT a small short-haired terrier occupying50%cellheight; MIDDLE a medium shiba-like companion dog occupying65%cellheight; RIGHT a large retriever occupying80%cellheight. These differences are illustrative body-scale cues, not breed recommendations. Each dog's entire body/head/tail/paws inside its own cell with12%empty margin. No other animals, props or backdrop. Finished digital gouache and colored-pencil drawing.
```

