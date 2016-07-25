/**
 * Created by cqian19 on 7/24/2016.
 */

var focused = true;
var mapObj = null;
var iconPath = "static/icons/"
var playerUpdateTime = 250;
var imgWidth = 45;
var imgHeight = 45;

var player = {
    img_name: 'player1R.gif',
    marker: '',
    lat: 0,
    lng: 0,
    latLng: null,
    initializeMarker: function() {
        player.marker = new google.maps.Marker({
            map: mapObj,
            position: player.latlng,
            icon: createIcon(iconPath + player.img_name),
            optimized: false,
            zIndex: 2,
            visible: true
        })
    },
    updateImage: function() {

    },
    updateMarker: function() {
        if (mapObj == null) { return; }
        if (player.marker == '') { player.initializeMarker(); }
        animate.ease({
            marker: player.marker,
            start: player.marker.getPosition(),
            end: player.latlng
        })
    },
    update: function () {
        if (mapObj == null || !focused) { return; }
        getPlayerLocation(function(location) {
            player.lat = parseFloat(location[0]);
            player.lng = parseFloat(location[1]);
            player.latlng = new google.maps.LatLng(player.lat, player.lng);
            mapObj.panTo(player.latlng);
            player.updateMarker();
        })
    }
}

function requester(r, fn, cb) {
    if (r == null) {
        alert("No response from " + fn + ". Server may be down.");
    } else if (typeof cb == 'function') {
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
    var fn = arguments.callee.name;

    $.ajax({
        url: 'location',
        type: 'GET',
        dataType: 'json',
        success: function(r) { requester(r["location"], fn, cb); }
    });
}

function createIcon(path) {
    var image = {
        url: path,
        scaledSize: new google.maps.Size(imgWidth, imgHeight)
    }
    return image;
}

function initializeMap() {
    console.log("initialize");
    console.log("Initializing map");
    mapObj = new google.maps.Map(document.getElementById('map'), {
          center: {lat: 37.4419, lng: -122.1419},
          zoom: 16,
          minZoom: 12
    });
}

$(function() {
    setInterval(getMapData, 5000);
    setInterval(player.update, 250)
})