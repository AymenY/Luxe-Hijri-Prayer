import Toybox.ActivityMonitor;
import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.System;
import Toybox.Time;
import Toybox.WatchUi;

// Luxe Hijri Prayer watch face for the fenix 7X Pro (280 x 280, 64-colour MIP).
//
// Update strategy
//  * onUpdate() (every second after a wrist raise, once per minute in low power) draws the
//    complete dial except the seconds hand into a full-screen buffered bitmap, copies it to
//    the screen and draws the seconds hand on top.
//  * onPartialUpdate() (every second in low power) only restores the area covered by the
//    previous seconds hand from the buffer and draws the new hand, clipped to the union of
//    both bounding boxes, to stay inside the watch-face power budget.
//  * If the system reports that the budget was exceeded, or the user chose "Only after wrist
//    raise", the seconds hand is hidden in low power instead of freezing.
// tools/face.py mirrors this drawing code for the reference previews.
class LuxeHijriPrayerView extends WatchUi.WatchFace {

    hidden var mSettings as LuxeSettings;
    hidden var mSchedule as PrayerSchedule;
    hidden var mColors as Array<Number> = [] as Array<Number>;
    hidden var mBgOps as Array? = null;

    hidden var mFontXXS;
    hidden var mFontXS;
    hidden var mFontS;
    hidden var mFontM;
    hidden var mFontL;
    hidden var mFontAyah;

    hidden var mDays as Array<String> = [];
    hidden var mMonths as Array<String> = [];
    hidden var mHijriMonths as Array<String> = [];
    hidden var mPrayerNames as Array = [];
    hidden var mUnits as Array<String> = [];   // KCAL, %, KM, MI
    hidden var mHijriSuffix as String = "";
    hidden var mSetLocation as String = "";

    hidden var mIndexPolys as Array = [];
    hidden var mTicks as Array = [];

    hidden var mBufferRef = null;   // Graphics.BufferedBitmapReference (API 4+)
    hidden var mBuffer = null;      // Graphics.BufferedBitmap fallback
    hidden var mSleeping as Boolean = false;
    hidden var mPartialAllowed as Boolean = true;
    hidden var mLastSecBox as Array<Number>? = null;

    function initialize() {
        WatchFace.initialize();
        mSettings = new LuxeSettings();
        mSchedule = new PrayerSchedule();
        mColors = Themes.PRESETS[0] as Array<Number>;
        loadStrings();
        buildDialGeometry();
        applySettings();
    }

    function onLayout(dc as Graphics.Dc) as Void {
        mFontXXS = WatchUi.loadResource(Rez.Fonts.LuxeXXS);
        mFontXS = WatchUi.loadResource(Rez.Fonts.LuxeXS);
        mFontS = WatchUi.loadResource(Rez.Fonts.LuxeS);
        mFontM = WatchUi.loadResource(Rez.Fonts.LuxeM);
        mFontL = WatchUi.loadResource(Rez.Fonts.LuxeL);
        mFontAyah = WatchUi.loadResource(Rez.Fonts.Ayah);
        createBuffer(dc.getWidth(), dc.getHeight());
    }

    // ------------------------------------------------------------------ settings
    function applySettings() as Void {
        mSettings.load();
        mColors = Themes.PRESETS[mSettings.preset] as Array<Number>;
        mBgOps = Backgrounds.load(mSettings.background);
        mSchedule.configure(mSettings.latitude, mSettings.longitude, mSettings.method,
                            mSettings.asrFactor, mSettings.highLat);
    }

    function disablePartialUpdates() as Void {
        mPartialAllowed = false;
    }

    hidden function loadStrings() as Void {
        mDays = [s(Rez.Strings.Day0), s(Rez.Strings.Day1), s(Rez.Strings.Day2), s(Rez.Strings.Day3),
                 s(Rez.Strings.Day4), s(Rez.Strings.Day5), s(Rez.Strings.Day6)];
        mMonths = [s(Rez.Strings.Month1), s(Rez.Strings.Month2), s(Rez.Strings.Month3), s(Rez.Strings.Month4),
                   s(Rez.Strings.Month5), s(Rez.Strings.Month6), s(Rez.Strings.Month7), s(Rez.Strings.Month8),
                   s(Rez.Strings.Month9), s(Rez.Strings.Month10), s(Rez.Strings.Month11), s(Rez.Strings.Month12)];
        mHijriMonths = [s(Rez.Strings.Hijri1), s(Rez.Strings.Hijri2), s(Rez.Strings.Hijri3), s(Rez.Strings.Hijri4),
                        s(Rez.Strings.Hijri5), s(Rez.Strings.Hijri6), s(Rez.Strings.Hijri7), s(Rez.Strings.Hijri8),
                        s(Rez.Strings.Hijri9), s(Rez.Strings.Hijri10), s(Rez.Strings.Hijri11), s(Rez.Strings.Hijri12)];
        mPrayerNames = [s(Rez.Strings.Prayer0), null, s(Rez.Strings.Prayer2), s(Rez.Strings.Prayer3), null,
                        s(Rez.Strings.Prayer5), s(Rez.Strings.Prayer6)];
        mUnits = [s(Rez.Strings.LabelCalories), s(Rez.Strings.LabelBattery), s(Rez.Strings.LabelKm),
                  s(Rez.Strings.LabelMi)];
        mHijriSuffix = s(Rez.Strings.HijriSuffix);
        mSetLocation = s(Rez.Strings.SetLocation);
    }

    hidden function s(id) as String {
        return WatchUi.loadResource(id) as String;
    }

    // ------------------------------------------------------------------ sleep / power
    function onEnterSleep() as Void {
        mSleeping = true;
        WatchUi.requestUpdate();
    }

    function onExitSleep() as Void {
        mSleeping = false;
        WatchUi.requestUpdate();
    }

    hidden function showSeconds() as Boolean {
        return !mSleeping || (mSettings.secondsAlways && mPartialAllowed);
    }

    // ------------------------------------------------------------------ buffer
    hidden function createBuffer(w as Number, h as Number) as Void {
        if (Graphics has :createBufferedBitmap) {
            mBufferRef = Graphics.createBufferedBitmap({:width => w, :height => h});
        } else {
            mBuffer = new Graphics.BufferedBitmap({:width => w, :height => h});
        }
    }

    hidden function getBuffer() {
        if (mBufferRef != null) {
            return mBufferRef.get();
        }
        return mBuffer;
    }

    // ------------------------------------------------------------------ updates
    function onUpdate(dc as Graphics.Dc) as Void {
        var now = Time.now().value();
        var clock = System.getClockTime();
        var buf = getBuffer();
        if (buf == null) {
            // The graphics pool may have reclaimed the buffer: recreate it once.
            createBuffer(dc.getWidth(), dc.getHeight());
            buf = getBuffer();
        }
        if (buf != null) {
            drawDial(buf.getDc(), now, clock);
            dc.drawBitmap(0, 0, buf);
        } else {
            drawDial(dc, now, clock);
        }
        mLastSecBox = null;
        if (showSeconds()) {
            setAntiAlias(dc);
            drawSecondsHand(dc, clock.sec);
            mLastSecBox = secondsBox(clock.sec);
        }
    }

    function onPartialUpdate(dc as Graphics.Dc) as Void {
        if (!mPartialAllowed || !mSettings.secondsAlways) {
            return;
        }
        var buf = getBuffer();
        if (buf == null) {
            return;
        }
        var sec = System.getClockTime().sec;
        var box = secondsBox(sec);
        var clip = box;
        var last = mLastSecBox;
        if (last != null) {
            var x0 = (last[0] < box[0]) ? last[0] : box[0];
            var y0 = (last[1] < box[1]) ? last[1] : box[1];
            var x1 = (last[0] + last[2] > box[0] + box[2]) ? last[0] + last[2] : box[0] + box[2];
            var y1 = (last[1] + last[3] > box[1] + box[3]) ? last[1] + last[3] : box[1] + box[3];
            clip = [x0, y0, x1 - x0, y1 - y0];
        }
        dc.setClip(clip[0], clip[1], clip[2], clip[3]);
        dc.drawBitmap(0, 0, buf);
        setAntiAlias(dc);
        drawSecondsHand(dc, sec);
        dc.clearClip();
        mLastSecBox = box;
    }

    hidden function setAntiAlias(dc as Graphics.Dc) as Void {
        if (dc has :setAntiAlias) {
            dc.setAntiAlias(true);
        }
    }

    // ------------------------------------------------------------------ dial
    hidden function drawDial(dc as Graphics.Dc, now as Number, clock as System.ClockTime) as Void {
        var c = mColors;
        setAntiAlias(dc);
        dc.setColor(c[Themes.BG], c[Themes.BG]);
        dc.clear();
        var bg = mBgOps;
        if (bg != null) {
            Backgrounds.draw(dc, bg, c);
        }
        drawChapterRing(dc);

        var day = CivilDate.localEpochDay(now, clock.timeZoneOffset);
        drawAyah(dc, clock.min);
        drawDates(dc, day);

        var info = ActivityMonitor.getInfo();
        var g = mSettings.gauges;
        drawGauge(dc, Layout.CX - Layout.GAUGE_DX, Layout.GAUGE_TOP_Y, g[0], info);
        drawGauge(dc, Layout.CX + Layout.GAUGE_DX, Layout.GAUGE_TOP_Y, g[1], info);
        drawGauge(dc, Layout.CX - Layout.GAUGE_DX, Layout.GAUGE_BOT_Y, g[2], info);
        drawGauge(dc, Layout.CX + Layout.GAUGE_DX, Layout.GAUGE_BOT_Y, g[3], info);

        drawPrayers(dc, now, clock);
        drawHourMinuteHands(dc, clock);
    }

    // Static dial geometry (minute track and hour indices) computed once.
    hidden function buildDialGeometry() as Void {
        mTicks = [];
        for (var i = 0; i < 60; i++) {
            if (i % 5 != 0) {
                var a = i * Math.PI / 30.0;
                mTicks.add([polar(Layout.TRACK_R_IN, a, 0), polar(Layout.TRACK_R_OUT, a, 0)]);
            }
        }
        mIndexPolys = [];
        for (var h = 1; h < 12; h++) {
            var a = h * Math.PI / 6.0;
            if (h == 3 || h == 9) {
                mIndexPolys.add(rotatePoly([[-2.5, -Layout.IDX_CARD_R_IN], [2.5, -Layout.IDX_CARD_R_IN],
                                            [2.5, -Layout.IDX_R_OUT], [-2.5, -Layout.IDX_R_OUT]], a));
            } else if (h != 6) {
                mIndexPolys.add(rotatePoly([[-1.5, -Layout.IDX_R_IN], [1.5, -Layout.IDX_R_IN],
                                            [Layout.IDX_W, -Layout.IDX_R_OUT], [-Layout.IDX_W, -Layout.IDX_R_OUT]], a));
            }
        }
        // 12 o'clock: two batons
        var g = Layout.IDX_12_GAP;
        mIndexPolys.add(rotatePoly([[-g - 2, -Layout.IDX_CARD_R_IN], [-g + 2, -Layout.IDX_CARD_R_IN],
                                    [-g + 2, -Layout.IDX_R_OUT], [-g - 2, -Layout.IDX_R_OUT]], 0.0));
        mIndexPolys.add(rotatePoly([[g - 2, -Layout.IDX_CARD_R_IN], [g + 2, -Layout.IDX_CARD_R_IN],
                                    [g + 2, -Layout.IDX_R_OUT], [g - 2, -Layout.IDX_R_OUT]], 0.0));
    }

    hidden function drawChapterRing(dc as Graphics.Dc) as Void {
        var c = mColors;
        dc.setPenWidth(1);
        dc.setColor(c[Themes.GOLD_DK], Graphics.COLOR_TRANSPARENT);
        for (var i = 0; i < mTicks.size(); i++) {
            var t = mTicks[i] as Array;
            var p0 = t[0] as Array<Number>;
            var p1 = t[1] as Array<Number>;
            dc.drawLine(p0[0], p0[1], p1[0], p1[1]);
        }
        dc.drawCircle(Layout.CX, Layout.CY, Layout.TRACK_R_OUT + 1);
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        for (var i = 0; i < mIndexPolys.size(); i++) {
            dc.fillPolygon(mIndexPolys[i] as Array);
        }
        // 6 o'clock: 8-point star (two overlapping squares) with a dark centre
        var x = Layout.CX;
        var y = Layout.STAR6_Y;
        var r = Layout.STAR6_R;
        var d = (r * 0.7071 + 0.5).toNumber();
        dc.fillPolygon([[x, y - r], [x + r, y], [x, y + r], [x - r, y]]);
        dc.fillPolygon([[x - d, y - d], [x + d, y - d], [x + d, y + d], [x - d, y + d]]);
        dc.setColor(c[Themes.BG], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(x, y, 2);
    }

    hidden function drawAyah(dc as Graphics.Dc, minute as Number) as Void {
        var a = mSettings.ayah;
        if (a == LuxeSettings.AYAH_NONE) {
            return;
        }
        // glyph "1".."7"; Al-Ikhlas alternates verses 1-2 ("6") and 3-4 ("8") every minute
        var code = (a + 1).toString();
        if (a == 5 && minute % 2 == 1) {
            code = "8";
        }
        dc.setColor(mColors[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.drawText(Layout.CX, Layout.AYAH_Y, mFontAyah, code,
                    Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    hidden function drawDates(dc as Graphics.Dc, day as Number) as Void {
        var c = mColors;
        var ymd = CivilDate.fromDays(day);
        var rest = ymd[2].toString() + " " + mMonths[ymd[1] - 1] + " " + ymd[0].toString();
        drawTwoTone(dc, Layout.CX, Layout.GREG_Y, mFontS, mDays[CivilDate.dayOfWeek(day)], c[Themes.ACCENT],
                    rest, c[Themes.TEXT]);

        var h = HijriCalendar.forEpochDay(day, mSettings.hijriCorrection);
        var hijri = h[2].toString() + " " + mHijriMonths[h[1] - 1] + " " + h[0].toString() + " " + mHijriSuffix;
        dc.setColor(c[Themes.ACCENT2], Graphics.COLOR_TRANSPARENT);
        dc.drawText(Layout.CX, Layout.HIJRI_Y, mFontS, hijri,
                    Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    // Draws "a b" centred on x with two colours.
    hidden function drawTwoTone(dc as Graphics.Dc, x as Number, y as Number, font, a as String, colA as Number,
                                b as String, colB as Number) as Void {
        var wa = dc.getTextWidthInPixels(a, font);
        var wb = dc.getTextWidthInPixels(b, font);
        var sp = dc.getTextWidthInPixels(" ", font);
        var x0 = x - (wa + sp + wb) / 2;
        var j = Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER;
        dc.setColor(colA, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x0, y, font, a, j);
        dc.setColor(colB, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x0 + wa + sp, y, font, b, j);
    }

    // ------------------------------------------------------------------ gauges
    hidden function drawGauge(dc as Graphics.Dc, x as Number, y as Number, source as Number,
                              info as ActivityMonitor.Info?) as Void {
        var c = mColors;
        var r = Layout.GAUGE_R;
        dc.setColor(c[Themes.PLATE], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(x, y, Layout.GAUGE_DISC_R);
        dc.setPenWidth(Layout.GAUGE_PEN);
        dc.setColor(c[Themes.TRACK], Graphics.COLOR_TRANSPARENT);
        dc.drawArc(x, y, r, Graphics.ARC_CLOCKWISE, 225, 315);

        var data = DataFields.read(source, info);
        var value = data[0];
        var progress = data[1];
        var flag = data[2] as Number;
        if (progress != null) {
            var p = progress as Float;
            if (p > 1.0) {
                p = 1.0;
            }
            var sweep = (270.0 * p).toNumber();
            if (sweep >= 2) {
                var end = 225 - sweep;
                if (end < 0) {
                    end += 360;
                }
                var warn = (source == DataFields.BATTERY && flag == 1);
                dc.setColor(warn ? c[Themes.WARN] : c[Themes.ACCENT], Graphics.COLOR_TRANSPARENT);
                dc.drawArc(x, y, r, Graphics.ARC_CLOCKWISE, 225, end);
            }
        }
        dc.setPenWidth(1);

        var color = c[Themes.TEXT];
        if (value == null) {
            value = "--";
            color = c[Themes.DIM];
        } else if (flag == 1) {
            color = (source == DataFields.BATTERY) ? c[Themes.WARN] : c[Themes.DIM];
        }
        // Battery uses the large font; any value wider than the ring interior steps down.
        var font = (source == DataFields.BATTERY) ? mFontL : mFontM;
        var inner = 2 * (r - Layout.GAUGE_PEN / 2) - 2;
        if (dc.getTextWidthInPixels(value as String, font) > inner) {
            font = mFontM;
            if (dc.getTextWidthInPixels(value as String, font) > inner) {
                font = mFontS;
            }
        }
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, y + Layout.GAUGE_VALUE_DY, font, value as String,
                    Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);

        dc.setColor(c[Themes.ACCENT2], Graphics.COLOR_TRANSPARENT);
        drawGaugeIcon(dc, x, y + Layout.GAUGE_ICON_DY, source);
    }

    // Unit or icon in the open bottom of the gauge ring (about 14 x 10 px).
    hidden function drawGaugeIcon(dc as Graphics.Dc, x as Number, y as Number, source as Number) as Void {
        var unit = null;
        if (source == DataFields.CALORIES) {
            unit = mUnits[0];
        } else if (source == DataFields.BATTERY) {
            unit = mUnits[1];
        } else if (source == DataFields.DISTANCE) {
            unit = (System.getDeviceSettings().distanceUnits == System.UNIT_STATUTE) ? mUnits[3] : mUnits[2];
        }
        if (unit != null) {
            dc.drawText(x, y, mFontXXS, unit as String, Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
            return;
        }
        if (source == DataFields.STEPS) {
            // two footprints
            dc.fillEllipse(x - 3, y + 1, 2, 4);
            dc.fillEllipse(x + 3, y - 1, 2, 4);
        } else if (source == DataFields.HEART) {
            dc.fillCircle(x - 2, y - 2, 3);
            dc.fillCircle(x + 2, y - 2, 3);
            dc.fillPolygon([[x - 5, y - 1], [x + 5, y - 1], [x, y + 5]]);
        } else if (source == DataFields.FLOORS) {
            dc.setPenWidth(2);
            dc.drawLine(x - 6, y + 4, x - 3, y + 4);
            dc.drawLine(x - 3, y + 4, x - 3, y + 1);
            dc.drawLine(x - 3, y + 1, x, y + 1);
            dc.drawLine(x, y + 1, x, y - 2);
            dc.drawLine(x, y - 2, x + 3, y - 2);
            dc.drawLine(x + 3, y - 2, x + 3, y - 5);
            dc.drawLine(x + 3, y - 5, x + 6, y - 5);
            dc.setPenWidth(1);
        } else if (source == DataFields.BODY_BATTERY) {
            // lightning bolt (two triangles)
            dc.fillPolygon([[x + 2, y - 6], [x - 3, y + 1], [x + 1, y + 1]]);
            dc.fillPolygon([[x - 1, y - 1], [x + 3, y - 1], [x - 2, y + 6]]);
        } else if (source == DataFields.STRESS) {
            dc.setPenWidth(2);
            dc.drawLine(x - 6, y + 1, x - 3, y - 3);
            dc.drawLine(x - 3, y - 3, x, y + 3);
            dc.drawLine(x, y + 3, x + 3, y - 3);
            dc.drawLine(x + 3, y - 3, x + 6, y + 1);
            dc.setPenWidth(1);
        }
    }

    // ------------------------------------------------------------------ prayers
    hidden function drawPrayers(dc as Graphics.Dc, now as Number, clock as System.ClockTime) as Void {
        var c = mColors;
        var vc = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        if (!mSettings.locationSet) {
            dc.setColor(c[Themes.DIM], Graphics.COLOR_TRANSPARENT);
            dc.drawText(Layout.CX, Layout.NEXT_Y, mFontM, mSetLocation, vc);
            return;
        }
        var offset = mSettings.tzManual ? mSettings.utcOffsetSeconds : clock.timeZoneOffset;
        mSchedule.update(now, offset);
        var next = mSchedule.next(now);
        var nextIdx = -1;
        var nextDay = 0;
        if (next != null) {
            nextIdx = next[0] as Number;
            nextDay = next[2] as Number;
        }
        var is24 = System.getDeviceSettings().is24Hour;

        // Schedule of the day the next prayer belongs to (tomorrow after Isha).
        var cell = Layout.SCHED_W / 5;
        var x0 = Layout.CX - Layout.SCHED_W / 2 + cell / 2;
        for (var k = 0; k < 5; k++) {
            var p = PrayerTimes.PRAYERS[k] as Number;
            var m = mSchedule.minutes(nextDay, p);
            var color = c[Themes.TEXT];
            if (p == nextIdx) {
                color = c[Themes.ACCENT2];
            } else if (next == null || (nextDay == 0 && p < nextIdx)) {
                color = c[Themes.DIM];
            }
            var x = x0 + k * cell;
            dc.setColor(color, Graphics.COLOR_TRANSPARENT);
            dc.drawText(x, Layout.SCHED_Y, mFontXS, formatTime(m, is24), vc);
            if (p == nextIdx) {
                dc.fillRectangle(x - 8, Layout.SCHED_Y + 8, 16, 2);
            }
        }

        // Next prayer name and countdown
        if (next != null) {
            var secs = ((next[1] as Long) - now).toNumber();
            drawTwoTone(dc, Layout.CX, Layout.NEXT_Y, mFontM, mPrayerNames[nextIdx] as String, c[Themes.ACCENT2],
                        countdown(secs), c[Themes.ACCENT]);
        } else {
            dc.setColor(c[Themes.DIM], Graphics.COLOR_TRANSPARENT);
            dc.drawText(Layout.CX, Layout.NEXT_Y, mFontM, "--", vc);
        }

        // Sunrise and sunset (today, location time)
        drawSun(dc, true, mSchedule.minutes(0, PrayerTimes.SUNRISE), is24);
        drawSun(dc, false, mSchedule.minutes(0, PrayerTimes.SUNSET), is24);
    }

    // Sunrise group left of the centre line, sunset group right of it.
    hidden function drawSun(dc as Graphics.Dc, rising as Boolean, minutes as Number?, is24 as Boolean) as Void {
        var c = mColors;
        var text = formatTime(minutes, is24);
        var tw = dc.getTextWidthInPixels(text, mFontXS);
        var gw = Layout.SUN_ICON_W + 3 + tw;
        var left = rising ? Layout.CX - Layout.SUN_GAP / 2 - gw : Layout.CX + Layout.SUN_GAP / 2;
        var y = Layout.SUN_Y;
        var ix = left + Layout.SUN_ICON_W / 2;
        // icon: half sun on the horizon with an up/down arrow
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(2);
        dc.drawArc(ix, y + 3, 4, Graphics.ARC_COUNTER_CLOCKWISE, 0, 180);
        dc.setPenWidth(1);
        dc.drawLine(ix - 6, y + 3, ix + 7, y + 3);
        if (rising) {
            dc.fillPolygon([[ix, y - 7], [ix - 3, y - 3], [ix + 3, y - 3]]);
        } else {
            dc.fillPolygon([[ix, y - 2], [ix - 3, y - 6], [ix + 3, y - 6]]);
        }
        dc.setColor(c[Themes.TEXT], Graphics.COLOR_TRANSPARENT);
        dc.drawText(left + Layout.SUN_ICON_W + 3, y, mFontXS, text,
                    Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    hidden function formatTime(minutes as Number?, is24 as Boolean) as String {
        if (minutes == null) {
            return "--:--";
        }
        var m = ((minutes % 1440) + 1440) % 1440;
        var h = m / 60;
        var mm = (m % 60).format("%02d");
        if (is24) {
            return h.format("%02d") + ":" + mm;
        }
        h = h % 12;
        if (h == 0) {
            h = 12;
        }
        return h.toString() + ":" + mm;
    }

    // Remaining time rounded up to the minute: "23m", "1h05", "10h59".
    hidden function countdown(secs as Number) as String {
        var mins = (secs + 59) / 60;
        if (mins < 60) {
            return mins.toString() + "m";
        }
        return (mins / 60).toString() + "h" + (mins % 60).format("%02d");
    }

    // ------------------------------------------------------------------ hands
    hidden function drawHourMinuteHands(dc as Graphics.Dc, clock as System.ClockTime) as Void {
        var c = mColors;
        var hourA = ((clock.hour % 12) + clock.min / 60.0) * Math.PI / 6.0;
        var minA = clock.min * Math.PI / 30.0;
        drawDauphine(dc, hourA, Layout.HOUR_LEN, Layout.HOUR_TAIL, Layout.HOUR_W);
        drawDauphine(dc, minA, Layout.MIN_LEN, Layout.MIN_TAIL, Layout.MIN_W);
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(Layout.CX, Layout.CY, Layout.CAP_R);
        dc.setColor(c[Themes.GOLD_DK], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(Layout.CX, Layout.CY, Layout.CAP_INNER_R);
    }

    // Faceted "dauphine" hand: gold left half, darker right half.
    hidden function drawDauphine(dc as Graphics.Dc, a as Numeric, len as Number, tail as Number, w as Number) as Void {
        var c = mColors;
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(rotatePoly([[0, -len], [-w, 0], [0, tail]], a));
        dc.setColor(c[Themes.GOLD_DK], Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(rotatePoly([[0, -len], [w, 0], [0, tail]], a));
    }

    hidden function drawSecondsHand(dc as Graphics.Dc, sec as Number) as Void {
        var c = mColors;
        var a = sec * Math.PI / 30.0;
        var tip = polar(Layout.SEC_LEN, a, 0);
        var tail = polar(-Layout.SEC_TAIL, a, 0);
        var weight = polar(-(Layout.SEC_TAIL - Layout.SEC_WEIGHT_R - 2), a, 0);
        dc.setColor(c[Themes.SECONDS], Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(Layout.SEC_PEN);
        dc.drawLine(tail[0], tail[1], tip[0], tip[1]);
        dc.setPenWidth(1);
        dc.fillCircle(weight[0], weight[1], Layout.SEC_WEIGHT_R);
        dc.fillCircle(Layout.CX, Layout.CY, Layout.CAP_R - 1);
        dc.setColor(c[Themes.PLATE], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(Layout.CX, Layout.CY, Layout.CAP_INNER_R);
    }

    // Bounding box [x, y, w, h] of everything drawSecondsHand() touches.
    hidden function secondsBox(sec as Number) as Array<Number> {
        var a = sec * Math.PI / 30.0;
        var tip = polar(Layout.SEC_LEN, a, 0);
        var tail = polar(-Layout.SEC_TAIL, a, 0);
        var m = Layout.SEC_WEIGHT_R + 3;
        var x0 = min3(tip[0], tail[0], Layout.CX - Layout.CAP_R) - m;
        var y0 = min3(tip[1], tail[1], Layout.CY - Layout.CAP_R) - m;
        var x1 = max3(tip[0], tail[0], Layout.CX + Layout.CAP_R) + m;
        var y1 = max3(tip[1], tail[1], Layout.CY + Layout.CAP_R) + m;
        return [x0, y0, x1 - x0, y1 - y0];
    }

    // ------------------------------------------------------------------ geometry helpers
    // Point at distance r from the centre in direction a (radians clockwise from 12 o'clock),
    // shifted sideways by `side` pixels.
    hidden function polar(r as Numeric, a as Numeric, side as Numeric) as Array<Number> {
        var sn = Math.sin(a);
        var cs = Math.cos(a);
        return [Math.round(Layout.CX + r * sn + side * cs).toNumber(),
                Math.round(Layout.CY - r * cs + side * sn).toNumber()];
    }

    // Rotates points given in hand coordinates (x right, y towards 12 o'clock is negative).
    hidden function rotatePoly(pts as Array, a as Numeric) as Array {
        var sn = Math.sin(a);
        var cs = Math.cos(a);
        var out = [];
        for (var i = 0; i < pts.size(); i++) {
            var p = pts[i] as Array;
            var x = p[0];
            var y = p[1];
            out.add([Math.round(Layout.CX + x * cs - y * sn).toNumber(),
                     Math.round(Layout.CY + x * sn + y * cs).toNumber()]);
        }
        return out;
    }

    hidden function min3(a as Number, b as Number, c as Number) as Number {
        var m = (a < b) ? a : b;
        return (m < c) ? m : c;
    }

    hidden function max3(a as Number, b as Number, c as Number) as Number {
        var m = (a > b) ? a : b;
        return (m > c) ? m : c;
    }
}
