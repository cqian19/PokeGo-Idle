/**
 * Created by cqian19 on 7/24/2016.
 */

var focused = true;
var mapObj = null;
var iconPath = "static/icons/"
var playerUpdateTime = 350;
var imgWidth = 45;
var imgHeight = 45;

var player = {
    img_name: 'player1',
    marker: '',
    dir : 'R', // Direction 'R' or 'L'
    lat: 0,
    lng: 0,
    latLng: null,
    posChanged: false,
    initializeMarker: function() {
        player.marker = new SlidingMarker({
            map: mapObj,
            position: player.latLng,
            icon: createIcon(player.getIconName()),
            optimized: false,
            zIndex: 2,
            visible: true,
            duration: playerUpdateTime
        })
        console.log(player.marker);
    },
    updateImage: function() {

    },
    getIconName: function() {
        return iconPath + player.img_name + player.dir + ".gif";
    },
    updateMarker: function() {
        if (mapObj == null) { return; }
        if (player.marker == '') { player.initializeMarker(); }
        var icon = player.marker.getIcon();
        var iconName = player.getIconName();
        if(icon.url != iconName) {
            icon.url = iconName;
            player.marker.setIcon(icon);
        }
        if (player.posChanged) {
            player.marker.setPosition(player.latLng);
            mapObj.panTo(player.latLng);
        }
    },
    update: function () {
        if (mapObj == null || !focused) { return; }
        getPlayerLocation(function(location) {
            player.lat = parseFloat(location[0]);
            var lng = parseFloat(location[1]);
            if (player.lng.toFixed(5) != lng.toFixed(5)) {
                player.posChanged = true;
                player.dir = player.lng > lng ? 'L' : 'R';
            } else {
                player.posChanged = false;
            }
            player.lng = lng;
            player.latLng = new google.maps.LatLng(player.lat, player.lng);
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
    console.log("Initializing map");
    mapObj = new google.maps.Map(document.getElementById('map'), {
          center: {lat: 37.4419, lng: -122.1419},
          zoom: 16,
          minZoom: 12
    });
    makeSliding();
    makeAnimate();
    setInterval(getMapData, 5000);
    setInterval(player.update, 250)
    console.log("Done")
}