/**
 * Created by cqian19 on 7/24/2016.
 */

var focused = true;
var mapObj = null;
var iconPath = "static/icons/";
var imagePath = "static/images/";
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
    updateTime: 500,
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
    caughtPokemon: {},
    thread: null,
    fortUpdating: false,
    pokemonUpdating: false,
    updateTime: 1000,
    lastPokemonData: {},
    lastCaughtPokemonData: {},
    _createPokemonMarker: function(poke, pokeSlot) {
        var marker = new google.maps.Marker({
            map: mapObj,
            position: new google.maps.LatLng(poke.latitude, poke.longitude),
            icon: createIcon(iconPath + poke.pokemon_id + '.png', 32, 32),
            zIndex: 1
        });

        var myOptions = {
             content: "<div class=\"pokeinfo\">" + toTime(poke.time_remaining) + "</div>"
            ,disableAutoPan: false
            ,pixelOffset: new google.maps.Size(-13, -5)
            ,zIndex: null
            ,isHidden: false
            ,pane: "floatPane"
            ,closeBoxURL: ""
            ,enableEventPropagation: false
        };
        var infoWindow = new InfoBox(myOptions);
        marker.infoWindow = infoWindow;
        infoWindow.open(mapObj, marker);
        // Create and update marker notification with timer
        infoWindow.update = function() {
            infoWindow.setContent("<div class=\"pokeinfo\">" + toTime(pokeSlot.timeLeft) + "</div>");
        };
        return marker;
    },
    updatePokemon: function(pokemonData, caughtPokemonData) {
        if (mapObjects.pokemonUpdating) { return; }
        mapObjects.lastPokemonData = pokemonData;
        mapObjects.lastCaughtPokemonData = caughtPokemonData;
        pokemonUpdating = true;
        console.log(pokemonData);
        var displayed = mapObjects.displayedPokemon;
        // Add new pokemon to display
        for (var key in pokemonData) {
            var poke = pokemonData[key];
            if (poke.encounter_id in mapObjects.caughtPokemon) { continue; }
            if (!(displayed[poke.encounter_id])) {
                // BUG: Some pokemon have negative time remaining
                var pokeSlot = {
                    timeLeft: poke.time_remaining < - 1000 ? 'Unknown' : Math.floor(poke.time_remaining),
                };
                pokeSlot.marker = mapObjects._createPokemonMarker(poke, pokeSlot);
                displayed[poke.encounter_id] = pokeSlot;
            }
        }
        // Decrease seconds remaining for all pokemon
        for (var key in displayed) {
            pokeObj = displayed[key];
            if (typeof pokeObj.timeLeft != 'string') {
                pokeObj.timeLeft -= mapObjects.updateTime;
                if (pokeObj.timeLeft <= 0) {
                    console.log("Pokemon disappeared");
                    pokeObj.marker.setMap(null);
                    pokeObj.marker.infoWindow.close();
                    delete displayed[key];
                } else {
                    pokeObj.marker.infoWindow.update();
                }
            }
        }
        // Hide all caught pokemon
        for (var key in caughtPokemonData) {
            var poke = caughtPokemonData[key];
            caughtPokemonData[poke.encounter_id] = poke;
            if (poke.encounter_id in displayed) {
                var pokeObj = displayed[poke.encounter_id];
                pokeObj.marker.setMap(null);
                pokeObj.marker.infoWindow.close();
                delete displayed[key];
            }
        }
        pokemonUpdating = false;
    },
    _createFortMarker: function(fort) {
        var marker = new google.maps.Marker({
            map: mapObj,
            position: new google.maps.LatLng(fort.latitude, fort.longitude),
            icon: createIcon(mapObjects._getFortIconName(fort), 32, 32),
            zIndex: 0
        });
        return marker;
    },
    _getFortIconName: function(fort) {
        return iconPath + "pstop" + (fort.lure ? "lure" : "") + ".png"
    },
    updateForts: function(fortData) {
        if (mapObjects.fortUpdating) { return; }
        console.log("Updating forts");
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
        // Display new forts or update image
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
                    marker.setIcon(createIcon(mapObjects._getFortIconName(displayed[key].fort), 32, 32));
                    displayed[key].fort.lure = f[key].lure;
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
            for (key in data) {
                if (data[key] == undefined) {
                    console.log("Error getting map data");
                    return;
                }
            }
            setTimeout(function() { mapObjects.updatePokemon(data["pokemon"], data["caughtPokemon"]) }, 0);
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
        dataType: 'json'
    }).done(function(r) {
        requester(r, arguments.callee.name, cb);
    }).fail(f);
}

function equals(d1, d2) {
    return JSON.stringify(d1) === JSON.stringify(d2);
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
    if (typeof ms == 'string') { return ms; }
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
          minZoom: 4
    });
    makeSliding();
    makeBox();
    makeAnimate();
    console.log("Done");
}

// Search bar initialize
var searchBar = $("#search");
var searchSub = $("#searchSubmit");
searchSub.click(search);
searchBar.on("keypress",function(e) {
    if (e.which === 13) {
        search();
    }
});
function search() {
    var location = searchBar.val();
    console.log("LOCATION", location);
    if (!location) { return; }
    searchBar.val("Search being processed.");
    searchBar.prop("disabled", true);
    searchSub.prop("disabled", true);
    $.ajax({
        url: 'search',
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({'location': location })
    }).done(function (r) {
        if (r["status"] != "1") {
            searchBar.val("Search failed.");
        } else {
            searchBar.val("Search succeeded!");
        }
        setTimeout(function() { searchBar.prop("disabled", false); searchSub.prop("disabled", false); searchBar.val(location)}, 2000);
    }).fail(function(r) {
        searchBar.val("Response could not go through.");
        setTimeout(function() { searchBar.prop("disabled", false); searchSub.prop("disabled", false); searchBar.val(location)}, 2000);
    })
}
// User config initialize
$(".configOpt").find("button").click(function() {
    var input = $(this).siblings("input");
    var option = input.attr("name");
    var value = input.val();
    var d = {};
    d[option] = value;
    $.ajax({
        url: 'config',
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify(d)
    })
});
// Start all object threads
$(function() {
    var threads = [player, mapObjects, notifications, playerInfo];

    function startThreads() {
        for (i in threads) {
            obj = threads[i];
            i.thread = setInterval(obj.update, obj.updateTime);
        }
    }

    function waitForLogin() {
        $.ajax({
            url: 'loggedIn',
            type: 'GET',
            dataType: 'json'
        }).done(function (r) {
            console.log(r);
            if (r["status"] == "1") {
                startThreads();
                clearInterval(loginThread);
            }
        })
    }

    loginThread = setTimeout(waitForLogin, 2000);
});