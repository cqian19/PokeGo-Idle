/**
 * Created by cqian19 on 7/24/2016.
 */
$(
    animate = {
        ease: function(options) {
            defaultOptions = {
                map: null,
                marker: null,
                start: new google.maps.LatLng(0, 0),
                end: new google.maps.LatLng(0, 0),
                duration: playerUpdateTime,
                easing: 'linear',
                complete: null
            }
            options = options || {};
            for (var k in defaultOptions) {
                options[k] = options[k] || defaultOptions[k];
            }
            if (!jQuery.easing[options.easing]) {
                options.easing = defaultOptions.easing;
            }
            animate.doAnimate(options)
        },
        doAnimate: function(options) {
            var startTime = (new Date()).getTime();
            var curTime = startTime;
            var doneRatio = 0;
            var elapsed = 0;
            var diffLat = options.end.lat() - options.start.lat();
            var diffLng = options.end.lng() - options.start.lng();
            while (doneRatio < 1) {
                animate.doStep (options, elapsed, doneRatio, diffLat, diffLng);
                curTime = (new Date()).getTime();
                elapsed = curTime - startTime;
                doneRatio = elapsed / options.duration;
            }
        },
        doStep: function(options, elapsed, doneRatio, diffLat, diffLng) {
            var marker = options.marker;
            var method = options.easing;
            var map = options.map;
            var duration = options.duration;
            var doneRatioEased = jQuery.easing[method](null, elapsed, 0, 1, duration);
            var newLoc = new google.maps.LatLng(options.start.lat() + diffLat * doneRatioEased, options.start.lng() + diffLng * doneRatioEased);
            marker.setPosition(newLoc);
            map.panTo(newLoc);
        }
    }
)