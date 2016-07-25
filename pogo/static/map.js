/**
 * Created by cqian19 on 7/24/2016.
 */

var focused = true;
var map = null;

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
        success: cb
    });
}

function getPlayerLocation(cb) {
    var location;
    $.ajax({
        url: 'location',
        type: 'GET',
        dataType: 'json',
        success: function(r) { requester(r["location"], this.name, cb); }
    });
}

function initializeMap() {
    console.log("initialize");
    console.log("Initializing map");
    map = new google.maps.Map(document.getElementById('map'), {
          center: {lat: 37.4419, lng: -122.1419},
          zoom: 17,
          minZoom: 12
    });
    followPlayer();
}

function followPlayer() {
    if (map == null || !focused) { return; }
    getPlayerLocation(function(location) {
        console.log(location[0], location[1]);
        var latlng = new google.maps.LatLng(parseFloat(location[0]), parseFloat(location[1]));
        map.panTo(latlng);
    });
}

$(function() {
    setInterval(getMapData, 5000);
    setInterval(followPlayer, 250)
})