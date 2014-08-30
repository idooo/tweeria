$(function(){
    var $playerConfigLink    = $(".player-pvp-status-toggler"),
        $popupTmpl      = $("#pvp-popup-template"),
        $changeSpell    = $("#change-spell");

    /**
     * init player hp-mp bars
     */
    $(".player-hp-mp-text").each(function(){
        $(this).parent().width($(this).outerWidth());
        $(this).show();
    });

    $changeSpell.on("click",function(event){
        event.preventDefault();
        event.stopPropagation();

        $.fancybox($("#changespell-popup").tmpl(),{
            "closeBtn"  : false,
            "wrapCSS"   : "tweenk-popup",
            "padding"   : [20,20,20,20],
            "helpers"   :  {
                "overlay" : {
                    "css" : {
                        "background": "transparent"
                    }
                }
            }
        });
    });

    $(".player-spells .player-slot-list li a").cluetip({splitTitle:'|'});
    $(".player-wealth .player-slot-list li a.with-tooltip").cluetip();

    $(".last-events-list .monster, .last-events-list .looted-item-normal, .last-events-list .dungeon, .last-events-list .achv, .last-events-list .poi").cluetip();

    $(".player-name-guild-rc h1.toggler").on("click",function(event){
        event.preventDefault();
        $("#player-tabs").tabs("select",0);
    });

    $(".buff-debuff-list img").cluetip({
        splitTitle: "|"
    });

    $(document).on("change","#post_to_twitter",function(){
        var $form = $(this).parents("form");
        $form.ajaxForm();
        $form.submit();
    });

    $(".player-items img[data-popup='1'], .player-inventory img[data-popup='1']").on("click", function (event) {
        event.preventDefault();
        event.stopPropagation();

        var data = $(this).data(),
            bonusparsed = {};

        data.bonus = (data.bonus == undefined) ? "" : data.bonus;

        if (data.bonus != "") {
            bonusparsed = JSON.parse(data.bonus.replace(/'/g, "\""));
        }

        data.bonusparsed = {};
        $.each(bonusparsed, function (index, value) {
            data.bonusparsed[index] = "+" + value['value'] + " " + value['name'];
        });

        $.fancybox($("#player-item-popup").tmpl(data), {//item popup
            closeBtn:false,
            wrapCSS:"tweenk-popup",
            padding: 0,
            autoSize: true,
            helpers:{
                overlay:{
                    css:{
                        "background":"transparent"
                    }
                }
            }
        });
    });


    if (typeof inviterData != "undefined"){
        $.fancybox($("#invited-block").tmpl(inviterData),{
            "closeBtn"  : false,
            "wrapCSS"   : "tweenk-popup",
            "padding"   : 0,
            "helpers"   :  {
                "overlay" : {
                    "css" : {
                        //"background": "transparent"
                    }
                }
            }
        });

        var currentSlide = 0,
            $ul = $(".quick-tour-block").find("ul:first"),
            elLength = $ul.find("li").size(),
            $prevButton = $(".quick-tour-prev"),
            $nextButton = $(".quick-tour-next");

        $(".quick-tour").on("click",function(e){
            e.preventDefault();
            $(this).hide();

            $(".invite-fade-block").fadeOut("slow",function(){
                $(".quick-tour-block").fadeIn("slow");
                $.fancybox.update();
            });

            return false;
        });


        $ul.on("click",".quick-tour-prev, .quick-tour-next",function(e){
            e.preventDefault();
            var $this = $(this),
                back = ($this.hasClass("quick-tour-prev")) ? true : false;

            if (back && currentSlide>0){
                $nextButton.show();
                $ul.animate({
                    "margin-left": "+=502"
                },"slow");
                currentSlide-=1;
                if (currentSlide==0){
                    $prevButton.hide();
                }
            } else if (!back && currentSlide<elLength-1) {
                $prevButton.show();
                $ul.animate({
                    "margin-left": "-=502"
                },"slow");
                currentSlide+=1;
                if (currentSlide==elLength-1){
                    $nextButton.hide();
                }
            }
        });
    }
});
