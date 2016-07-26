/**
 * Created by cqian19 on 7/24/2016.
 */

var focused = true;
var mapObj = null;
var iconPath = "static/icons/"
var playerUpdateTime = 350;

var player = {
    img_name: 'player1',
    marker: '',
    dir : 'R', // Direction 'R' or 'L'
    lat: 0,
    lng: 0,
    latLng: null,
    posChanged: false,
    initializeMarker: function() {
        if (player.marker) { return; }
        player.marker = new SlidingMarker({
            map: mapObj,
            position: player.latLng,
            icon: createIcon(player.getIconName(), 45, 45),
            optimized: false,
            duration: playerUpdateTime,
            easing: 'linear',
            zIndex: 2,
            visible: true
        })
    },
    updateImage: function() {
        // Different player gifs?
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
            setTimeout(function() { mapObj.panTo(player.latLng); }, playerUpdateTime/2.35);
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

var mapObjects = {
    displayedPokemon: {},
    displayedForts: {},
    _createPokemonMarker: function(poke) {
        console.log(poke);
        var marker = new google.maps.Marker({
            map: mapObj,
            position: new google.maps.LatLng(poke.latitude, poke.longitude),
            icon: createIcon(iconPath + poke.pokemon_id + '.png', 32, 32)
        })
        return marker;
    },
    updatePokemon: function(pokemonData) {
        for (var key in pokemonData) {
            var poke = pokemonData[key];
            if (!mapObjects.displayedPokemon[poke.encounter_id]) {
                mapObjects.displayedPokemon[poke.encounter_id] = mapObjects._createPokemonMarker(poke);
            }
        }
    },
    updateForts: function(fortData) {

    },
    update: function() {
        if (mapObj == null) { return; }
        getMapData(function(data) {
            if (data["pokemon"] == undefined || data["forts"] == undefined) {
                alert("Error getting map data");
                return;
            }
            mapObjects.updatePokemon(data["pokemon"]);
            mapObjects.updateForts(data["forts"]);
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

function createIcon(path, width, height) {
    var image = {
        url: path,
        scaledSize: new google.maps.Size(width, height)
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
    setInterval(player.update, 250);
    setInterval(mapObjects.update, 2000);
    console.log("Done");
}