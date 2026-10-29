import Toybox.Graphics;
import Toybox.Lang;
import Toybox.WatchUi;

// Draws a background from its vector description (resources/jsonData/bg_*.json, generated
// by tools/build_assets.py). Shapes reference colour roles, so every background is
// recoloured by the selected style preset. tools/face.py interprets the same data.
module Backgrounds {

    const OP_POLY = 0;      // [0, role, x1, y1, x2, y2, ...]
    const OP_CIRCLE = 1;    // [1, role, x, y, r]
    const OP_LINE = 2;      // [2, role, pen, x1, y1, x2, y2]
    const OP_POLYLINE = 3;  // [3, role, pen, x1, y1, ...]
    const OP_POINTS = 4;    // [4, role, size, x1, y1, ...]
    const OP_RING = 5;      // [5, role, pen, x, y, r]
    const OP_RECT = 6;      // [6, role, x, y, w, h]
    const OP_STAR8 = 7;     // [7, role, pen, x, y, r]  8-point star outline (two squares)
    const OP_FILL = 8;      // [8, role]
    const OP_CRESCENT = 9;  // [9, role, maskRole, x, y, r, dx, dy, r2]

    function load(index as Number) as Array? {
        var id = Rez.JsonData.BgMosque;
        if (index == 1) {
            id = Rez.JsonData.BgGeometric;
        } else if (index == 2) {
            id = Rez.JsonData.BgMarble;
        } else if (index == 3) {
            id = Rez.JsonData.BgNight;
        }
        return WatchUi.loadResource(id) as Array?;
    }

    function draw(dc as Graphics.Dc, ops as Array, colors as Array) as Void {
        for (var i = 0; i < ops.size(); i++) {
            var op = ops[i] as Array<Number>;
            var code = op[0];
            var color = colors[op[1]] as Number;
            dc.setColor(color, Graphics.COLOR_TRANSPARENT);
            if (code == OP_POLY) {
                var pts = [];
                for (var k = 2; k + 1 < op.size(); k += 2) {
                    pts.add([op[k], op[k + 1]]);
                }
                dc.fillPolygon(pts);
            } else if (code == OP_CIRCLE) {
                dc.fillCircle(op[2], op[3], op[4]);
            } else if (code == OP_LINE) {
                dc.setPenWidth(op[2]);
                dc.drawLine(op[3], op[4], op[5], op[6]);
            } else if (code == OP_POLYLINE) {
                dc.setPenWidth(op[2]);
                for (var k = 3; k + 3 < op.size(); k += 2) {
                    dc.drawLine(op[k], op[k + 1], op[k + 2], op[k + 3]);
                }
            } else if (code == OP_POINTS) {
                var size = op[2];
                for (var k = 3; k + 1 < op.size(); k += 2) {
                    if (size <= 1) {
                        dc.drawPoint(op[k], op[k + 1]);
                    } else {
                        dc.fillRectangle(op[k], op[k + 1], size, size);
                    }
                }
            } else if (code == OP_RING) {
                dc.setPenWidth(op[2]);
                dc.drawCircle(op[3], op[4], op[5]);
            } else if (code == OP_RECT) {
                dc.fillRectangle(op[2], op[3], op[4], op[5]);
            } else if (code == OP_STAR8) {
                dc.setPenWidth(op[2]);
                drawStar8(dc, op[3], op[4], op[5]);
            } else if (code == OP_FILL) {
                dc.fillRectangle(0, 0, dc.getWidth(), dc.getHeight());
            } else if (code == OP_CRESCENT) {
                dc.fillCircle(op[3], op[4], op[5]);
                dc.setColor(colors[op[2]] as Number, Graphics.COLOR_TRANSPARENT);
                dc.fillCircle(op[3] + op[6], op[4] + op[7], op[8]);
            }
        }
        dc.setPenWidth(1);
    }

    // Outline of an 8-point star (Rub el Hizb): a square and the same square turned 45 deg.
    function drawStar8(dc as Graphics.Dc, x as Number, y as Number, r as Number) as Void {
        var d = (r * 0.7071 + 0.5).toNumber();
        dc.drawLine(x, y - r, x + r, y);
        dc.drawLine(x + r, y, x, y + r);
        dc.drawLine(x, y + r, x - r, y);
        dc.drawLine(x - r, y, x, y - r);
        dc.drawLine(x - d, y - d, x + d, y - d);
        dc.drawLine(x + d, y - d, x + d, y + d);
        dc.drawLine(x + d, y + d, x - d, y + d);
        dc.drawLine(x - d, y + d, x - d, y - d);
    }
}
