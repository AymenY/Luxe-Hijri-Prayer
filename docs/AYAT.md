# Ayah selection

Arabic source: Tanzil "quran-simple" text via github.com/fawazahmed0/quran-api (edition ara-quransimple), cross-checked letter-by-letter against Tanzil Uthmani 1.0.2 (md5 6aae945d556a1b28cfe682c0ea5ab518).

French translation: Muhammad Hamidullah, via Tanzil (edition fra-muhammadhamidul); punctuation normalised. The French text is documentation only; it is not drawn on the watch.

Each entry is rendered with Amiri Bold (SIL OFL) and shaped with HarfBuzz/raqm by `tools/build_assets.py`, then stored as one glyph of the custom font `resources/fonts/ayah.fnt`; the watch draws it in the colour of the selected style. Glyph sizes are chosen automatically as the largest legible size that fits the round verse band.

| Setting | Reference | Arabic shown on the watch | Glyph | French (Hamidullah) |
|---|---|---|---|---|
| 1 | Taha 20:114 (excerpt) | وَقُل رَّبِّ زِدْنِي عِلْمًا | 117×33 px, 19 px font | « Ô mon Seigneur, accroît mes connaissances ! » |
| 2 | Al-Inshirah 94:5 | فَإِنَّ مَعَ الْعُسْرِ يُسْرًا | 116×36 px, 20 px font | « À côté de la difficulté est, certes, une facilité. » |
| 3 | Al-Baqarah 2:286 (excerpt) | لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا | 129×24 px, 14 px font | « Allah n'impose à aucune âme une charge supérieure à sa capacité. » |
| 4 | Al-Imran 3:8 (excerpt) | رَبَّنَا لَا تُزِغْ قُلُوبَنَا | 112×36 px, 21 px font | « Seigneur ! Ne laisse pas dévier nos cœurs » |
| 5 | Al-Fath 48:4 (excerpt) | هُوَ الَّذِي أَنْزَلَ السَّكِينَةَ | 127×30 px, 18 px font | « C'est Lui qui a fait descendre la quiétude » |
| 6 (even minutes) | Al-Ikhlas 112:1-4 | قُلْ هُوَ اللَّهُ أَحَدٌ / اللَّهُ الصَّمَدُ | 82×43 px, 17 px font | « Dis : Il est Allah, Unique. Allah, Le Seul à être imploré pour ce que nous désirons. Il n'a jamais engendré, n'a pas été engendré non plus. Et nul n'est égal à Lui. » |
| 7 | Hud 11:88 (excerpt) | وَمَا تَوْفِيقِي إِلَّا بِاللَّهِ | 113×34 px, 19 px font | « Et ma réussite ne dépend que d'Allah. » |
| 6 (odd minutes) | Al-Ikhlas 112:3-4 | لَمْ يَلِدْ وَلَمْ يُولَدْ / وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | 96×44 px, 14 px font | « Dis : Il est Allah, Unique. Allah, Le Seul à être imploré pour ce que nous désirons. Il n'a jamais engendré, n'a pas été engendré non plus. Et nul n'est égal à Lui. » |
| 8 | None (hide) | — | — | — |

Notes:

* 20:114 uses the orthography given in the project specification (وَقُل رَّبِّ — Uthmani spelling with the assimilation marks), which corresponds to Tanzil Uthmani words 15–18; the other entries use the Tanzil simple orthography.
* “Excerpt” means the opening phrase of the verse, copied verbatim from the source text; nothing was paraphrased or re-ordered.
* Al-Ikhlas is shown completely: verses 1–2 during even minutes and verses 3–4 during odd minutes (the change happens with the regular once-per-minute redraw, at no extra power cost).
* The Arabic text was cross-checked letter by letter between the two sources listed above (differences limited to Uthmani vs. simple spelling, and a Basmala prepended to 112:1 by one source, which is not part of the verse and is not displayed).
