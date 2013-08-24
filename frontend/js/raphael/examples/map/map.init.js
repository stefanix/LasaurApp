jQuery(function ($) {
    var inDetails = false;
    var container = $("#map");
    var r = Raphael('map', container.width(), container.height());
    var panZoom = r.panzoom({ initialZoom: 6, initialPosition: { x: 120, y: 70} });
    
    panZoom.enable();
    r.safari();

    var attributes = {
        fill: '#F1F1F1',
        stroke: '#FFFFFF',
        'stroke-width': 2,
        'stroke-linejoin': 'round'
    };


    var arr = [];

    var overlay = r.rect(0, 0, r.width, r.height);
    overlay.attr({ fill: '#ffffff', 'fill-opacity': 0, "stroke-width": 0, stroke: '#FFFFFF' });

    for (var country in paths) {
        var obj;

        if (paths[country].path.constructor == Array) {
            obj = r.set();
            for (var i = 0; i < paths[country].path.length; i++) {
                var pt = r.path(paths[country].path[i]);
                obj.push(pt);
            }
        }
        else {
            obj = r.path(paths[country].path);
        }

        obj.attr(attributes);
        arr[paths[country].name] = obj;
    }

    $("#mapContainer #up").click(function (e) {
        panZoom.zoomIn(1);
        e.preventDefault();
    });

    $("#mapContainer #down").click(function (e) {
        panZoom.zoomOut(1);
        e.preventDefault();
    });

});