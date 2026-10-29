import Toybox.Activity;
import Toybox.ActivityMonitor;
import Toybox.Lang;
import Toybox.Math;
import Toybox.SensorHistory;
import Toybox.System;
import Toybox.Time;

// Live data for the four gauges. Only documented Toybox APIs are used and every source is
// guarded with `has` checks, so a value the watch cannot provide is shown as "--".
module DataFields {

    // Order must match the gauge source lists in resources/settings/settings.xml.
    const STEPS = 0;
    const HEART = 1;
    const CALORIES = 2;
    const BATTERY = 3;
    const DISTANCE = 4;
    const FLOORS = 5;
    const BODY_BATTERY = 6;
    const STRESS = 7;
    const ACTIVE_MINUTES = 8;
    const NONE = 9;               // empty gauge

    const HR_SCALE_MIN = 40.0;   // the heart-rate ring is a meter from 40 to 200 bpm
    const HR_SCALE_MAX = 200.0;
    const HR_STALE_SECONDS = 900;
    const LOW_BATTERY = 15;

    // Returns [value text or null, progress 0..1 or null, flag]
    // flag: 0 = normal, 1 = stale or warning (dimmed / warning colour)
    function read(source as Number, info as ActivityMonitor.Info?) as Array {
        if (source == BATTERY) {
            var stats = System.getSystemStats();
            var pct = Math.round(stats.battery).toNumber();
            var warn = (pct <= LOW_BATTERY && !((stats has :charging) && stats.charging)) ? 1 : 0;
            return [pct.toString(), stats.battery / 100.0, warn];
        }
        if (source == HEART) {
            return heartRate();
        }
        if (source == BODY_BATTERY) {
            if ((Toybox has :SensorHistory) && (SensorHistory has :getBodyBatteryHistory)) {
                return history(SensorHistory.getBodyBatteryHistory({:period => 1}));
            }
            return [null, null, 0];
        }
        if (source == STRESS) {
            if ((Toybox has :SensorHistory) && (SensorHistory has :getStressHistory)) {
                return history(SensorHistory.getStressHistory({:period => 1}));
            }
            return [null, null, 0];
        }
        if (info == null) {
            return [null, null, 0];
        }
        if (source == STEPS) {
            var steps = info.steps;
            if (steps == null) {
                return [null, null, 0];
            }
            return [formatCount(steps), ratio(steps, info.stepGoal), 0];
        }
        if (source == CALORIES) {
            // ActivityMonitor has no calorie goal: the ring shows its track only.
            return [info.calories == null ? null : formatCount(info.calories), null, 0];
        }
        if (source == DISTANCE) {
            var cm = info.distance;
            if (cm == null) {
                return [null, null, 0];
            }
            var units = cm / ((System.getDeviceSettings().distanceUnits == System.UNIT_STATUTE) ? 160934.4 : 100000.0);
            return [(units < 100.0) ? units.format("%.1f") : units.toNumber().toString(), null, 0];
        }
        if (source == ACTIVE_MINUTES) {
            if (!(info has :activeMinutesWeek) || info.activeMinutesWeek == null) {
                return [null, null, 0];
            }
            var total = info.activeMinutesWeek.total;
            var goal = (info has :activeMinutesWeekGoal) ? info.activeMinutesWeekGoal : null;
            return [total.toString(), ratio(total, goal), 0];
        }
        if (source == FLOORS) {
            if (!(info has :floorsClimbed) || info.floorsClimbed == null) {
                return [null, null, 0];
            }
            var goal = (info has :floorsClimbedGoal) ? info.floorsClimbedGoal : null;
            return [info.floorsClimbed.toString(), ratio(info.floorsClimbed, goal), 0];
        }
        return [null, null, 0];
    }

    function heartRate() as Array {
        var act = Activity.getActivityInfo();
        if (act != null && act.currentHeartRate != null) {
            return [act.currentHeartRate.toString(), hrRatio(act.currentHeartRate), 0];
        }
        if (ActivityMonitor has :getHeartRateHistory) {
            var it = ActivityMonitor.getHeartRateHistory(1, true);
            var s = it.next();
            if (s != null && s.heartRate != null && s.heartRate != ActivityMonitor.INVALID_HR_SAMPLE) {
                var stale = (s.when != null && Time.now().value() - s.when.value() > HR_STALE_SECONDS) ? 1 : 0;
                return [s.heartRate.toString(), hrRatio(s.heartRate), stale];
            }
        }
        return [null, null, 0];
    }

    function history(it) as Array {
        if (it == null) {
            return [null, null, 0];
        }
        var s = it.next();
        if (s == null || s.data == null) {
            return [null, null, 0];
        }
        var v = s.data.toNumber();
        return [v.toString(), v / 100.0, 0];
    }

    function hrRatio(hr as Number) as Float {
        return (hr - HR_SCALE_MIN) / (HR_SCALE_MAX - HR_SCALE_MIN);
    }

    function ratio(value, goal) as Float? {
        if (value == null || goal == null || goal <= 0) {
            return null;
        }
        return value.toFloat() / goal;
    }

    // Keeps the value inside the gauge: 9999, 12.3k, 123k
    function formatCount(n as Number) as String {
        if (n < 10000) {
            return n.toString();
        }
        if (n < 100000) {
            return (n / 1000.0).format("%.1f") + "k";
        }
        return (n / 1000).toString() + "k";
    }
}
