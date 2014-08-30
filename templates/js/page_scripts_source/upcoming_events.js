$(function () {
    var eventPlayers = {},
        eventDef = {},
        $eventFormBlock = $(".new-event-form"),
        $tabHead = $(".event-type-head"),
        $tabContainer = $(".new-event-tabs"),
        $tabHeadItem = $tabHead.find("li"),
        $eventTypeSelect = $("#event-type"),
        $eventTypeBlocks = $(".event-type-depend"),
        $dungeonSelect = $("#dungeon"),
        $eventTypeTogglers = $(".new-event-type-toggler"),
        tabHandlerShow = function (event, ui) {

            var iL = $tabHeadItem.length,
                currentType = $(ui.tab).data(),
                $currentOption = $eventTypeSelect.find("option[name='" + currentType + "']");

            $currentOption.attr("selected", "selected").siblings().removeAttr("selected");

            $('#event_type_field').val($(ui.tab).data('type'))

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

    $tabContainer.tabs({
        show:tabHandlerShow,
        create:tabHandlerShow
    });

    var $datepickerInput = $eventFormBlock.find(".new-event-time").datetimepicker({
            dateFormat:"dd.mm.yy",
            showOtherMonths:true,
            dayNamesMin:["end", "M", "T", "W", "T", "F", "Week"],
            firstDay:1,
            beforeShow:function () {
                var $datePickerOverlay = {};
                if (!$("#datepicker-overlay").length) {
                    $datePickerOverlay = $("<div />", {
                        "id":"datepicker-overlay",
                        css:{
                            "width":$(document).width(),
                            "height":$(document).height(),
                            "zIndex":parseInt($(".fancybox-opened").css("z-index")),
                            "background":"transparent",
                            "position":"absolute",
                            "top":"0",
                            "left":"0",
                            "display":"none"
                        }

                    });
                    $("body").append($datePickerOverlay);
                } else {
                    $datePickerOverlay = $("#datepicker-overlay");
                }
                $datePickerOverlay.show();

            },
            onClose:function () {
                $("#datepicker-overlay").hide();
            }
        }),
        $datepicker = $("#ui-datepicker-div").addClass("tweenk-datepicker");

    $datepickerInput.on("focus", function () {
        $datepicker.css({
            "top":"100px"
        });
    });

    var initUpcomingListDetailPreview = function () {
        if ($(".upcoming-event-table").length == 0) return false;

        $(".upcoming-event-table tbody tr td").on("click", function (e) {

            e.preventDefault();
            e.stopPropagation();

            var tmp = {},
                $this = $(this).parent(),
                data = $this.data(),
                eventId = data['_id'],
                urlForAjax = "/u/events/?type_of_form=get_event_players&event_id=" + data["_id"];

            document.location = "/events/" + data["_id"];
            return false;
            /*
             if (typeof eventPlayers[eventId] === "undefined" ) {
             eventDef[eventId] = $.ajax({
             url     : urlForAjax,
             type    : "get",
             dataType: "text",
             success : function(responceData){
             eventPlayers[eventId] = $.parseJSON(responceData)
             }
             });
             }

             eventDef[eventId].done(function(){
             data['people_count'] = eventPlayers[data['_id']]['players'].length;
             data['players'] = eventPlayers[data['_id']]['players'];

             var $tmpl = $("#event-detail-template").tmpl(data);

             $this.attr("data-playernew",true);

             $.fancybox($tmpl[0],{
             closeBtn : false,
             wrapCSS  : "tweenk-popup",
             padding: [0,0,0,0],
             width: 535,
             maxWidth: 535,
             helpers  :  {
             overlay : {
             css: {
             "background": "transparent"
             }
             }
             },
             afterLoad: function(){
             $.fancybox.update();

             }
             });
             });
             */

        });
    };
    $dungeonSelect.uniform();
    $eventTypeTogglers.on("click", function (e) {
        e.preventDefault();

        var $this = $(this),
            type = $this.data("type");
        if ($this.hasClass("active")) return false;
        $eventTypeBlocks.hide();
        $eventTypeTogglers.removeClass("active");
        $this.addClass("active");
        $("." + type + "-block").show();

        $('#event_type_field').val(type)

    });


    initUpcomingListDetailPreview();


    //Автокомплит для поиска гильдии
    var minSearchLength = 1,
        $guildInput = $("#guild"),
        selected = false,
        $guildAutpComplete = $guildInput.autocomplete({
            source:function (request, response) {
                $.ajax({
                    url:"/guilds",
                    dataType:"json",
                    type:"get",
                    data:{
                        find:request.term
                    },
                    success:function (data) {
                        selected = false;
                        response($.map(data, function (item) {
                            return {
                                label:item.name,
                                value:item.name
                            }
                        }));
                    }
                });
            },
            select:function (event, ui) {
                selected = true;
            },
            minLength:minSearchLength
        });

    $guildInput.on("focus", function () {
        setTimeout(function () {
            if ($guildInput.val().length >= minSearchLength && !selected)
                $guildAutpComplete.autocomplete("search", $guildInput.val());
        }, 100);
    });

   

});