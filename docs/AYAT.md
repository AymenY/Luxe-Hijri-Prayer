# Ayah library

Only **complete verses** are used (owner's requirement), chosen among short, well-known verses so that each fits on one line at a legible size (at least 13 px on a 280 px screen).

* Arabic source: Tanzil "quran-simple" text via github.com/fawazahmed0/quran-api (edition ara-quransimple), cross-checked letter-by-letter against Tanzil Uthmani 1.0.2 (md5 6aae945d556a1b28cfe682c0ea5ab518).
* French translation (documentation only, too small to show on the watch): Muhammad Hamidullah, via Tanzil (edition fra-muhammadhamidul); punctuation normalised.
* Every verse is shaped with HarfBuzz (Amiri Bold, SIL OFL) by `tools/build_assets.py` and stored as one glyph of the fonts Ayah0..Ayah4 (8 verses per font, only the font of the current verse is loaded). The reference under the verse (surah name and verse number) is in Arabic.
* Settings: *Ayah* = hourly rotation over the verses ticked in the settings (default: all), a fixed verse, or hidden. The rotation changes verse at every full hour.

| # | Reference | Arabic | Reference shown | Font px at 218 / 280 / 454 | French (Hamidullah) |
|---|---|---|---|---|---|
| 1 | Al-Fatiha 1:2 | الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ | الفاتحة: ٢ | 11 / 15 / 25 | Louange à Allah, Seigneur de l'univers |
| 2 | Al-Fatiha 1:4 | مَالِكِ يَوْمِ الدِّينِ | الفاتحة: ٤ | 11 / 16 / 25 | Maître du Jour de la rétribution |
| 3 | Al-Fatiha 1:5 | إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ | الفاتحة: ٥ | 10 / 13 / 22 | C'est Toi [Seul] que nous adorons, et c'est Toi [Seul] dont nous implorons secours |
| 4 | Al-Fatiha 1:6 | اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ | الفاتحة: ٦ | 10 / 13 / 23 | Guide-nous dans le droit chemin |
| 5 | Taha 20:25 | قَالَ رَبِّ اشْرَحْ لِي صَدْرِي | طه: ٢٥ | 11 / 15 / 25 | [Moïse] dit: «Seigneur, ouvre-moi ma poitrine |
| 6 | Taha 20:26 | وَيَسِّرْ لِي أَمْرِي | طه: ٢٦ | 11 / 15 / 25 | et facilite ma mission |
| 7 | Taha 20:27 | وَاحْلُلْ عُقْدَةً مِنْ لِسَانِي | طه: ٢٧ | 10 / 14 / 24 | et dénoue un nœud en ma langue |
| 8 | Taha 20:28 | يَفْقَهُوا قَوْلِي | طه: ٢٨ | 11 / 15 / 25 | afin qu'ils comprennent mes paroles |
| 9 | Al-Anbiya 21:107 | وَمَا أَرْسَلْنَاكَ إِلَّا رَحْمَةً لِلْعَالَمِينَ | الأنبياء: ١٠٧ | 11 / 14 / 23 | Et Nous ne t'avons envoyé qu'en miséricorde pour l'univers |
| 10 | Ar-Rahman 55:13 | فَبِأَيِّ آلَاءِ رَبِّكُمَا تُكَذِّبَانِ | الرحمن: ١٣ | 10 / 14 / 23 | Lequel donc des bienfaits de votre Seigneur nierez-vous |
| 11 | Ar-Rahman 55:26 | كُلُّ مَنْ عَلَيْهَا فَانٍ | الرحمن: ٢٦ | 9 / 13 / 21 | Tout ce qui est sur elle [la terre] doit disparaître |
| 12 | Al-A'la 87:1 | سَبِّحِ اسْمَ رَبِّكَ الْأَعْلَى | الأعلى: ١ | 10 / 14 / 23 | Glorifie le nom de ton Seigneur, le Très Haut |
| 13 | Al-Fajr 89:27 | يَا أَيَّتُهَا النَّفْسُ الْمُطْمَئِنَّةُ | الفجر: ٢٧ | 11 / 15 / 25 | «O toi, âme apaisée |
| 14 | Al-Fajr 89:28 | ارْجِعِي إِلَىٰ رَبِّكِ رَاضِيَةً مَرْضِيَّةً | الفجر: ٢٨ | 10 / 13 / 22 | retourne vers ton Seigneur, satisfaite et agréée |
| 15 | Ad-Duha 93:3 | مَا وَدَّعَكَ رَبُّكَ وَمَا قَلَىٰ | الضحى: ٣ | 10 / 15 / 25 | Ton Seigneur ne t'a ni abandonné, ni détesté |
| 16 | Ad-Duha 93:4 | وَلَلْآخِرَةُ خَيْرٌ لَكَ مِنَ الْأُولَىٰ | الضحى: ٤ | 10 / 14 / 22 | La vie dernière t'est, certes, meilleure que la vie présente |
| 17 | Ad-Duha 93:5 | وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ | الضحى: ٥ | 10 / 14 / 23 | Ton Seigneur t'accordera certes [Ses faveurs], et alors tu seras satisfait |
| 18 | Ad-Duha 93:11 | وَأَمَّا بِنِعْمَةِ رَبِّكَ فَحَدِّثْ | الضحى: ١١ | 11 / 15 / 25 | Et quant au bienfait de ton Seigneur, proclame-le |
| 19 | Ash-Sharh 94:5 | فَإِنَّ مَعَ الْعُسْرِ يُسْرًا | الشرح: ٥ | 10 / 14 / 24 | A côté de la difficulté est, certes, une facilité |
| 20 | Ash-Sharh 94:6 | إِنَّ مَعَ الْعُسْرِ يُسْرًا | الشرح: ٦ | 10 / 14 / 24 | A côté de la difficulté est, certes, une facilité |
| 21 | Ash-Sharh 94:7 | فَإِذَا فَرَغْتَ فَانْصَبْ | الشرح: ٧ | 12 / 17 / 27 | Quand tu te libères, donc, lève-toi |
| 22 | Ash-Sharh 94:8 | وَإِلَىٰ رَبِّكَ فَارْغَبْ | الشرح: ٨ | 10 / 13 / 22 | et à ton Seigneur aspire |
| 23 | Al-Alaq 96:1 | اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ | العلق: ١ | 9 / 13 / 22 | Lis, au nom de ton Seigneur qui a créé |
| 24 | Al-Qadr 97:1 | إِنَّا أَنْزَلْنَاهُ فِي لَيْلَةِ الْقَدْرِ | القدر: ١ | 10 / 14 / 24 | Nous l'avons certes, fait descendre (le Coran) pendant la nuit d'Al-Qadr |
| 25 | Al-Qadr 97:3 | لَيْلَةُ الْقَدْرِ خَيْرٌ مِنْ أَلْفِ شَهْرٍ | القدر: ٣ | 9 / 13 / 22 | La nuit d'Al-Qadr est meilleure que mille mois |
| 26 | Az-Zalzalah 99:7 | فَمَنْ يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًا يَرَهُ | الزلزلة: ٧ | 10 / 13 / 22 | Quiconque fait un bien fût-ce du poids d'un atome, le verra |
| 27 | Al-Asr 103:1 | وَالْعَصْرِ | العصر: ١ | 12 / 16 / 27 | Par le Temps |
| 28 | Al-Asr 103:2 | إِنَّ الْإِنْسَانَ لَفِي خُسْرٍ | العصر: ٢ | 10 / 14 / 23 | L'homme est certes, en perdition |
| 29 | Al-Kawthar 108:1 | إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ | الكوثر: ١ | 11 / 15 / 25 | Nous t'avons certes, accordé l'Abondance |
| 30 | Al-Kawthar 108:2 | فَصَلِّ لِرَبِّكَ وَانْحَرْ | الكوثر: ٢ | 11 / 16 / 26 | Accomplis la Salât pour ton Seigneur et sacrifie |
| 31 | An-Nasr 110:1 | إِذَا جَاءَ نَصْرُ اللَّهِ وَالْفَتْحُ | النصر: ١ | 11 / 15 / 25 | Lorsque vient le secours d'Allah ainsi que la victoire |
| 32 | Al-Ikhlas 112:1 | قُلْ هُوَ اللَّهُ أَحَدٌ | الإخلاص: ١ | 12 / 16 / 26 | Dis: «Il est Allah, Unique |
| 33 | Al-Ikhlas 112:2 | اللَّهُ الصَّمَدُ | الإخلاص: ٢ | 15 / 20 / 33 | Allah, Le Seul à être imploré pour ce que nous désirons |
| 34 | Al-Ikhlas 112:3 | لَمْ يَلِدْ وَلَمْ يُولَدْ | الإخلاص: ٣ | 11 / 15 / 25 | Il n'a jamais engendré, n'a pas été engendré non plus |
| 35 | Al-Ikhlas 112:4 | وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ | الإخلاص: ٤ | 12 / 16 / 27 | Et nul n'est égal à Lui» |
| 36 | Al-Falaq 113:1 | قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ | الفلق: ١ | 11 / 15 / 25 | Dis: «Je cherche protection auprès du Seigneur de l'aube naissante |
| 37 | An-Nas 114:1 | قُلْ أَعُوذُ بِرَبِّ النَّاسِ | الناس: ١ | 11 / 15 / 25 | Dis: «Je cherche protection auprès du Seigneur des hommes |
| 38 | An-Nas 114:2 | مَلِكِ النَّاسِ | الناس: ٢ | 11 / 15 / 25 | Le Souverain des hommes |
| 39 | An-Nas 114:3 | إِلَٰهِ النَّاسِ | الناس: ٣ | 10 / 14 / 23 | Dieu des hommes |

Removed from the first version because they are too long to be shown complete: Taha 20:114, Al-Baqarah 2:286, Al-Imran 3:8, Al-Fath 48:4, Hud 11:88 (the specification listed them; the owner asked for complete verses only). The Basmala that one source prepends to the first verse of each surah is not part of those verses and is not shown.
