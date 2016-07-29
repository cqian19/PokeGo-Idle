/**
 * Created by cqian19 on 7/28/2016.
 */

infoParsers = {
    'pokemonEvent': parsePokemon
}

function parsePokemon(poke) {
    var header;
    var pokeName = poke.name.capitalizeFirstLetter();
    switch(poke.status) {
        case 'Caught':
            header = pokeName + " (CP: " + poke.cp + ")" + " caught!";
            content = "Caught on:\t" + getTime(poke.timestamp) + "<br>"
                      "Rewards:  ";
            var first = true;
            for (key in poke.award) {
                if (first) {
                    content += key.capitalizeFirstLetter() + "x" + poke.award[key];
                    first = false;
                } else {
                    content += "  " + key.capitalizeFirstLetter() + "x" + poke.award[key];
                }
            }
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
    }
    appendNotification(d);
}

function appendNotification(info) {
    var container = $(".notificationContainer");
    var note = $("<div class=\"notification\">");
    var iconCont = $("<div class =\"iconContainer\">");
    note.append(iconCont);
    iconCont.append($("<img class=\"icon\">").attr("src", info.icon));
    var inner = ($("<div class=\"container\">"));
    note.append(inner)
    inner.append($("<tbody>"))
        .append($("<td>"))
        .append($("<tr>"))
        .append($("<div class=\"noteHeader\">").text(info.header))
        .append($("<tr>"))
        .append($("<div class=\"noteBody\">").text(info.content))
        .append($("</tbody>"));
    container.prepend(note);
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