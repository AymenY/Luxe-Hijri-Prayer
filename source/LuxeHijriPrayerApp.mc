import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

class LuxeHijriPrayerApp extends Application.AppBase {

    hidden var mView as LuxeHijriPrayerView?;

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state as Dictionary?) as Void {
    }

    function onStop(state as Dictionary?) as Void {
    }

    function getInitialView() {
        var view = new LuxeHijriPrayerView();
        mView = view;
        return [view, new LuxeHijriPrayerDelegate(view)];
    }

    // Called when the user saves settings in the Connect IQ / Garmin Connect app.
    function onSettingsChanged() as Void {
        var view = mView;
        if (view != null) {
            view.applySettings();
        }
        WatchUi.requestUpdate();
    }
}

class LuxeHijriPrayerDelegate extends WatchUi.WatchFaceDelegate {

    hidden var mView as LuxeHijriPrayerView;

    function initialize(view as LuxeHijriPrayerView) {
        WatchFaceDelegate.initialize();
        mView = view;
    }

    // The system reports that onPartialUpdate() used too much time on average: stop
    // drawing the seconds hand in low-power mode (it stays visible after a wrist raise).
    function onPowerBudgetExceeded(powerInfo as WatchUi.WatchFacePowerInfo) as Void {
        mView.disablePartialUpdates();
    }
}
