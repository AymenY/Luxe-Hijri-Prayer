# Connect IQ Store listing

Status: **ready for review, not submitted.** The Store package (`.iq`) must be built with the
owner's permanent developer key (README, “Store package”). Screenshots in `store/` are reference
renders and must be replaced by real simulator or device screenshots before submission.

* App type: Watch face
* Supported devices: the 70 round colour watches with Connect IQ 4+ listed in `manifest.xml`
  (fēnix 7 / 8 / 9 / E and Pro models, epix 2, tactix, quatix, Enduro 3 / 4, Forerunner 165 / 170 /
  255 / 265 / 570 / 70 / 955 / 965 / 970, Venu 2 / 3 / 4, vívoactive 5 / 6, MARQ 2 / 3, Instinct
  AMOLED, D2, Descent, Approach). Older watches (Connect IQ 3, e.g. fēnix 6) are not supported.
* Languages: English, French
* Price: free (suggested)
* Category: Watch faces
* Permission: *Sensor history* (Body Battery and stress)

## English

**Title:** Luxe Hijri Prayer

**Short description:** Luxury analog watch face with prayer times, Hijri date, Moon and Quran verse.

**Description:**

Luxe Hijri Prayer is an analog watch face inspired by fine watchmaking and Islamic art, for
round Garmin displays (MIP and AMOLED).

* Next prayer with a live countdown, and the following prayer with its time
* Prayer names in Arabic or Latin script; 14 calculation methods, standard or Hanafi Asr,
  high-latitude rules, and a per-prayer adjustment (±30 min) to match your mosque
* Prayer times follow your position automatically (the watch's last GPS position) or a location
  you enter
* Hijri date in Arabic (Arabic or Indian digits) or in Latin script, with a ±2 day correction
* Moon dial: tonight's Moon, the age of the lunar month and the illuminated fraction
* 24-hour daylight / darkness ring with dawn and dusk, and the time left until sunset or sunrise
* A complete Quranic verse in Arabic, changing every hour (39 short verses), a fixed verse or none
* Four configurable complications: steps, heart rate, calories, battery, distance, floors,
  Body Battery, stress, active minutes, Moon, daylight
* Six styles, four backgrounds (mosque illustration, Islamic geometry, black marble, night sky),
  three fonts, Arabic or Indian dial numerals, hand styles and colours
* Settings on the watch (watch face → Customise) and in Garmin Connect
* Burn-in-safe always-on mode on AMOLED watches; seconds hand in low power on MIP watches

Prayer times are calculated astronomically on the watch and can differ by a few minutes from a
mosque timetable; use the adjustment settings to align them. The Hijri date is a calculated
(tabular) calendar and may differ by a day from local moon sighting; use the correction setting.

No weather, temperature, altitude or compass data is shown.

**Privacy:** the watch face works entirely offline. It does not collect or transmit any personal
data and makes no network requests. Your position is used only on the watch to compute prayer
times; it is stored in the watch-face settings on your watch (and in Garmin Connect if you edit
the settings there). Permission used: *Sensor history* (to display Body Battery and stress).

## Français

**Titre :** Luxe Hijri Prayer

**Description courte :** Cadran analogique de luxe : heures de prière, date hégirienne, lune et verset.

**Description :**

Luxe Hijri Prayer est un cadran analogique inspiré de la haute horlogerie et de l'art islamique,
pour les écrans ronds Garmin (MIP et AMOLED).

* Prochaine prière avec compte à rebours, et la prière suivante avec son heure
* Noms des prières en arabe ou en écriture latine ; 14 méthodes de calcul, Asr standard ou
  hanafite, règles des hautes latitudes, et un ajustement par prière (±30 min) pour coller à
  l'horaire de votre mosquée
* Les heures suivent automatiquement votre position (dernière position GPS de la montre) ou une
  position saisie
* Date hégirienne en arabe (chiffres arabes ou indiens) ou en écriture latine, correction ±2 jours
* Cadran lunaire : la Lune de ce soir, l'âge du mois lunaire et la fraction éclairée
* Anneau lumière / obscurité sur 24 h avec aube et crépuscule, et le temps restant avant le
  coucher ou le lever du soleil
* Un verset complet du Coran en arabe, qui change chaque heure (39 versets courts), un verset
  fixe ou aucun
* Quatre complications configurables : pas, fréquence cardiaque, calories, batterie, distance,
  étages, Body Battery, stress, minutes intensives, lune, lumière du jour
* Six styles, quatre arrière-plans (illustration de mosquée, géométrie islamique, marbre noir,
  ciel nocturne), trois polices, chiffres du cadran arabes ou indiens, styles et couleurs d'aiguilles
* Réglages sur la montre (cadran → Personnaliser) et dans Garmin Connect
* Mode toujours allumé protégé contre le marquage sur AMOLED ; trotteuse en basse consommation sur MIP

Les heures de prière sont calculées astronomiquement sur la montre et peuvent différer de
quelques minutes de l'horaire d'une mosquée ; les réglages d'ajustement permettent de les
aligner. La date hégirienne est un calendrier calculé (tabulaire) qui peut différer d'un jour de
l'observation locale du croissant ; utilisez le réglage de correction.

Aucune donnée météo, température, altitude ou boussole n'est affichée.

**Confidentialité :** le cadran fonctionne entièrement hors ligne. Il ne collecte ni ne transmet
aucune donnée personnelle et n'effectue aucune requête réseau. Votre position sert uniquement,
sur la montre, au calcul des heures de prière ; elle est enregistrée dans les réglages du cadran
(sur la montre, et dans Garmin Connect si vous y modifiez les réglages). Autorisation utilisée :
*historique des capteurs* (Body Battery et stress).

## Artwork

| File | Content | Status |
|---|---|---|
| `resources/drawables/launcher_icon.png` | launcher icon (crescent and star) | generated; the compiler rescales it per device |
| `store/store-icon-512.png` | 512 × 512 store icon | artwork, ready |
| `store/hero-1440x720.png` | hero banner | reference render, optional |
| `store/screenshot-*.png` | screenshots | **reference renders — replace with simulator or device screenshots** |

## Rights to check before submission

* Background illustration `tools/art-src/mosque-night.png`: supplied by the owner; publishing it
  requires the rights to it.
* Fonts: SIL Open Font License 1.1 (licences in `tools/fonts-src/`), compatible with distribution.
* Quranic text: Tanzil (CC BY 3.0, unmodified text); credit Tanzil in the Store description if
  required by the licence ("Quran text: Tanzil.net").
