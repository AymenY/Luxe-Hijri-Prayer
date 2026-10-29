# Ayah selection

Arabic source: Tanzil "quran-simple" text via github.com/fawazahmed0/quran-api (edition ara-quransimple), cross-checked letter-by-letter against Tanzil Uthmani 1.0.2 (md5 6aae945d556a1b28cfe682c0ea5ab518).

French translation: Muhammad Hamidullah, via Tanzil (edition fra-muhammadhamidul); punctuation normalised. The translation is documentation only: at watch size it would be about 6 px tall, so the dial shows the Arabic text and the reference.

Each entry is rendered with Amiri Bold (SIL OFL), shaped with HarfBuzz/raqm by `tools/build_assets.py`, and stored as one glyph of the custom font `ayah.fnt` — one font per screen size. The watch draws it in the colour of the selected style, inside the cartouche at the bottom of the dial, with the reference underneath. The glyph size is the largest that fits the cartouche on that screen.

| Setting | Reference | Arabic shown on the watch | Font px at 218 / 280 / 454 | French (Hamidullah) |
|---|---|---|---|---|
| 1 | Taha 20:114 (excerpt) | وَقُل رَّبِّ زِدْنِي عِلْمًا | 11 / 14 / 24 | « Ô mon Seigneur, accroît mes connaissances ! » |
| 2 | Al-Inshirah 94:5 | فَإِنَّ مَعَ الْعُسْرِ يُسْرًا | 11 / 14 / 24 | « À côté de la difficulté est, certes, une facilité. » |
| 3 | Al-Baqarah 2:286 (excerpt) | لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا | 11 / 14 / 23 | « Allah n'impose à aucune âme une charge supérieure à sa capacité. » |
| 4 | Al-Imran 3:8 (excerpt) | رَبَّنَا لَا تُزِغْ قُلُوبَنَا | 12 / 15 / 25 | « Seigneur ! Ne laisse pas dévier nos cœurs » |
| 5 | Al-Fath 48:4 (excerpt) | هُوَ الَّذِي أَنْزَلَ السَّكِينَةَ | 12 / 15 / 25 | « C'est Lui qui a fait descendre la quiétude » |
| 6 (minute ≡ 0 mod 4) | Al-Ikhlas 112:1 | قُلْ هُوَ اللَّهُ أَحَدٌ | 12 / 16 / 26 | « Dis : Il est Allah, Unique. » |
| 6 (≡ 1) | Al-Ikhlas 112:2 | اللَّهُ الصَّمَدُ | 16 / 20 / 33 | « Allah, Le Seul à être imploré pour ce que nous désirons. » |
| 6 (≡ 2) | Al-Ikhlas 112:3 | لَمْ يَلِدْ وَلَمْ يُولَدْ | 12 / 15 / 25 | « Il n'a jamais engendré, n'a pas été engendré non plus. » |
| 6 (≡ 3) | Al-Ikhlas 112:4 | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | 13 / 16 / 27 | « Et nul n'est égal à Lui. » |
| 7 | Hud 11:88 (excerpt) | وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ | 11 / 14 / 23 | « Et ma réussite ne dépend que d'Allah. » |
| 8 | None (hide) | — | — | — |

Notes:

* 20:114 uses the orthography given in the project specification (وَقُل رَّبِّ — Uthmani spelling with the assimilation marks), which corresponds to Tanzil Uthmani words 15–18; the other entries use the Tanzil simple orthography.
* “Excerpt” means the opening phrase of the verse, copied verbatim from the source text; nothing was paraphrased or re-ordered.
* Al-Ikhlas is shown completely, one verse per minute (verses 1, 2, 3, 4 in turn); the change happens with the regular once-per-minute redraw, at no extra power cost.
* The Arabic text was cross-checked letter by letter between the two sources listed above (differences limited to Uthmani vs. simple spelling, and a Basmala prepended to 112:1 by one source, which is not part of the verse and is not displayed).
