/**
 * Created by cqian19 on 7/24/2016.
 */

var focused = true;
var mapObj = null;
var imgWidth = 32;
var imgHeight = 32;

player = {
    img_root: '',
    marker: '',
    lat: 0,
    lng: 0,
    initializeMarker: function() {
        player.marker = new google.maps.Marker({
            map: mapObj,
            position: {lat: player.lat, lng: player.lng},
            icon: createIcon(player.img_root),
            zIndex: 2
        })
    },
    updateMarker: function() {
        if (map == null || marker == null) { return; }

    }
}

function requester(r, fn, cb) {
    if (r == null) {
        alert("No response from " + fn + ". Server may be down.");
    } else {
        cb(r);
    }
}

function getMapData(cb) {
    $.ajax({
        url: 'data',
        type: 'GET',
        dataType: 'json',
        success: function(r) { requester(r, arguments.callee.name, cb); }
    });
}

function getPlayerLocation(cb) {
    var location;
    $.ajax({
        url: 'location',
        type: 'GET',
        dataType: 'json',
        success: function(r) { requester(r["location"], arguments.callee.name, cb); }
    });
}

function initializeMap() {
    console.log("initialize");
    console.log("Initializing map");
    mapObj = new google.maps.Map(document.getElementById('map'), {
          center: {lat: 37.4419, lng: -122.1419},
          zoom: 17,
          minZoom: 12
    });
    followPlayer();
}

function createIcon(url) {
    return new google.maps.Icon({
        url: url,
        scaledSize: new google.maps.Size({
            width: imgWidth,
            height: imgHeight
        })
    })
}

function initializePlayer() {

}

function followPlayer() {
    if (map == null || !focused) { return; }
    getPlayerLocation(function(location) {
        console.log(location[0], location[1]);
        var latlng = new google.maps.LatLng(parseFloat(location[0]), parseFloat(location[1]));
        map.panTo(latlng);
    });
}


function updateMarker() { }
$(function() {
    setInterval(getMapData, 5000);
    setInterval(followPlayer, 250)
})