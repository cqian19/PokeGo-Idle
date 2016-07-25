/**
 * Created by cqian19 on 7/24/2016.
 */
$(
    animate = {
        ease: function(options) {
            defaultOptions = {
                marker: null,
                start: new google.maps.LatLng(0, 0),
                end: new google.maps.LatLng(0, 0),
                step: 17,
                duration: playerUpdateTime,
                easing: 'easeInOutQuint',
                complete: null
            }
            options = options || {};
            for (var k in defaultOptions) {
                options[k] = options[k] || defaultOptions[k];
            }
            if (!jQuery.easing[options.easing]) {
                options.easing = defaultOptions.easing;
            }
            animate.doAnimate(options);
        },
        doAnimate: function(options) {
            console.log(options);
            var time = 0;
            var done_ratio = 0;
            var diffLat = options.end.lat() - options.start.lat();
            var diffLng = options.end.lng() - options.start.lng();
            while (time < options.duration) {
                setTimeout(function() { animate.doStep (options, done_ratio, time, diffLat, diffLng) }, time == 0 ? 0 : options.step);
                time += options.step;
                done_ratio = time / options.duration;
            }
        },
        doStep: function(options, doneRatio, time, diffLat, diffLng) {
            var marker = options.marker;
            var method = options.easing;
            var duration = options.duration;
            newLat = jQuery.easing[method](null, doneRatio, options.start.lat(), diffLat, duration);
            newLng = jQuery.easing[method](null, doneRatio, options.start.lng(), diffLng, duration);
            console.log(time, options.duration, newLat, newLng);
            marker.setPosition(new google.maps.LatLng(newLat, newLng));
        }
    }
)