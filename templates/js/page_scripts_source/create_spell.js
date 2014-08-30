$(function(){
    $("#spell-img").uniform({
        fileDefaultText : "",
        fileBtnText     : ""
    })
    $("#create-spell-form select, #create-spell-form input:text").uniform();






    /**
     * @description Спелбук
     * @type {*}
     */
    var sliders = {},
        $form = $("#create-spell-form"),
        $oreCount           = $(".ore-count"),
        $spellbook          = $("#spellbook"), //Книжка заклинаний
        $spellTemplate      = $("#used-spell-template"),
        $submitButton       = $("#create-spell-submit"),
        $totalSummCont      = $submitButton.find(".count"),
        $spellFilter        = $spellbook.find(".spellbook-spell-filter"), //фильтры
        $availableSpells    = $spellbook.find(".available-spell-list li"), //доступные спеллы
        $usedSpells         = $spellbook.find(".spellbook-spell-to-create li"), //используемые спеллы
        $paramsSpan         = $spellbook.find("span.spell-power-slider"),
        $spellLvl           = $("#spell-lvl"); //параметры


    function addSpell($this,$container,actionIndex,data,multiply){
        if ($container.size()==1){
            var title = $this.attr("title") || "";

            if (sliders["spell-"+data.spellId]!=undefined) return false;

            $container.removeClass("empty").html($spellTemplate.tmpl(data));
            $("#action"+actionIndex).val(data.spellId);
            $container.data("actionindex",actionIndex);
            var $img = $container.prev().find("img");

            if ($img){
                $img.attr({
                    "src": data.spellImg,
                    "data-title" : data.title
                })
                    .cluetip({
                        titleAttribute: "data-title",
                        splitTitle:'|'
                    })
                    .parent().removeClass("empty");
            }
            var maxValue = ($this.data("maxvalue")) ? parseInt($this.data("maxvalue"))*parseInt($spellLvl.val()) : 50;

            sliders['spell-'+data.spellId] = $container.find(".spell-power-slider").slider({
                min     : $this.data("min-value") || 1,
                max     : maxValue,
                value   : $this.data("min-value") || $this.data("spellvalue") || 1,
                animate : false,
                create  : sliderCreateHandler,
                change  : sliderSlideHandler,
                slide   : sliderSlideHandler,
                stop    : slideStopHandler
            }).data("multiply",multiply);

            $this.addClass("selected");

            var needScroll = parseInt($oreCount.text())+1;
            $("#ore-count").val(needScroll).trigger("change");
            $oreCount.text(needScroll);

        }
    }
    function removeSpell($this,img,$li){
        var spellId = $this.data("spellid");

        $(".input-action").filter(function(){
            return $(this).val()==spellId;
        }).val("").next().val("");

        var multiply = (sliders["spell-"+spellId].data("multiply") === undefined) ? 1 : sliders["spell-"+spellId].data("multiply")
        tmp = $totalSummCont.text() - sliders["spell-"+spellId].slider("option","value") * multiply;
        $totalSummCont.text(tmp);

        delete sliders["spell-"+spellId];
        $availableSpells.filter(function(){
            return $(this).data("spellid")==spellId;
        }).removeClass("selected");

        $this.parent().empty().addClass("empty").prev().find("img").attr("src",img).parent().addClass("empty");



        var needScroll = parseInt($oreCount.text())-1;
        $("#ore-count").val(needScroll).trigger("change");
        $oreCount.text(needScroll);
    }

    $availableSpells.on("click",function(event){//Add spell
        event.preventDefault();
        event.stopPropagation();
        var $this       = $(this),
            $container  = $usedSpells.find(".spell-info.empty:first").first(),
            actionIndex = 4-$usedSpells.find(".spell-info.empty").size(),
            data        = {},
            multiply        = ($this.data("multiply") === undefined) ? 1 : $this.data("multiply");

        data.spellName      =
            ($this.data("spellname") == undefined)
                ? $this.find(".spell-title").text()
                : $this.data("spellname");
        data.spellIcon      =
            ($this.data("spellicon") == undefined)
                ? $this.find(".icon.spell").attr("class").split(" ")[2]
                : $this.data("spellicon");
        data.spellType      =
            ($this.data("spelltype") == undefined)
                ? $this.find(".spell-type").text()
                : $this.data("spelltype");
        data.spellId        =
            ($this.data("spellid") == undefined)
                ? $.guid++
                : $this.data("spellid");
        data.spellCountText =
            ($this.data("spellcounttext") == undefined)
                ? "damage"
                : $this.data("spellcounttext");
        data.spellManaCost =
            ($this.data("spellmanacost") == undefined)
                ? ""
                : $this.data("spellmanacost");
        data.spellImg =
            ($this.data("spellimg") == undefined)
                ? $this.find(".spell-img img").attr("src")
                : $this.data("spellimg");
        data.spellValueText =
            ($this.data("spellvaluetext") == undefined)
                ? "damage"
                : $this.data("spellvaluetext");
        data.spellValue=
            ($this.data("spellvalue") == undefined)
                ? "1"
                : $this.data("spellvalue");
        data.title =
            ($this.data("title") == undefined)
                ? "1"
                : $this.data("title");

        if (typeof sliders['spell-'+data.spellId] === "undefined"){
            addSpell($this,$container,actionIndex,data,multiply);
        }else{
            var $closeButton = $(".remove-spell[data-spellid="+data.spellId+"]"),
                $li = $closeButton.parent();
            removeSpell($closeButton,"/style/img/clean-spell-slot.png",$li);
        }


    });

    /**
     * @description handler создания для слайдеров
     *
     * @param event
     * @param ui
     */
    function sliderCreateHandler(event,ui){
        var $this       = $(this),
            $activeSpan = $("<span />",{
                "class"   : "active-bg"
            }),
            tmp         = 0,
            id          = $this.attr("id").replace("spell-",""),
            $source     = $availableSpells.filter(function(){
                return $(this).data("spellid")==id;
            });

        $activeSpan.appendTo($this);

        $.each(sliders,function(index,item){
            var multiply = (sliders[index].data("multiply") === undefined) ? 1 : sliders[index].data("multiply")
            tmp += sliders[index].slider("option","value") * multiply;
        });

        tmp += parseInt($source.data("multiply"));

        $totalSummCont.text(tmp);
    }

    /**
     * @description хендлер для управления изменениями параметров
     * @param event
     * @param ui
     */
    function sliderSlideHandler(event,ui){

        var $this           = $(this), //текущий слайдер
            $spellInfo      = $this.parents(".spell-info"),//инфо
            aLeft           = $this.find("a").css("left"), //отступ каретки
            $activeSpan     = $this.find(".active-bg"), //спан, закрашивающий выбранную область
            tmp             = 0;

        $activeSpan.width(aLeft);

        $.each(sliders,function(index,item){
            var multiply = (sliders[index].data("multiply") === undefined) ? 1 : sliders[index].data("multiply")
            tmp += sliders[index].slider("option","value")*multiply;
        });

        $this.next().val(ui.value);
        $activeSpan.width(aLeft);
        $("#action"+$spellInfo.data("actionindex")+"_value").val(ui.value);

        $totalSummCont.text(tmp);
    }

    /**
     * @description хендлер про истановке слайдера
     * @param event
     * @param ui
     */
    function slideStopHandler(event,ui){
        var $this           = $(this) //текущий слайдер
            ,aLeft           = $this.find("a").css("left")  //отступ каретки
            ,$activeSpan     = $this.find(".active-bg") //спан, закрашивающий выбранную область
            ,tmp            = 0;


        $.each(sliders,function(index,item){
            var multiply = (sliders[index].data("multiply") === undefined) ? 1 : sliders[index].data("multiply")
            tmp += sliders[index].slider("option","value") * multiply;
        });

        $activeSpan.width(aLeft);
        $totalSummCont.text(tmp);
    }

    $paramsSpan.empty().each(function(){
        var $this = $(this),
            id = $this.attr("id");



        sliders[id] = $this.slider({
            min     : $this.data("min-value") || 1,
            max     : parseInt($this.data("maxvalue"))*parseInt($spellLvl.val()) || 50,
            animate : false,
            create  : sliderCreateHandler,
            change  : sliderSlideHandler,
            slide   : sliderSlideHandler,
            stop    : slideStopHandler
        });
    });

    $(document).on("click",".remove-spell",function(eventas){//remove spell
        event.preventDefault();
        event.stopPropagation();

        var $this   = $(this),
            img     = "/style/img/clean-spell-slot.png",
            $li     = $this.parents("li");

        removeSpell($this,img,$li);
    });
    /**
     * END слайдеры
     */

    $(".available-spell-list li").cluetip({
        titleAttribute: "data-title",
        splitTitle:'|'
    });

    $form.on("submit",function(e){
        var $form = $(this);
        $form.find("input.params:text[disabled]").each(function(){
            $(this).removeAttr("disabled");
        });
        return false
    });

    $spellLvl.on("change",function(){
        var $this = $(this),
            val = $this.val();

        $.each(sliders,function(index,item){
           console.log(index,item);
            var orId = index.replace("spell-",""),
                $avSpell = $availableSpells.filter(function(){
                    return $(this).data("spellid")==orId;
                }),
                resByLvl = $avSpell.data("maxvalue"),
                curVal = sliders[index].slider("option","value");

            sliders[index].slider("option","max",resByLvl*val).slider("option","value",curVal);
        });
    });

    var filterSpells = function(types){


        $availableSpells.hide();

        $usedSpells.find(".remove-spell").click();
        if (types.length>0){

            $.each(types,function(index,type){
                $availableSpells.filter(function(){
                    return $(this).data("type")==type;
                }).show();
            })
        }
    };

    $spellFilter.on("click","li",function(e){
        e.preventDefault();

        var $this = $(this),
            filterTypes = [];

        if ($this.hasClass("active")) return false;

        $this.addClass("active").siblings(".active").removeClass("active");

        filterTypes.push($this.data("type"));
        filterSpells(filterTypes);

    }).find("li:first").click();

    $("#delete-item-button").on("click",function(e){
        e.preventDefault();
        if (confirm("Friend, do you really want delete this spell?")){
            $(this).parents("form").submit();
        }
    })

});