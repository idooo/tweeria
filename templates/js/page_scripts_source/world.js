$(function(){
    var showPlacesOnMap = function($map){

        if (typeof placesData === "undefined"){
            return false;
        }


        //выбор слоя
        /*$map.parent().parent().prepend('<div class="layer-toggler-wrap"><div class="layer-toggler">' +
            '<a href="#players" data-layer="player" class="toggler active">Players</a>' +
            '<a href="#places" data-layer="place" id="place-toggler" class="toggler">Location</a>' +
            '<a href="/help" class="help">Help</a>' +
            '</div></div>').on("click",".layer-toggler .toggler",function(e){
                e.preventDefault();
                var $this = $(this),
                    $layer = $("#"+$this.data("layer")+'-layer');

                if ($layer.size()>0){
                    $layer.show().siblings(".map-layer").hide();
                    $this.addClass("active").siblings(".toggler.active").removeClass("active");
                }
            });*/

        var $tmpItem = {},
            $placeList = {},
            $place = {},
            placeClass = "place-map-title",
            types = {0: "Dungeon", 1:"Raid"},
            $placesLayer = $('<div id="place-layer" class="map-layer"></div>').appendTo($map);
        $.each(placesData,function(placeInd,placeData){
            $tmpItem = $("<div />",{
                "class": "place-mark",
                "css": {
                    "top"       : placeData.pos.y+"px",
                    "left"      : placeData.pos.x+"px",
                    "position"  : "absolute"
                }
            });
            if (placeData.gotomap){
                $tmpItem.addClass("gotomap").data({
                    "x": placeData.pos.x,
                    "y": placeData.pos.y,
                    "name": placeData.name
                });
            }

            if (placeData.places[0].max_players>1)
                console.log(placeData);//TODO снести нахер

            $placeList = $("<ul />",{
                "class" : "place-map-list",
                "css": {
                    "top"       : placeData.pos.y+"px",
                    "left"      : placeData.pos.x+"px",
                    "position"  : "absolute"
                }
            });
            $.each(placeData.places,function(index,place){
                var lvl = 1,
                    max_players = 1;
                placeClass = "place-map-title";
                if (place.current){
                    placeClass = "place-map-title-current";
                    $tmpItem.addClass("current-place-mark");
                }
                $place = $('<li>' +
                    '<span class="'+placeClass+'">'+place['name']+'</span>' +

                    '</li>');
                if (place.lvl_min>0){
                    lvl = place.lvl_min;
                }else if (place.lvl_max>0){
                    lvl = place.lvl_max;
                }
                if (place.type==0){
                    $place.append('<span class="place-map-info">'+types[place['type']]+', level '+lvl+'</span>');
                }else if (place.type==1){

                    if (place.max_players>0){
                        max_players = place.max_players;
                    }

                    $place.append('<span class="place-map-info">'+types[place['type']]+', level '+lvl+' for '+max_players+' players</span>');
                    $place.append('<a href="/events/new?hash='+place.hash+'" class="create-raid">Create raid</a>');
                }else{
                    $place.append('<span class="place-map-info">'+place['desc']+'</span>');
                }
                $place.append('<span class="place-go"><a href="https://twitter.com/intent/tweet?hashtags='+place.hash+'&text=">Tweet #'+place.hash+'</a> to&nbsp;go&nbsp;here</a></span>');
                $placeList.append($place);
            });

            $placeList.find("li:first").append('<span class="close-place-map-list">x</span>');
            $placesLayer.append($tmpItem);
            $placesLayer.append($placeList);
        });


        $map.on("click",".place-mark",function(event){
            var $this = $(this),
                $currentList = $this.next();



            if ($this.hasClass("gotomap")){
                document.location="/u/world?x="+$this.data("x")+"&y="+$this.data("y");
            }else{
                $currentList.toggle().siblings(".place-map-list").hide();
                $this.siblings(".active").removeClass("active");
                $this.toggleClass("active");

                if ($currentList.is(":visible")){
                    $this.css("z-index","103").siblings(".place-mark").css("z-index","101");
                    $currentList.css("z-index","102").siblings(".place-map-list").css("z-index",100);
                }else{
                    $this.css("z-index","101").siblings(".place-mark").css("z-index","101");
                    $currentList.css("z-index","100").siblings(".place-map-list").css("z-index",100);
                }
            }
        })
            .on("click",".place-map-title,.place-map-title-current",function(event){
                document.location = $(this).attr("href");
                return false;
            })
            .on("click",".close-place-map-list",function(){
                var $this = $(this),
                    $currentList = $this.parents(".place-map-list"),
                    $mart = $currentList.prev();

                $currentList.hide();
                $(".place-mark").css("z-index","101");
                $(".place-map-list").css("z-index",100);
            });



    };

    showPlacesOnMap($("#map-sprite .global-map"));

    if (typeof currentPlayer != "undefined"){
        addPlayerMark(currentPlayer,$("#place-layer"));
    }

    if (document.location.hash == "#places"){
        $("#place-toggler").click();
    }
    $("#player-layer").show();
    $("#place-layer").show();
});