/**
 * Created by cqian19 on 7/24/2016.
 */

var focused = true;
var mapObj = null;
var iconPath = "static/icons/";
var playerUpdateTime = 350;

var player = {
    img_name: 'player1',
    marker: '',
    dir : 'R', // Direction 'R' or 'L'
    lat: 0,
    lng: 0,
    latLng: null,
    posChanged: false,
    thread: null,
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
            setTimeout(function() { mapObj.panTo(player.latLng); }, playerUpdateTime/2.2);
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
        }, function() {
            console.log("Getting player data has failed");
        })
    }
};

var mapObjects = {
    displayedPokemon: {},
    displayedForts: {},
    thread: null,
    fortUpdating: false,
    pokemonUpdating: false,
    updateTime: 1000,
    _createPokemonMarker: function(poke, pokeSlot) {
        var marker = new google.maps.Marker({
            map: mapObj,
            position: new google.maps.LatLng(poke.latitude, poke.longitude),
            icon: createIcon(iconPath + poke.pokemon_id + '.png', 32, 32),

        });
        var infoWindow = new google.maps.InfoWindow({
            content: poke.name + "\t" + toTime(poke.time_remaining)
        });
        // Create and update marker notification with timer
        var thread; var opened = false;
        var update = function() {
            infoWindow.setContent(poke.name + "\t" + toTime(pokeSlot.timeLeft));
        }
        marker.addListener('mouseover', function() {
            if (!opened && !thread) {
                opened = true;
                thread = setInterval(update, 1);
                infoWindow.open(mapObj, this);
            }
        });
        marker.addListener('mouseout', function() {
            if (opened && thread) {
                opened = false;
                clearInterval(thread);
                thread = null;
                infoWindow.close();
            }
        });
        return marker;
    },
    updatePokemon: function(pokemonData) {
        if (mapObjects.pokemonUpdating) { return; }
        pokemonUpdating = true;
        var displayed = mapObjects.displayedPokemon;
        for (var key in pokemonData) {
            var poke = pokemonData[key];
            if (!(displayed[poke.encounter_id])) {
                var pokeSlot = {
                    timeLeft: Math.floor(poke.time_remaining),
                };
                pokeSlot.marker = mapObjects._createPokemonMarker(poke, pokeSlot);
                displayed[poke.encounter_id] = pokeSlot;
            }
        }
        for (var key in displayed) {
            pokeObj = displayed[key];
            pokeObj.timeLeft -= mapObjects.updateTime;
            if (pokeObj.timeLeft <= 0) {
                console.log("Pokemon disappeared");
                pokeObj.marker.setVisible(false);
                mapObjects.displayedPokemon[poke.encounter_id] = null;
                pokeObj = null;
            }
        }
        pokemonUpdating = false;
    },
    _createFortMarker: function(fort) {
        var marker = new google.maps.Marker({
            map: mapObj,
            position: new google.maps.LatLng(fort.latitude, fort.longitude),
            icon: createIcon(mapObjects._getFortIconName(fort), 32, 32)
        });
        return marker;
    },
    _getFortIconName: function(fort) {
        return iconPath + "pstop" + (fort.lure ? "lure" : "") + ".png"
    },
    updateForts: function(fortData) {
        console.log("UpdateForts");
        if (mapObjects.fortUpdating) { return; }
        mapObjects.fortUpdating = true;
        var f = {};
        var displayed = mapObjects.displayedForts;
        for (var key in fortData) {
            var fort = fortData[key];
            f[fort.id] = fort;
        }
        /*for (var key in displayed) {
            var marker = displayed[key].marker;
            var distToFort = google.maps.geometry.spherical.computeDistanceBetween(player.latLng, marker.getPosition());
            if (distToFort > 450 && marker.visible) {
                marker.setVisible(false);
            }
        }*/
        for (var key in f) {
            if (!displayed[key]) {
                displayed[key] = {
                    marker: mapObjects._createFortMarker(f[key]),
                    fort: f[key]
                }
            } else {
                var marker = displayed[key].marker;
                if (displayed[key].fort.lure != f[key].lure) {
                    console.log("Updating fort icon");
                    marker.setIcon(createIcon(mapObjects._getFortIconName(displayed[key].fort), 32, 32))
                }
                if (!marker.visible) {
                    marker.setVisible(true);
                }
            }
        }
        mapObjects.fortUpdating = false;
    },
    update: function() {
        if (mapObj == null) { return; }
        getMapData(function(data) {
            if (data["pokemon"] == undefined || data["forts"] == undefined) {
                alert("Error getting map data");
                return;
            }
            setTimeout(function() { mapObjects.updatePokemon(data["pokemon"]) }, 0);
            setTimeout(function() { mapObjects.updateForts(data["forts"]) }, 0);
        }, function() {
            console.log("Getting map data has failed");
        })
    }
};
function requester(r, fn, cb) {
    if (r == null) {
        alert("No response from " + fn + ". Server may be down.");
    } else if (typeof cb == 'function') {
        cb(r);
    }
}

function getMapData(cb, f) {
    $.ajax({
        url: 'data',
        type: 'GET',
        dataType: 'json',
    }).done(function(r) {
        requester(r, arguments.callee.name, cb);
    }).fail(f);
}

function getPlayerLocation(cb, f) {
    var location;
    var fn = arguments.callee.name;

    $.ajax({
        url: 'location',
        type: 'GET',
        dataType: 'json'
    }).done(function(r) {
        requester(r["location"], fn, cb);
    }).fail(f);
}

function toTime(ms) {
    if (ms <= 0) { return "0"; }
    seconds = Math.floor((ms/1000)%60);
    minutes = Math.floor((ms/(1000*60))%60);
    hours = Math.floor((ms/(1000*60*60))%24);
    s = "";
    if (hours) {
        s += hours + ":";
    }
    s += minutes + ":";
    s += seconds < 10 ? "0" + seconds : seconds;
    return s;
}

function createIcon(path, width, height) {
    var image = {
        url: path,
        scaledSize: new google.maps.Size(width, height)
    };
    return image;
}

function initializeMap() {
    console.log("Initializing map");
    mapObj = new google.maps.Map(document.getElementById('map'), {
          center: {lat: 37.4419, lng: -122.1419},
          zoom: 16,
          minZoom: 5
    });
    makeSliding();
    makeAnimate();
    setInterval(getMapData, 5000);
    player.thread = setInterval(player.update, 250);
    mapObjects.thread = setInterval(mapObjects.update, mapObjects.updateTime);
    console.log("Done");
}