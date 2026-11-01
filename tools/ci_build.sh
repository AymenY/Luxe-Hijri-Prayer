#!/usr/bin/env bash
# Compile Luxe Hijri Prayer with the Connect IQ SDK (monkeyc must be on PATH).
#
#   tools/ci_build.sh <developer_key.der> [preview|all|iq|tests]
#
#   preview  one device per screen size and display type (default)
#   all      every product listed in manifest.xml
#   iq       the Store package bin/LuxeHijriPrayer.iq (all products, release build)
#   tests    the unit-test build for fenix7xpro (run it in the simulator with monkeydo -t)
#
# Outputs go to bin/: one .prg per device and a build log per device in bin/logs/.
# The script continues after a failing device and exits non-zero if any build failed.
set -u
KEY="${1:?usage: tools/ci_build.sh <developer_key.der> [preview|all|iq|tests]}"
MODE="${2:-preview}"
cd "$(dirname "$0")/.."
mkdir -p bin/logs

# one device per screen size / display type (see docs/RELEASE_CHECKLIST.md)
PREVIEW="fr255s fenix7s fenix7 fenix7xpro venu2s fr165 epix2pro47mm epix2pro51mm"
ALL=$(grep -o 'iq:product id="[^"]*"' manifest.xml | sed 's/.*id="\([^"]*\)"/\1/')

failed=0
build() {  # device
    local dev="$1"
    echo "::group::monkeyc $dev"
    if monkeyc -f monkey.jungle -d "$dev" -o "bin/LuxeHijriPrayer-$dev.prg" -y "$KEY" -w \
            > "bin/logs/$dev.log" 2>&1; then
        echo "OK   $dev ($(du -k "bin/LuxeHijriPrayer-$dev.prg" | cut -f1) KB)"
    else
        echo "FAIL $dev"
        failed=1
    fi
    cat "bin/logs/$dev.log"
    echo "::endgroup::"
}

case "$MODE" in
    preview) for d in $PREVIEW; do build "$d"; done ;;
    all)     for d in $ALL; do build "$d"; done ;;
    iq)
        if monkeyc -f monkey.jungle -e -r -o bin/LuxeHijriPrayer.iq -y "$KEY" -w > bin/logs/iq.log 2>&1; then
            echo "OK   bin/LuxeHijriPrayer.iq ($(du -k bin/LuxeHijriPrayer.iq | cut -f1) KB)"
        else
            echo "FAIL iq"; failed=1
        fi
        cat bin/logs/iq.log ;;
    tests)
        if monkeyc -f monkey.jungle -d fenix7xpro -o bin/LuxeHijriPrayer-tests.prg -y "$KEY" -w --unit-test \
                > bin/logs/tests.log 2>&1; then
            echo "OK   unit-test build (run: monkeydo bin/LuxeHijriPrayer-tests.prg fenix7xpro -t)"
        else
            echo "FAIL unit-test build"; failed=1
        fi
        cat bin/logs/tests.log ;;
    *) echo "unknown mode $MODE"; exit 2 ;;
esac
exit $failed
