/**
 * Created by cqian19 on 7/24/2016.
 */

function getMapData() {
    $.ajax({
        url: 'data',
        type: 'GET',
        dataType: 'json'
    }).done(function(r) {
        console.log(r);
    });
}

setInterval(getMapData, 5000)