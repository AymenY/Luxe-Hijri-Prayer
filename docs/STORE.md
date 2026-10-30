# Connect IQ Store listing (draft)

Status: **not submitted.** The app has not been compiled yet (see `AUDIT.md`), so no `.iq`
package exists. Artwork in `store/` consists of reference renders and must be replaced by real
simulator/device screenshots before submission (the Store requires genuine screenshots).

* App type: Watch face
* Supported devices: round colour watches with Connect IQ 4+ (fēnix 7 / 7 Pro / 8, epix 2 / Pro,
  Enduro 3, Forerunner 165 / 255 / 265 / 955 / 965, Venu 2 / 3, vívoactive 5, MARQ 2); final list
  from `tools/update_products.py`
* Languages: English, French
* Price: free (suggested)
* Category: Watch faces

## English

**Title:** Luxe Hijri Prayer

**Short description:** Luxury analog watch face with prayer times, countdown and Hijri date.

**Description:**

Luxe Hijri Prayer is an analog-digital watch face inspired by fine mechanical watches and
Islamic geometric art, designed for round Garmin displays (MIP and AMOLED).

* Real analog clock with gold dauphine hands and a long seconds hand
* Next prayer with a live countdown, and the following prayer with its time (Fajr, Dhuhr, Asr, Maghrib, Isha)
* Sunrise and sunset times
* Gregorian date and Hijri date in Arabic script, with a −2…+2 day correction
* Four configurable gauges: steps, heart rate, calories, battery, distance, floors, Body Battery, stress
* Large battery percentage
* Six style presets: Luxury Blue, Royal Gold, Emerald Night, Burgundy Royale, Ice Silver, Stealth
* Four backgrounds: mosque and crescent, Islamic geometric pattern, black marble, night sky
* A complete Quranic verse in Arabic with its reference, changing every hour (39 short verses to choose from), a fixed verse or none
* Fully customisable: fonts, text, accent and seconds colours, hand styles, gauge sources and colours, Arabic or Latin Hijri date
* Mosque night scene under a pointed Islamic arch; burn-in safe always-on mode on AMOLED watches
* 14 calculation methods (Tunisia, MWL, ISNA, Egypt, Umm al-Qura, Karachi, Gulf, Kuwait,
  Qatar, Singapore, Turkey, France UOIF, Algeria, Morocco), standard or Hanafi Asr,
  high-latitude rules

Set your latitude and longitude in the watch-face settings (default: Djerba, Tunisia). Prayer
times are calculated astronomically on the watch and can differ by a few minutes from your
local mosque timetable. The Hijri date is a calculated (tabular) calendar and may differ by a
day from local moon sighting; use the correction setting to align it.

No weather, temperature, altitude or compass data is shown, by design.

**Privacy:** the watch face works entirely offline. It does not collect, store or transmit any
personal data. The coordinates you enter are stored only in the watch-face settings on your
watch and in Garmin Connect. Permission used: *Sensor history* (to display Body Battery and stress).

## Français

**Titre :** Luxe Hijri Prayer

**Description courte :** Cadran analogique de luxe avec heures de prière, compte à rebours et date hégirienne.

**Description :**

Luxe Hijri Prayer est un cadran analogique-numérique inspiré de la haute horlogerie et de l'art
géométrique islamique, conçu pour les écrans ronds Garmin (MIP et AMOLED).

* Véritable horloge analogique, aiguilles dauphine dorées et longue trotteuse
* Prochaine prière avec compte à rebours, et la prière suivante avec son heure (Fajr, Dhohr, Asr, Maghrib, Icha)
* Heures du lever et du coucher du soleil
* Date grégorienne et date hégirienne en écriture arabe, avec correction de −2 à +2 jours
* Quatre jauges configurables : pas, fréquence cardiaque, calories, batterie, distance, étages, Body Battery, stress
* Grand pourcentage de batterie
* Six styles : Luxury Blue, Royal Gold, Emerald Night, Burgundy Royale, Ice Silver, Stealth
* Quatre arrière-plans : mosquée et croissant, motif géométrique islamique, marbre noir, ciel nocturne
* Un verset complet du Coran en arabe avec sa référence, qui change chaque heure (39 versets courts au choix), un verset fixe ou aucun
* Entièrement personnalisable : polices, couleurs du texte, d'accent et de la trotteuse, styles d'aiguilles, données et couleurs des jauges, date hégirienne en arabe ou en latin
* Scène nocturne de mosquée sous un arc islamique ; mode toujours allumé protégé contre le marquage sur les montres AMOLED
* 14 méthodes de calcul (Tunisie, Ligue islamique mondiale, ISNA, Égypte, Umm al-Qura, Karachi,
  Golfe, Koweït, Qatar, Singapour, Turquie, France UOIF, Algérie, Maroc), Asr standard ou
  hanafite, règles des hautes latitudes

Indiquez votre latitude et votre longitude dans les réglages du cadran (par défaut : Djerba,
Tunisie). Les heures de prière sont calculées astronomiquement sur la montre et peuvent différer
de quelques minutes du calendrier de votre mosquée. La date hégirienne est un calendrier calculé
(tabulaire) qui peut différer d'un jour de l'observation locale du croissant ; utilisez le
réglage de correction pour l'ajuster.

Aucune donnée météo, température, altitude ou boussole n'est affichée, volontairement.

**Confidentialité :** le cadran fonctionne entièrement hors ligne. Il ne collecte, ne stocke et
ne transmet aucune donnée personnelle. Les coordonnées saisies restent dans les réglages du
cadran (montre et Garmin Connect). Autorisation utilisée : *historique des capteurs* (pour Body
Battery et stress).

## Artwork

| File | Content | Status |
|---|---|---|
| `resources/drawables/launcher_icon.png` | 40 × 40 launcher icon (crescent and star) | generated; the compiler rescales it if the device expects another size |
| `store/store-icon-512.png` | 512 × 512 store icon | reference render — check the size requested by the submission form |
| `store/hero-1440x720.png` | hero banner with three styles | reference render |
| `store/screenshot-1..6.png` | the six styles at 280 × 280 (one per device size is also expected by the Store) | **reference renders — replace with simulator screenshots** |
