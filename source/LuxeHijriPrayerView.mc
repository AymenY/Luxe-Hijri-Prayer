import Toybox.ActivityMonitor;
import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Math;
import Toybox.System;
import Toybox.Time;
import Toybox.WatchUi;

// Luxe Hijri Prayer watch face for round colour Garmin watches (218 to 454 px, MIP and AMOLED).
//
// Geometry is defined for a 280 x 280 dial (source/Layout.mc) and scaled to the screen with
// p(); bitmap fonts come in one set per screen size (resource qualifiers).
//
// Update strategy
//  * The static layer (background art, arch scene, chapter ring, numerals, gauge recesses,
//    cartouches, fixed icons) is an HD bitmap rendered offline for each screen size, style and
//    background (tools/render_hd.py). If it cannot be loaded, a vector version is drawn once
//    into a buffered bitmap instead and redrawn only after a settings change.
//  * onUpdate() copies the static layer, draws the live content (dates, gauges, prayers,
//    Ayah, hour/minute hands) and then the seconds hand.
//  * MIP screens: the frame without the seconds hand is also kept in a second buffer, so that
//    onPartialUpdate() (every second in low power) only restores the area under the previous
//    seconds hand and draws the new one, clipped. If the system reports the power budget was
//    exceeded, or the user chose "Only after wrist raise", the seconds hand is hidden in low
//    power instead of freezing.
//  * AMOLED screens (burn-in protection): in always-on mode only thin hour/minute hands and four
//    dots are drawn on black, shifted every minute; nothing else stays lit.
// tools/face.py mirrors this drawing code for the reference previews.
class LuxeHijriPrayerView extends WatchUi.WatchFace {

    hidden var mSettings as LuxeSettings;
    hidden var mSchedule as PrayerSchedule;
    hidden var mColors as Array<Number> = [] as Array<Number>;
    hidden var mMulticolor as Boolean = false;
    hidden var mBgOps as Array? = null;
    hidden var mFrameOps as Array? = null;
    hidden var mDial = null;        // HD static layer (BitmapResource) or null

    hidden var mFontNum;
    hidden var mFontL;
    hidden var mFontM;
    hidden var mFontS;
    hidden var mFontXS;
    hidden var mFontAyah;

    hidden var mDays as Array<String> = [];
    hidden var mMonths as Array<String> = [];
    hidden var mHijriMonths as Array<String> = [];
    hidden var mPrayerNames as Array = [];
    hidden var mLabels as Array<String> = [];
    hidden var mLabelMi as String = "MI";
    hidden var mAyahRefs as Array<String> = [];
    hidden var mHijriSuffix as String = "";
    hidden var mSetLocation as String = "";
    hidden var mSetLocation2 as String = "";

    hidden var mSize as Number = 280;
    hidden var mK as Float = 1.0;
    hidden var mBurnIn as Boolean = false;

    hidden var mStaticRef = null;   // static layer (BufferedBitmapReference or BufferedBitmap)
    hidden var mFrameRef = null;    // full frame without seconds hand (MIP only)
    hidden var mStaticDirty as Boolean = true;
    hidden var mSleeping as Boolean = false;
    hidden var mPartialAllowed as Boolean = true;
    hidden var mLastSecBox as Array<Number>? = null;

    function initialize() {
        WatchFace.initialize();
        mSettings = new LuxeSettings();
        mSchedule = new PrayerSchedule();
        mColors = Themes.PRESETS[0] as Array<Number>;
        var ds = System.getDeviceSettings();
        mBurnIn = (ds has :requiresBurnInProtection) && ds.requiresBurnInProtection;
        loadStrings();
        applySettings();
    }

    function onLayout(dc as Graphics.Dc) as Void {
        mSize = dc.getWidth();
        mK = mSize / 280.0;
        mFontNum = WatchUi.loadResource(Rez.Fonts.LuxeNum);
        mFontL = WatchUi.loadResource(Rez.Fonts.LuxeL);
        mFontM = WatchUi.loadResource(Rez.Fonts.LuxeM);
        mFontS = WatchUi.loadResource(Rez.Fonts.LuxeS);
        mFontXS = WatchUi.loadResource(Rez.Fonts.LuxeXS);
        mFontAyah = WatchUi.loadResource(Rez.Fonts.Ayah);
        if (mDial == null) {
            mStaticRef = createBuffer(dc.getWidth(), dc.getHeight());
        }
        if (!mBurnIn) {
            mFrameRef = createBuffer(dc.getWidth(), dc.getHeight());
        }
        mStaticDirty = true;
    }

    // ------------------------------------------------------------------ settings
    function applySettings() as Void {
        mSettings.load();
        mColors = Themes.PRESETS[mSettings.preset] as Array<Number>;
        mMulticolor = Themes.MULTICOLOR[mSettings.preset] as Boolean;
        mDial = null;
        mDial = loadDial(mSettings.preset, mSettings.background);
        if (mDial == null) {
            mBgOps = Backgrounds.load(mSettings.background);
            mFrameOps = Backgrounds.loadFrame();
        } else {
            mBgOps = null;
            mFrameOps = null;
            mStaticRef = null;
        }
        mSchedule.configure(mSettings.latitude, mSettings.longitude, mSettings.method,
                            mSettings.asrFactor, mSettings.highLat);
        mStaticDirty = true;
    }

    // HD dial for style s and background b; null if it cannot be loaded (e.g. out of memory).
    hidden function loadDial(st as Number, bg as Number) {
        var ids = [Rez.Drawables.Dial00, Rez.Drawables.Dial01, Rez.Drawables.Dial02, Rez.Drawables.Dial03,
                   Rez.Drawables.Dial10, Rez.Drawables.Dial11, Rez.Drawables.Dial12, Rez.Drawables.Dial13,
                   Rez.Drawables.Dial20, Rez.Drawables.Dial21, Rez.Drawables.Dial22, Rez.Drawables.Dial23,
                   Rez.Drawables.Dial30, Rez.Drawables.Dial31, Rez.Drawables.Dial32, Rez.Drawables.Dial33,
                   Rez.Drawables.Dial40, Rez.Drawables.Dial41, Rez.Drawables.Dial42, Rez.Drawables.Dial43,
                   Rez.Drawables.Dial50, Rez.Drawables.Dial51, Rez.Drawables.Dial52, Rez.Drawables.Dial53];
        try {
            return WatchUi.loadResource(ids[st * 4 + bg]);
        } catch (e) {
            return null;
        }
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
        mLabels = [s(Rez.Strings.LabelSteps), s(Rez.Strings.LabelHeart), s(Rez.Strings.LabelCalories),
                   s(Rez.Strings.LabelBattery), s(Rez.Strings.LabelKm), s(Rez.Strings.LabelFloors),
                   s(Rez.Strings.LabelBodyBattery), s(Rez.Strings.LabelStress)];
        mLabelMi = s(Rez.Strings.LabelMi);
        mAyahRefs = [s(Rez.Strings.AyahRef1), s(Rez.Strings.AyahRef2), s(Rez.Strings.AyahRef3), s(Rez.Strings.AyahRef4),
                     s(Rez.Strings.AyahRef5), s(Rez.Strings.AyahRef6), s(Rez.Strings.AyahRef7)];
        mHijriSuffix = s(Rez.Strings.HijriSuffix);
        mSetLocation = s(Rez.Strings.SetLocation);
        mSetLocation2 = s(Rez.Strings.SetLocation2);
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
        return !mSleeping || (!mBurnIn && mSettings.secondsAlways && mPartialAllowed);
    }

    // ------------------------------------------------------------------ buffers
    hidden function createBuffer(w as Number, h as Number) {
        if (Graphics has :createBufferedBitmap) {
            return Graphics.createBufferedBitmap({:width => w, :height => h});
        }
        return new Graphics.BufferedBitmap({:width => w, :height => h});
    }

    // The bitmap behind a reference (API 4+) or the bitmap itself; null if it was reclaimed.
    hidden function bitmapOf(ref) {
        if (ref == null) {
            return null;
        }
        if (ref has :get) {
            return ref.get();
        }
        return ref;
    }

    // ------------------------------------------------------------------ updates
    function onUpdate(dc as Graphics.Dc) as Void {
        var now = Time.now().value();
        var clock = System.getClockTime();
        if (mSleeping && mBurnIn) {
            drawAlwaysOn(dc, clock);
            return;
        }
        var frame = bitmapOf(mFrameRef);
        var target = (frame != null) ? frame.getDc() : dc;
        setAntiAlias(target);

        var dial = mDial;
        if (dial == null && mStaticRef == null) {
            // HD dial unavailable (e.g. after a settings change): vector static layer instead
            mStaticRef = createBuffer(dc.getWidth(), dc.getHeight());
            mStaticDirty = true;
        }
        var stat = bitmapOf(mStaticRef);
        if (dial != null) {
            target.drawBitmap(0, 0, dial);
        } else if (stat != null) {
            if (mStaticDirty) {
                var sdc = stat.getDc();
                setAntiAlias(sdc);
                drawStaticLayer(sdc);
                mStaticDirty = false;
            }
            target.drawBitmap(0, 0, stat);
        } else {
            drawStaticLayer(target);
        }
        drawLive(target, now, clock);

        if (frame != null) {
            dc.drawBitmap(0, 0, frame);
        }
        mLastSecBox = null;
        if (showSeconds()) {
            setAntiAlias(dc);
            drawSecondsHand(dc, clock.sec);
            mLastSecBox = secondsBox(clock.sec);
        }
    }

    function onPartialUpdate(dc as Graphics.Dc) as Void {
        if (mBurnIn || !mPartialAllowed || !mSettings.secondsAlways) {
            return;
        }
        var frame = bitmapOf(mFrameRef);
        if (frame == null) {
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
        dc.drawBitmap(0, 0, frame);
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

    // ------------------------------------------------------------------ scaling helpers
    // v in 280-px dial units -> device pixels
    hidden function p(v as Numeric) as Number {
        return Math.floor(v * mK + 0.5).toNumber();
    }

    hidden function pen(w as Numeric) as Number {
        var v = p(w);
        return (v < 1) ? 1 : v;
    }

    // Point at distance r (dial units) from the centre, direction a (radians clockwise from 12).
    hidden function polar(r as Numeric, a as Numeric) as Array<Number> {
        var c = mSize / 2.0;
        return [Math.floor(c + r * mK * Math.sin(a) + 0.5).toNumber(),
                Math.floor(c - r * mK * Math.cos(a) + 0.5).toNumber()];
    }

    // Rotates and scales points given in dial units around the centre (y towards 12 is negative).
    hidden function rotatePoly(pts as Array, a as Numeric) as Array {
        var sn = Math.sin(a);
        var cs = Math.cos(a);
        var c = mSize / 2.0;
        var out = [];
        for (var i = 0; i < pts.size(); i++) {
            var pt = pts[i] as Array;
            var x = pt[0];
            var y = pt[1];
            out.add([Math.floor(c + (x * cs - y * sn) * mK + 0.5).toNumber(),
                     Math.floor(c + (x * sn + y * cs) * mK + 0.5).toNumber()]);
        }
        return out;
    }

    hidden function gaugeCentre(i as Number) as Array<Number> {
        if (i < 2) {
            var dx = (i == 0) ? -Layout.GAUGE_UP_DX : Layout.GAUGE_UP_DX;
            return [p(Layout.CX + dx), p(Layout.GAUGE_UP_Y)];
        }
        var dx2 = (i == 2) ? -Layout.GAUGE_SIDE_DX : Layout.GAUGE_SIDE_DX;
        return [p(Layout.CX + dx2), p(Layout.GAUGE_SIDE_Y)];
    }

    // ------------------------------------------------------------------ static layer
    hidden function drawStaticLayer(dc as Graphics.Dc) as Void {
        var c = mColors;
        var vc = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        dc.setColor(c[Themes.BG], c[Themes.BG]);
        dc.clear();
        var bg = mBgOps;
        if (bg != null) {
            Backgrounds.draw(dc, bg, c, mK);
        }
        var fr = mFrameOps;
        if (fr != null) {
            Backgrounds.draw(dc, fr, c, mK);
        }

        // minute track
        dc.setPenWidth(pen(1));
        dc.setColor(c[Themes.TICK], Graphics.COLOR_TRANSPARENT);
        for (var i = 0; i < 60; i++) {
            if (i % 5 != 0) {
                var a = i * Math.PI / 30.0;
                var p0 = polar(Layout.TICK_R_IN, a);
                var p1 = polar(Layout.TICK_R_OUT, a);
                dc.drawLine(p0[0], p0[1], p1[0], p1[1]);
            }
        }
        // two-tone hour indices, numerals at 12 / 3 / 6 / 9
        var wi = Layout.IDX_W_IN;
        var wo = Layout.IDX_W_OUT;
        var ri = Layout.IDX_R_IN;
        var ro = Layout.IDX_R_OUT;
        for (var h = 0; h < 12; h++) {
            if (h % 3 != 0) {
                var a = h * Math.PI / 6.0;
                dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
                dc.fillPolygon(rotatePoly([[-wi, -ri], [0, -ri], [0, -ro], [-wo, -ro]], a));
                dc.setColor(c[Themes.GOLD_DK], Graphics.COLOR_TRANSPARENT);
                dc.fillPolygon(rotatePoly([[0, -ri], [wi, -ri], [wo, -ro], [0, -ro]], a));
            }
        }
        var nums = ["12", "3", "6", "9"];
        for (var q = 0; q < 4; q++) {
            var pt = polar(Layout.NUM_R, q * Math.PI / 2.0);
            dc.setColor(c[Themes.PLATE], Graphics.COLOR_TRANSPARENT);
            dc.drawText(pt[0] + 1, pt[1] + 1, mFontNum, nums[q], vc);
            dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
            dc.drawText(pt[0], pt[1], mFontNum, nums[q], vc);
        }
        // crescent above the date block
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(p(140), p(Layout.CRESCENT_Y), p(6));
        dc.setColor(c[Themes.BG], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(p(143), p(Layout.CRESCENT_Y - 2), p(5));
        // gauge discs, gold rims and tracks
        for (var g = 0; g < 4; g++) {
            var gc = gaugeCentre(g);
            dc.setColor(c[Themes.PLATE], Graphics.COLOR_TRANSPARENT);
            dc.fillCircle(gc[0], gc[1], p(Layout.GAUGE_DISC_R));
            dc.setPenWidth(pen(1));
            dc.setColor(c[Themes.GOLD_DK], Graphics.COLOR_TRANSPARENT);
            dc.drawCircle(gc[0], gc[1], p(Layout.GAUGE_DISC_R));
            dc.setPenWidth(pen(Layout.GAUGE_PEN));
            dc.setColor(c[Themes.TRACK], Graphics.COLOR_TRANSPARENT);
            dc.drawCircle(gc[0], gc[1], p(Layout.GAUGE_R));
        }
        dc.setPenWidth(1);
        // small gold diamond under the hub
        var cx = p(140);
        var dy = p(Layout.HUB_DIAMOND_Y);
        var d = p(4);
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([[cx, dy - d], [cx + d, dy], [cx, dy + d], [cx - d, dy]]);
    }

    // ------------------------------------------------------------------ live content
    hidden function drawLive(dc as Graphics.Dc, now as Number, clock as System.ClockTime) as Void {
        var c = mColors;
        var vc = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        var day = CivilDate.localEpochDay(now, clock.timeZoneOffset);

        // date block
        var ymd = CivilDate.fromDays(day);
        dc.setColor(c[Themes.TEXT], Graphics.COLOR_TRANSPARENT);
        dc.drawText(p(140), p(Layout.DAY_NAME_Y), mFontXS, mDays[CivilDate.dayOfWeek(day)], vc);
        dc.drawText(p(140), p(Layout.DAY_NUM_Y), mFontL, ymd[2].toString(), vc);
        dc.drawText(p(140), p(Layout.MONTH_Y), mFontXS, mMonths[ymd[1] - 1] + " " + ymd[0].toString(), vc);
        var h = HijriCalendar.forEpochDay(day, mSettings.hijriCorrection);
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.drawText(p(140), p(Layout.HIJRI_Y), mFontXS,
                    h[2].toString() + " " + mHijriMonths[h[1] - 1] + " " + h[0].toString() + " " + mHijriSuffix, vc);

        // gauges
        var info = ActivityMonitor.getInfo();
        for (var g = 0; g < 4; g++) {
            var gc = gaugeCentre(g);
            drawGauge(dc, gc[0], gc[1], mSettings.gauges[g], info);
        }

        drawPrayers(dc, now, clock);
        drawAyah(dc, clock.min);
        drawHourMinuteHands(dc, clock);
    }

    // ------------------------------------------------------------------ gauges
    hidden function drawGauge(dc as Graphics.Dc, x as Number, y as Number, source as Number,
                              info as ActivityMonitor.Info?) as Void {
        var c = mColors;
        var color = c[Themes.ACCENT];
        if (mMulticolor) {
            color = Themes.SOURCE_COLORS[source] as Number;
        }
        var data = DataFields.read(source, info);
        var value = data[0];
        var progress = data[1];
        var flag = data[2] as Number;
        if (progress != null) {
            var pr = progress as Float;
            if (pr > 1.0) {
                pr = 1.0;
            }
            var sweep = (360.0 * pr).toNumber();
            if (sweep >= 2) {
                var end = 90 - sweep;
                if (end < 0) {
                    end += 360;
                }
                var warn = (source == DataFields.BATTERY && flag == 1);
                dc.setColor(warn ? c[Themes.WARN] : color, Graphics.COLOR_TRANSPARENT);
                dc.setPenWidth(pen(Layout.GAUGE_PEN));
                dc.drawArc(x, y, p(Layout.GAUGE_R), Graphics.ARC_CLOCKWISE, 90, end);
                dc.setPenWidth(1);
            }
        }
        var isBatt = (source == DataFields.BATTERY);
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        drawGaugeIcon(dc, x, y + p(isBatt ? Layout.GAUGE_BATT_ICON_DY : Layout.GAUGE_ICON_DY), source);

        var tcol = c[Themes.TEXT];
        if (value == null) {
            value = "--";
            tcol = c[Themes.DIM];
        } else if (flag == 1) {
            tcol = (source == DataFields.BATTERY) ? c[Themes.WARN] : c[Themes.DIM];
        }
        // Battery uses the large font; a value wider than the ring interior steps down.
        var font = (source == DataFields.BATTERY) ? mFontL : mFontM;
        var inner = 2 * (p(Layout.GAUGE_R) - pen(Layout.GAUGE_PEN) / 2) - 2;
        if (dc.getTextWidthInPixels(value as String, font) > inner) {
            font = mFontM;
            if (dc.getTextWidthInPixels(value as String, font) > inner) {
                font = mFontS;
            }
        }
        dc.setColor(tcol, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, y + p(Layout.GAUGE_VALUE_DY), font, value as String,
                    Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);

        var label = mLabels[source];
        if (source == DataFields.DISTANCE && System.getDeviceSettings().distanceUnits == System.UNIT_STATUTE) {
            label = mLabelMi;
        }
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, y + p(isBatt ? Layout.GAUGE_BATT_LABEL_DY : Layout.GAUGE_LABEL_DY), mFontXS, label,
                    Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }

    // Icon above the value (about 13 x 12 dial units), in the current colour.
    hidden function drawGaugeIcon(dc as Graphics.Dc, x as Number, y as Number, source as Number) as Void {
        if (source == DataFields.STEPS) {
            dc.fillEllipse(x - p(3), y + p(1), p(2), p(4));
            dc.fillEllipse(x + p(3), y - p(1), p(2), p(4));
        } else if (source == DataFields.HEART) {
            dc.fillCircle(x - p(2), y - p(2), p(3));
            dc.fillCircle(x + p(2), y - p(2), p(3));
            dc.fillPolygon([[x - p(5), y - p(1)], [x + p(5), y - p(1)], [x, y + p(5)]]);
        } else if (source == DataFields.CALORIES) {
            dc.fillPolygon([[x, y - p(6)], [x + p(4), y + p(1)], [x + p(3), y + p(4)], [x - p(3), y + p(4)],
                            [x - p(4), y + p(1)]]);
        } else if (source == DataFields.BATTERY) {
            dc.fillRectangle(x - p(6), y - p(3), p(11), p(7));
            dc.fillRectangle(x + p(5), y - p(1), p(2), p(3));
        } else if (source == DataFields.DISTANCE) {
            dc.setPenWidth(pen(2));
            dc.drawLine(x - p(5), y + p(4), x + p(4), y - p(4));
            dc.setPenWidth(1);
            dc.fillPolygon([[x + p(5), y - p(5)], [x, y - p(4)], [x + p(4), y]]);
        } else if (source == DataFields.FLOORS) {
            dc.setPenWidth(pen(2));
            var st = [[-6, 4], [-3, 4], [-3, 1], [0, 1], [0, -2], [3, -2], [3, -5], [6, -5]];
            for (var i = 0; i + 1 < st.size(); i++) {
                var a = st[i] as Array<Number>;
                var b = st[i + 1] as Array<Number>;
                dc.drawLine(x + p(a[0]), y + p(a[1]), x + p(b[0]), y + p(b[1]));
            }
            dc.setPenWidth(1);
        } else if (source == DataFields.BODY_BATTERY) {
            dc.fillPolygon([[x + p(2), y - p(6)], [x - p(3), y + p(1)], [x + p(1), y + p(1)]]);
            dc.fillPolygon([[x - p(1), y - p(1)], [x + p(3), y - p(1)], [x - p(2), y + p(6)]]);
        } else if (source == DataFields.STRESS) {
            dc.setPenWidth(pen(2));
            var zz = [[-6, 1], [-3, -3], [0, 3], [3, -3], [6, 1]];
            for (var i = 0; i + 1 < zz.size(); i++) {
                var a = zz[i] as Array<Number>;
                var b = zz[i + 1] as Array<Number>;
                dc.drawLine(x + p(a[0]), y + p(a[1]), x + p(b[0]), y + p(b[1]));
            }
            dc.setPenWidth(1);
        }
    }

    // ------------------------------------------------------------------ prayers and sun
    hidden function drawPrayers(dc as Graphics.Dc, now as Number, clock as System.ClockTime) as Void {
        var c = mColors;
        var vc = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        if (!mSettings.locationSet) {
            dc.setColor(c[Themes.DIM], Graphics.COLOR_TRANSPARENT);
            dc.drawText(p(Layout.CX - Layout.PANEL_DX), p(Layout.PANEL_Y0 + 8), mFontXS, mSetLocation, vc);
            dc.drawText(p(Layout.CX - Layout.PANEL_DX), p(Layout.PANEL_Y0 + 20), mFontXS, mSetLocation2, vc);
            return;
        }
        var offset = mSettings.tzManual ? mSettings.utcOffsetSeconds : clock.timeZoneOffset;
        mSchedule.update(now, offset);
        var is24 = System.getDeviceSettings().is24Hour;
        var list = mSchedule.upcoming(now, 2);
        if (list.size() > 0) {
            var n = list[0] as Array;
            var secs = ((n[1] as Long) - now).toNumber();
            drawPanel(dc, p(Layout.CX - Layout.PANEL_DX), true, mPrayerNames[n[0] as Number] as String,
                      countdown(secs), c[Themes.GOLD]);
        }
        if (list.size() > 1) {
            var f = list[1] as Array;
            drawPanel(dc, p(Layout.CX + Layout.PANEL_DX), false, mPrayerNames[f[0] as Number] as String,
                      formatTime(mSchedule.minutes(f[2] as Number, f[0] as Number), is24), c[Themes.TEXT]);
        }
        drawSun(dc, true, mSchedule.minutes(0, PrayerTimes.SUNRISE), is24);
        drawSun(dc, false, mSchedule.minutes(0, PrayerTimes.SUNSET), is24);
    }

    // Cartouche content: icon on the left, name above value. `next` selects the mosque icon.
    hidden function drawPanel(dc as Graphics.Dc, cx as Number, next as Boolean, name as String, value as String,
                              valueColor as Number) as Void {
        var c = mColors;
        var vc = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        var x0 = cx - p(Layout.PANEL_W) / 2;
        var ix = x0 + p(11);
        var iy = p(Layout.PANEL_Y0 + Layout.PANEL_H / 2);
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        if (mDial != null) {
            // icons are part of the HD dial
        } else if (next) {
            dc.fillCircle(ix, iy, p(4));
            dc.fillRectangle(ix - p(5), iy, p(10) + 1, p(6));
            dc.fillRectangle(ix, iy - p(7), 1, p(3));
        } else {
            dc.fillCircle(ix, iy, p(5));
            dc.setColor(c[Themes.PLATE], Graphics.COLOR_TRANSPARENT);
            dc.fillCircle(ix + p(2), iy - p(2), p(4));
            dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
            dc.fillCircle(ix + p(4), iy + p(2), 1);
        }
        var tx = x0 + p(20) + (p(Layout.PANEL_W) - p(22)) / 2;
        dc.setColor(c[Themes.TEXT], Graphics.COLOR_TRANSPARENT);
        dc.drawText(tx, p(Layout.PANEL_Y0 + 8), mFontXS, name, vc);
        dc.setColor(valueColor, Graphics.COLOR_TRANSPARENT);
        dc.drawText(tx, p(Layout.PANEL_Y0 + 20), mFontS, value, vc);
    }

    // Sun on the horizon with rays and an up/down arrow, time below.
    hidden function drawSun(dc as Graphics.Dc, rising as Boolean, minutes as Number?, is24 as Boolean) as Void {
        var c = mColors;
        var x = p(Layout.CX + (rising ? -Layout.SUN_DX : Layout.SUN_DX));
        var y = p(Layout.SUN_ICON_Y);
        if (mDial != null) {
            // the sun icon is part of the HD dial: only the time is live
            dc.setColor(c[Themes.TEXT], Graphics.COLOR_TRANSPARENT);
            dc.drawText(x, p(Layout.SUN_TIME_Y), mFontS, formatTime(minutes, is24),
                        Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
            return;
        }
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(pen(2));
        dc.drawArc(x, y + p(2), p(5), Graphics.ARC_COUNTER_CLOCKWISE, 0, 180);
        dc.setPenWidth(pen(1));
        dc.drawLine(x - p(8), y + p(2), x + p(8), y + p(2));
        var rays = [30, 90, 150];
        for (var i = 0; i < 3; i++) {
            var a = Math.toRadians(rays[i]);
            dc.drawLine(x + Math.round(p(7) * Math.cos(a)).toNumber(), y + p(2) - Math.round(p(7) * Math.sin(a)).toNumber(),
                        x + Math.round(p(9) * Math.cos(a)).toNumber(), y + p(2) - Math.round(p(9) * Math.sin(a)).toNumber());
        }
        dc.setPenWidth(1);
        if (rising) {
            dc.fillPolygon([[x, y + p(3)], [x - p(2), y + p(6)], [x + p(2), y + p(6)]]);
        } else {
            dc.fillPolygon([[x, y + p(7)], [x - p(2), y + p(4)], [x + p(2), y + p(4)]]);
        }
        dc.setColor(c[Themes.TEXT], Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, p(Layout.SUN_TIME_Y), mFontS, formatTime(minutes, is24),
                    Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
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

    // ------------------------------------------------------------------ Ayah
    hidden function drawAyah(dc as Graphics.Dc, minute as Number) as Void {
        var a = mSettings.ayah;
        if (a == LuxeSettings.AYAH_NONE) {
            return;
        }
        // glyphs "1".."7"; Al-Ikhlas shows one verse per minute: "6", "A", "B", "C"
        var code = (a + 1).toString();
        var ref = mAyahRefs[a];
        if (a == 5) {
            var v = minute % 4;
            var codes = ["6", "A", "B", "C"];
            code = codes[v];
            ref = ref + (v + 1).toString();
        }
        var vc = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        dc.setColor(mColors[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.drawText(p(140), p(Layout.AYAH_Y), mFontAyah, code, vc);
        dc.setColor(mColors[Themes.DIM], Graphics.COLOR_TRANSPARENT);
        dc.drawText(p(140), p(Layout.AYAH_REF_Y), mFontXS, ref, vc);
    }

    // ------------------------------------------------------------------ hands
    hidden function drawHourMinuteHands(dc as Graphics.Dc, clock as System.ClockTime) as Void {
        var c = mColors;
        var hourA = ((clock.hour % 12) + clock.min / 60.0) * Math.PI / 6.0;
        var minA = clock.min * Math.PI / 30.0;
        drawBaton(dc, hourA, Layout.HOUR_LEN, Layout.HOUR_W, Layout.HOUR_TAIL);
        drawBaton(dc, minA, Layout.MIN_LEN, Layout.MIN_W, Layout.MIN_TAIL);
        var cx = mSize / 2;
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx, cx, p(Layout.CAP_R));
        dc.setColor(c[Themes.GOLD_DK], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx, cx, p(Layout.CAP_INNER_R));
    }

    // Gold baton hand with a pointed tip, drop shadow, dark outline and a light lume insert.
    hidden function drawBaton(dc as Graphics.Dc, a as Numeric, len as Number, w as Number, tail as Number) as Void {
        var c = mColors;
        var sh = rotatePoly([[-w - 1, tail + 1], [w + 1, tail + 1], [w, -len - 1], [0, -len - 5], [-w, -len - 1]], a);
        var off = pen(2);
        for (var i = 0; i < sh.size(); i++) {
            var pt = sh[i] as Array<Number>;
            sh[i] = [pt[0] + off, pt[1] + off];
        }
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(sh);
        dc.setColor(c[Themes.PLATE], Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(rotatePoly([[-w - 1, tail + 1], [w + 1, tail + 1], [w, -len - 1], [0, -len - 5], [-w, -len - 1]], a));
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(rotatePoly([[-w, tail], [w, tail], [w - 0.5, -len], [0, -len - 4], [-w + 0.5, -len]], a));
        dc.setColor(c[Themes.TEXT], Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon(rotatePoly([[-w + 1.5, -14], [w - 1.5, -14], [w - 1.5, -len + 3], [-w + 1.5, -len + 3]], a));
    }

    hidden function drawSecondsHand(dc as Graphics.Dc, sec as Number) as Void {
        var c = mColors;
        var a = sec * Math.PI / 30.0;
        var tip = polar(Layout.SEC_LEN, a);
        var tail = polar(-Layout.SEC_TAIL, a);
        var weight = polar(-(Layout.SEC_TAIL - Layout.SEC_WEIGHT_R - 2), a);
        dc.setColor(c[Themes.SECONDS], Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(pen(Layout.SEC_PEN));
        dc.drawLine(tail[0], tail[1], tip[0], tip[1]);
        dc.setPenWidth(pen(2));
        dc.drawCircle(weight[0], weight[1], p(Layout.SEC_WEIGHT_R));
        dc.setPenWidth(1);
        var cx = mSize / 2;
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx, cx, p(Layout.CAP_R));
        dc.setColor(c[Themes.SECONDS], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx, cx, p(Layout.CAP_INNER_R));
        dc.setColor(c[Themes.PLATE], Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx, cx, pen(1.5));
    }

    // Bounding box [x, y, w, h] of everything drawSecondsHand() touches.
    hidden function secondsBox(sec as Number) as Array<Number> {
        var a = sec * Math.PI / 30.0;
        var tip = polar(Layout.SEC_LEN, a);
        var tail = polar(-Layout.SEC_TAIL, a);
        var cx = mSize / 2;
        var cap = p(Layout.CAP_R);
        var m = p(Layout.SEC_WEIGHT_R) + pen(2) + 3;
        var x0 = min3(tip[0], tail[0], cx - cap) - m;
        var y0 = min3(tip[1], tail[1], cx - cap) - m;
        var x1 = max3(tip[0], tail[0], cx + cap) + m;
        var y1 = max3(tip[1], tail[1], cx + cap) + m;
        return [x0, y0, x1 - x0, y1 - y0];
    }

    hidden function min3(a as Number, b as Number, c as Number) as Number {
        var m = (a < b) ? a : b;
        return (m < c) ? m : c;
    }

    hidden function max3(a as Number, b as Number, c as Number) as Number {
        var m = (a > b) ? a : b;
        return (m > c) ? m : c;
    }

    // ------------------------------------------------------------------ AMOLED always-on
    // Burn-in safe frame: black screen, thin hour/minute hands, four dots; everything shifts by
    // up to 2 px each minute so that no pixel stays lit.
    hidden function drawAlwaysOn(dc as Graphics.Dc, clock as System.ClockTime) as Void {
        var c = mColors;
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        setAntiAlias(dc);
        var shift = (clock.min % 5) - 2;
        var cx = mSize / 2 + shift;
        dc.setColor(c[Themes.DIM], Graphics.COLOR_TRANSPARENT);
        for (var q = 0; q < 4; q++) {
            var pt = polar(Layout.NUM_R + 6, q * Math.PI / 2.0);
            dc.fillCircle(pt[0] + shift, pt[1] + shift, pen(2));
        }
        dc.setColor(c[Themes.GOLD], Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(pen(2));
        var hourTip = polar(Layout.HOUR_LEN, ((clock.hour % 12) + clock.min / 60.0) * Math.PI / 6.0);
        var minTip = polar(Layout.MIN_LEN, clock.min * Math.PI / 30.0);
        dc.drawLine(cx, cx, hourTip[0] + shift, hourTip[1] + shift);
        dc.drawLine(cx, cx, minTip[0] + shift, minTip[1] + shift);
        dc.setPenWidth(1);
        dc.drawCircle(cx, cx, p(4));
    }
}
