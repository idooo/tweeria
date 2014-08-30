/* Author:Elfrey

 */


$(function(){
    inits();
    fixes();
});

$(window).resize(function(){
    fixes();
});

var inits = function(){
    if ($.browser.msie){
        $("html").toggleClass("ie");
    }
    if ($.browser.opera){
        $("html").toggleClass("opera");
    }

    initProfileMenu();

    initToolTips();
    initMainItemSlide();
    /**
     * Player page
     */
    initInvTabs($("#player-tabs"));


    changeOperaOutline();
};

var fixes = function(){

    /**
     * Player page
     */
    fixHpMpBar($(".player-current-hp-mp"));
    fixPlayeArt($(".player-art"));
};

var initToolTips = function(remove){

    remove = (remove === undefined) ? false: remove;


    if (remove){
        $(".player-items img")
            .cluetip("destroy");

        $(".player-inventory img")
            .cluetip("destroy");

        $("#player_achvs .achvs .achv")
            .cluetip("destroy");
    }else{
        if ($(".player-items img").size()>0){
            $(".player-items img")
                .cluetip("destroy");

            $(".player-items img[data-tooltip]").cluetip({
                "titleAttribute":"data-tooltip",
                "splitTitle":"|"
            });
        }

        if ($(".player-inventory img").size()>0){
            $(".player-inventory img")
                .cluetip("destroy");
            $(".player-inventory img[data-tooltip]").cluetip({
                "titleAttribute":"data-tooltip",
                "splitTitle":"|"
            });
        }
        if ( $("#player_achvs .achvs .achv").size()>0){
            $("#player_achvs .achvs .achv")
                .cluetip("destroy")
                .cluetip({
                    "titleAttribute":"data-tooltip",
                    "splitTitle":"|"
                });
        }
    }
};

var fixHpMpBar = function($hpMpBarCurrent){
    $hpMpBarCurrent = ($hpMpBarCurrent == undefined) ? $(".player-current-hp-mp") : $hpMpBarCurrent;
    $hpMpBarCurrent.each(function(){
        var $this = $(this),
            width = parseInt(( 100 * parseInt($this.css('width')) / parseInt($this.parent().css('width'))));


        if (width==99){
            $this.css("border-top-right-radius","3px");
            $this.css("border-bottom-right-radius","3px");
        }else if(width==98){
            $this.css("border-top-right-radius","1px");
            $this.css("border-bottom-right-radius","1px");
        }else if(width<98){
            $this.css("border-top-right-radius","0px");
            $this.css("border-bottom-right-radius","0px");
        }
    });
};

var fixPlayeArt = function($art){
    $art = ($art == undefined) ? $(".player-art") : $art;
    var $prev = $art.prev(), prW = $prev.outerWidth(true),
        $next = $art.next(), nW = $next.outerWidth(true),
        $parent = $art.parent(), pW = $parent.width();

    $art.width(pW-prW-nW-1);
};

var initInvTabs = function($tabs){
    $tabs = ($tabs == undefined) ? $("#player-tabs") : $tabs;
    var tab = $tabs.tabs({
        show: function(event,ui){
            if (ui.index==0){
                $(".player-name-guild-rc h1").removeClass("toggler");
            } else {
                $(".player-name-guild-rc h1").addClass("toggler");
            }
        },
        create: function(event,ui){
            $("#tab-overlay").hide();
            $("#player-tabs").show();
        }
    });

};

var changeOperaOutline = function(){
    if ($.browser.opera){
        var $outlineItems =  $("#main *").filter(function(){
            var $this = $(this);
            return $this.css("outline-style") == "solid";
        });
        $outlineItems.each(function(){
            var $this = $(this),
                $wrapper = $("<div />").css({
                    "border" : $this.css("outline")
                });

            $this.wrap($wrapper);
            $this.css("outline","none");
        });
    }
};


var initMainItemSlide = function(){
    if (!$(".new-items-list li").length){
        return false;
    }
    var $scrollBlock    = $(".new-items-list"),
        $buttons        = $(".new-in-shop-selector");

    $buttons.on("click",function(){
        var $this = $(this),
            page = $this.index(),
            ml = page*480*-1;

        $scrollBlock.animate({
            "margin-left": ml
        });
        $this.addClass("active").siblings(".active").removeClass("active");
    });
};


var initProfileMenu = function(){
    if ($(".header-player-block").size()==0)
        return false;

    var $opener = $(".header-player-menu-opener"),
        $menu = $(".header-player-menu");

    $opener.on("click",function(e){
        e.preventDefault();
        var $this = $(this);
        if (!$menu.is(":visible")){
            $this.addClass("opened");
            $menu.show();

            $(".player-mark,.player-map-list").css("z-index",1);

            $(document).on("click.popup",function(event){
                var $target = $(event.target);
                if ($target.parents(".header-player-menu").size()==0 && !$target.hasClass("header-player-menu")
                    &&
                    $target.parents(".header-player-menu-opener").size()==0 && !$target.hasClass("header-player-menu-opener")){
                    $menu.hide();
                    $opener.removeClass("opened");
                    $(document).off(".popup");
                    $(".player-mark").css("z-index",101);
                    $(".player-map-list").css("z-index",100);
                }
            });
        }else{
            $this.removeClass("opened");
            $menu.hide();
            $(".player-mark").css("z-index",101);
            $(".player-map-list").css("z-index",100);
            $(document).off(".popup");
        }
    });
};