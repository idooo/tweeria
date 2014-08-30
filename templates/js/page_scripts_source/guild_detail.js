$(function(){
    var $tabContainer = $("#guild-detail-page")
        , $tabHead = $(".guild-page-tab-header")
        , $tabHeadItem = $tabHead.find("li"),
        tabsByCode = {
        "#!tab-guild-info" : 0,
        "#!tab-guild-events" : 1
        },
        indexTab = (document.location.hash!=undefined) ? tabsByCode[document.location.hash] : 0;
    var tabHandlerShow = function (event, ui) {
        var iL = $tabHeadItem.length;
        $tabHeadItem.each(function (index) {
            var $this = $(this);

            if ($this.hasClass("ui-tabs-selected")) {
                $this.css({
                    "position":"relative",
                    "z-index":iL + 1
                });
            } else {
                $this.css({
                    "position":"relative",
                    "z-index":iL - index
                });
            }
        });
    };
    var tabSelectHandler = function (event, ui) {
        var scroll = $(document).scrollTop(),
            selected = tabs.tabs("option","selected"),
            href = ui.tab.pathname+ui.tab.hash.replace("#","#!");


        if (ui.index==selected) {
            event.preventDefault();
            if (selected>0)
                document.location = href;
        }
        document.location.hash = (ui.tab.hash != undefined) ? "!"+ui.tab.hash.substr(1) : "";

        $(document).scrollTop(scroll);
    };

    $(".looted-item-normal[data-tooltip], .monster[data-tooltip], .achv[data-tooltip], .dungeon[data-tooltip]").cluetip({
        // attribute:"rel"
        "titleAttribute": "data-tooltip",
        "splitTitle": "|"
    });

    var tabs = $tabContainer.tabs({
        selected: indexTab,
        show:tabHandlerShow,
        create:tabHandlerShow,
        select: tabSelectHandler
    });

    $(".guild-events-list .last-events-list li").on("mouseenter",function(){
        $(this).find(".twitter-event").fadeIn();
    })
        .on("mouseleave",function(){
            $(this).find(".twitter-event").fadeOut();
        });

    $(".submit-parent").on("click",function(e){
        e.preventDefault();
        $(this).parents("form").submit();
    });

    $(".guild-detail-table tbody tr").on("click",function(e){
        e.preventDefault();
        var href = $(this).find("a:first").attr("href");

        if (href!=""){
            document.location = href;
        }
    });

    $(".guild-invite-block .invite").on("click",function(e){
        e.preventDefault();
        var $this = $(this),
            url = $this.attr("href"),
            popupOptions = "menubar=no,location=no,resizable=yes,scrollbars=yes,status=no",
            popup = window.open(url,'Share',"width=565,height=480,"+popupOptions);
        popup.focus();
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
    }
});