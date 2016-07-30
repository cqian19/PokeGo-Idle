/**
 * Created by cqian19 on 7/28/2016.
 */

infoParsers = {
    'pokemonEvent': parsePokemon,
    'stopEvent': parseStop
}

function parsePokemon(poke) {
    console.log("New pokemon")
    var header;
    var pokeName = poke.name.capitalizeFirstLetter();
    switch(poke.status) {
        case 'Caught':
            header = pokeName + " (CP: " + poke.cp + ")" + " caught!";
            content = "Caught at\t" + getTime(poke.timestamp) + "\n" +
                      "Rewards:  ";
            break;
        case 'Fled':
            header = pokeName + " (CP: " + poke.cp + ")" + " has fled!";
            content = pokeName + " fled. " + getTime(poke.timestamp);
            break;
        case 'Failed':
            header = poke.name.capitalizeFirstLetter() + " (CP: " + poke.cp + ")" + " could not be caught.";
            content = pokeName + " escaped too many times. " + getTime(poke.timestamp);
            break;
    }
    d = {
        icon: iconPath + poke.id +'.png',
        header: header,
        content: content
    };
    appendNotification(d, poke.hasAward ? poke.award : []);
}

function parseStop(stop) {
    console.log("New stop");
    d = {
        icon: iconPath + 'pstop' + (stop.lure ? 'lure' : '') + '.png',
        header: 'Pokestop has been visited!',
        content: 'Visited at\t' + getTime(stop.timestamp) + '\n' +
                 'Rewards:'
    }
    appendNotification(d, stop.award);
}

function appendNotification(info, additional) {
    var note = $("<div class=\"notification\">");
    var iconCont = $("<div class =\"iconContainer\">");
    note.append(iconCont);
    iconCont.append($("<img class=\"icon\">").attr("src", info.icon));
    var inner = ($("<div class=\"container\">"));
    note.append(inner);
    inner.append($("<table>")
        .append($("<tbody>"))
            .append($("<tr>")
            .append($("<div class=\"noteHeader\">").text(info.header)))
            .append($("<tr>")
            .append(list = $("<div class=\"noteBody\">").text(info.content)))
        );
        if (additional) {
            var l = $("<ul>");
            for (key in additional) {
                console.log(key);
                l.append($("<li class='reward'>").text(key.replace('_', ' ') + ": " + additional[key]));
            }
            list.append(l);
        }
    inner.append("</tbody></table>");
    prependAndShift(note);

}

function prependAndShift(note) {
    var container = $(".notificationContainer");
    container.prepend(note);
    var sep = 10;
    var height = note.height() + sep;
    var max = 800;
    note.remove();
    container.children().each(function(i, child) {
        child = $(child);
        if (height >= max) {
            child.remove();
        } else {
            $(child).animate({
                top: height
            }, 200);
            height += child.height() + sep;
        }
    });
    container.prepend(note.hide().fadeIn(1000));
    note.fadeIn(1000);
    console.log(note.height());
}

function parsePastInfo(pastInfo) {
    for (key in pastInfo) {
        info = pastInfo[key];
        console.log(info);
        if (info['event'] in infoParsers) {
            infoParsers[info['event']](info);
        } else {
            console.log("Error info type " + info.type + " not in parsers");
        }
    }
}

function getPastInfo(cb, f) {
    $.ajax({
        url: 'pastInfo',
        type: 'GET',
        dataType: 'json'
    }).done(function(r) {
        requester(r, arguments.callee.name, cb);
    }).fail(f);
}

function update() {
    getPastInfo(parsePastInfo, function() { console.log("Get past info failed"); });
}

setInterval(update, 1000);

function getTime(t) {
    var diff = new Date().getTimezoneOffset();
    return (new Date(t - diff * 60000)).toLocaleTimeString()
}

String.prototype.capitalizeFirstLetter = function() {
    return this.charAt(0).toUpperCase() + this.toLowerCase().slice(1);
}
setTimeout(function() {
    parsePokemon({
        status: 'Caught',
        name: 'Pokeball',
        timestamp: 1,
        cp: 1000,
        id: 1,
        hasAward: true,
        award: {
            'candy': 3,
            'xp': 210,
            'stardust': 300
        }
    })
}, 5000);