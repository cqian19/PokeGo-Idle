/**
 * Created by cqian19 on 7/30/2016.
 */

var lastxp = 0;

playerInfo = {
    updateTime: 2000,
    update: function() {
        getPlayerData(parsePlayerData, function() { console.log("Get player info failed"); });
    }
};

function getPlayerData(cb, f) {
    $.ajax({
        url: 'playerData',
        type: 'GET',
        dataType: 'json'
    }).done(function(r) {
        requester(r, arguments.callee.name, cb);
    }).fail(f);
}

function parsePlayerData(playerData) {
    console.log(playerData);
    var card = $(".playerCard");
    var image = card.find(".playerImage");
    var avaName = imagePath + 'trainer' + (playerData.gender == 'Male' ? 'M' : 'F') + '.png';
    if (image.attr("src") != avaName) {
        image.attr("src", avaName)
    }
    var name = card.find(".playerName");
    var username = playerData.username + " Lv. " + playerData.level;
    if (name.text() != username) {
        name.text(username);
    }
    var exp = card.find(".exp");
    var expText = "Exp:  " + playerData.xp + " / " + playerData.maxXp;
    var expBar = $(".xpBar");
    if (exp.text() != expText) {
        exp.text(expText);
        var xpInt = parseInt(playerData.xp);
        var newW = expBar.parent().width() * xpInt / parseInt(playerData.maxXp);
        if (xpInt != lastxp) {
            if (xpInt > lastxp) {
                 $(expBar).animate({
                    width: newW
                 }, 500, 'easeOutQuart')
            } else {
                 $(expBar).animate({
                    width: expBar.parent().width()
                 }, 2000, 'easeOutQuart', function() {
                     expBar.attr('width', 0);
                     $(expBar).animate({
                         width: newW
                     }, 500, 'easeOutQuart')
                 })
            }
            lastxp = xpInt;
        }

    }
    var stardust = card.find("#stardust");
    var sdamount = "Stardust:  " + playerData.stardust;
    if (stardust.text() != sdamount) {
        stardust.text(sdamount);
    }
    var pokecoin = card.find("#pokecoin");
    var pcamount = "Pokecoins:  " + playerData.pokecoin;
    if (pokecoin.text() != pcamount){
        pokecoin.text(pcamount);
    }
}