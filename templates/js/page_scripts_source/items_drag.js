$(function(){

    var $inventory      = $(".player-inventory li"),
        $playerSlots    = $(".player-items li"),
        $equipForm      = $("#equip-form"),
        $artWorkBlock   = $(".player-art"),
        $sellBlock      = $(".sell-item-form"),
        $sellFormText   = $artWorkBlock.find(".sell-form-text"),
        $sellFormGolds  = $artWorkBlock.find(".gold-gained-block"),
        $sellForm       = $("#sell-item-form"),
        $sellItemCreated= $("#sell-item-created"),
        $sellItemId     = $("#sell-item-uid"),
        $uidInput       = $equipForm.find("#uid"),
        $blankItem      = $("<img src=\"/style/img/fancybox/blank.gif\" alt=\"No item\" data-form-id=\"0\">"),
        playerAbPreId   = "player-ab-",
        colorClasses    = ["itm1","itm2","itm3","itm0"],
        sellFlag        = false;


    /**
     * @desc проносим объект над областью
     * @param event
     * @param ui
     */
    var draggableOver = function(event,ui){
        var $this = $(this),
            $item = $(ui.draggable),
            formId = $item.attr("data-form-id"),
            $form = $("#equip-form-"+formId);


        if ($item.attr("data-slot") == $this.attr("data-slot")){
            $this.addClass("can-drop");
        }else{
            $this.addClass("cant-drop")
        }
    };
    /**
     * @desc выносим объект за область
     * @param event
     * @param ui
     */
    var draggableOut =  function(event,ui){
        //$(this).removeClass("can-drop cant-drop");
        var $this       = $(this),
            $item       = $(ui.draggable),
            $destImg    = $this.find("img"),
            $sourceImg  = $item.find("img");
    };

    /**
     * @desc бросаем объект на слот(чтобы одеть или снять)
     * @param event
     * @param ui
     * @return {Boolean}
     */
    var draggableDrop = function(event, ui){
        var $this       = $(this),
            $item       = $(ui.draggable),
            $destImg    = $this.find("img"),
            $sourceImg  = $item.find("img"),
            itemId      = $sourceImg.attr("data-form-id"),
            oldItemId   = $destImg.attr("data-form-id") || false,
            addType     = false;

        var $parent = $(".player-inventory li[data-uid=\""+$sourceImg.data("uid")+"\"]");

        if ($this.parent().hasClass("player-inventory") && $item.parent().hasClass("player-inventory")) return false;

        $uidInput.val(0)

        if ($item.attr("data-slot")=="6"){
            addType = "66";
        }else if($item.attr("data-slot")=="66"){
            addType = "6";
        }

        if (
            (($item.attr("data-slot") == $this.attr("data-slot") || addType == $this.attr("data-slot")) || $this.attr("data-slot")==undefined)
                && $equipForm.size()==1
            ){

            $uidInput.val(itemId);

            var formParams  = $equipForm.serialize();
            formParams+= "&slot="+$this.attr("data-slot");
            if (oldItemId){
                formParams += "&old_id="+oldItemId;
            }

            $.ajax({
                dataType: "json",
                data: formParams,
                type: "POST",
                success: function(data){
                    //data = $.parseJSON(data);

                    if (data.equipted){

                        $.each(data.stats,function(key,value){

                            if (key == "HP" || key == "MP"){
                                $("#"+playerAbPreId+key+"-cur").text(value.current);
                                $("#"+playerAbPreId+key+"-max").text(value.max_dirty);
                                var percent = value.current/(value.max_dirty/100)

                                if (percent>100) percent = 100;

                                $("#"+playerAbPreId+key+"-percent").css({
                                    "width" : percent+"%"
                                });
                            }else if (key == "DMG"){
                                if (value.current<1){
                                    value.current = 1
                                }
                                $("#"+playerAbPreId+key).text((value.current - 1)+" — "+(value.current+1));
                            }else {
                                $("#"+playerAbPreId+key).text(value.current);
                            }
                        });


                        swapItems($destImg,$sourceImg,$destImg.parent(),$sourceImg.parent());

                        if ($item.parents(".player-slot-list.player-inventory").size()==1 && $item.find("img").attr("data-form-id")==0){//TODO выяснить что это...
                            $item.removeAttr("data-slot").removeClass("cant-drop, can-drop").removeAttr("data-slot");
                        }
                        $uidInput.val(0)
                    }
                }
            });
        }
        //$(this).removeClass("cant-drop can-drop");
    };

    $inventory
        .draggable({//@description драг из инвентаря
            cursor: "pointer",
            snapMode: "inner"
            ,snapTolerance: "5"

            ,helper: "clone"
            ,containment: "#tab-items"

            ,start: function(event,ui){
                showSellBlock();
            }
            ,drag: function(event,ui){

                var $this = $(this),
                    addType = 0;
                if ($this.find("img").attr("data-form-id")==0){
                    event.preventDefault();
                }
                $(".player-items .ui-droppable[data-slot='"+$this.attr("data-slot")+"']").addClass("can-drop");
                if ($this.attr("data-slot")=="6"){
                    addType = "66";
                    $(".player-items .ui-droppable[data-slot='"+addType+"']").addClass("can-drop");
                }else if ($this.attr("data-slot")=="66"){
                    addType = "6";
                    $(".player-items .ui-droppable[data-slot='"+addType+"']").addClass("can-drop");
                }
            }
            ,stop: function (event,ui){
                $(".player-items .ui-droppable").removeClass("can-drop");

                if (!sellFlag){
                    hideSellBlock();
                }
            }
        })
        .droppable({
            over: draggableOver,
            out: draggableOut,
            drop: draggableDrop
        })
    ;


    $playerSlots
        .draggable({
            cursor: "pointer",
            helper: "clone"
            ,containment: "#tab-items"
            ,start: function(event,ui){
                showSellBlock();
            }
            ,drag: function(event,ui){
                var $this = $(this);
                if ($this.find("img").attr("data-form-id")==0){
                    event.preventDefault();
                }
                $(".player-items .ui-droppable[data-slot='"+$this.attr("data-slot")+"']").addClass("can-drop");
                if ($this.attr("data-slot")=="6"){
                    var addType = "66";
                    $(".player-items .ui-droppable[data-slot='"+addType+"']").addClass("can-drop");
                }else if ($this.attr("data-slot")=="66   "){
                    addType = "6";
                    $(".player-items .ui-droppable[data-slot='"+addType+"']").addClass("can-drop");
                }
            }
            ,stop: function (event,ui){
                $(".player-items .ui-droppable").removeClass("can-drop");
                if (!sellFlag){
                    hideSellBlock();
                }
            }
        })
        .droppable({//@description можно уронить на слот плеера
            over: draggableOver,
            out: draggableOut,
            drop: draggableDrop
        });

    function swapItemColorClass($destItem,$endItem){
        var $destParent = $destItem.parent(),
            $endParent = $endItem.parent(),
            destClass = $destParent.hasClasses(colorClasses),
            endClass = $endParent.hasClasses(colorClasses);

        console.log(destClass,endClass);

        if ( destClass && endClass){
            $destParent.removeClass(destClass).addClass(endClass);
            $endParent.removeClass(endClass).addClass(destClass);
        }

    }

    function swapItems($destItem, $endItem, $dParent, $eParent) {
        var destType = $destItem.parent().attr("data-slot") || "",
            sourceType = $endItem.parent().attr("data-slot") || "";

        swapItemColorClass($destItem,$endItem);

        $destItem.parent().attr("data-slot", sourceType);
        $destItem.swapWith($endItem);
        $endItem.parent().attr("data-slot", destType);

        initToolTips();
    }

    /**
     * @description Дром на артворк для продажи
     */
    var sellDropOver = function(event,ui){
        $(this).addClass("can-drop");
        showSellBlock();
    };
    var sellDropOut = function (event,ui){
        /*if (dragDef.state()=="resolved"){
         setTimeout(function(){
         hideSellBlock();
         },100)
         }*/

    };
    var sellDropDrop = function (event,ui){

        sellFlag = true;
        $artWorkBlock.addClass("can-drop");

        var $this       = $(this),
            $item       = $(ui.draggable),
            $sourceImg  = $item.find("img"),
            itemId      = $sourceImg.attr("data-form-id"),
            created     = $sourceImg.attr("data-created"),
            currentGold = parseInt($("#player-gold").text());


        created = (created == "True") ? 1 : 0;

        $sellItemCreated.val(created);
        $sellItemId.val(itemId);


        if (itemId==0){

            $sourceImg.remove();
            $item.append($blankItem)
            $sellFormText.hide();
            $sellFormGolds.show().delay(3000).fadeOut(function(){
                $this.removeClass("can-drop");
                $sellFormText.show();
                hideSellBlock();
                sellFlag = false;
            });
        }else{
            //$inventory.draggable("disable");
            //$playerSlots.draggable("disable");
            $.ajax({
                dataType: "text",
                data: $sellForm.serialize(),
                type: "POST",
                success: function(data){
                    data = JSON.parse(data);

                    if (data.sold) {
                        $sourceImg.remove();
                        $item.append($blankItem);
                        $item.removeClass($item.hasClasses(colorClasses)).addClass("itm0");

                        hideSellBlock(1);
                        $.each(data.stats,function(key,value){
                            if (key == "HP" || key == "MP"){
                                $("#"+playerAbPreId+key+"-cur").text(value.current);
                                $("#"+playerAbPreId+key+"-max").text(value.max_dirty);
                                var percent = value.current/(value.max_dirty/100)

                                if (percent>100) percent = 100;

                                $("#"+playerAbPreId+key+"-percent").css({
                                    "width" : percent+"%"
                                });
                            }else if (key == "DMG"){
                                if (value.current<1){
                                    value.current = 1
                                }
                                $("#"+playerAbPreId+key).text((value.current - 1)+" — "+(value.current+1));
                            }else {
                                $("#"+playerAbPreId+key).text(value.current);
                            }

                            $("#player-gold").text(currentGold+data.goldgained);
                            $(".gold-gained-block .count").text(data.goldgained);
                        });

                    }else{
                        hideSellBlock();
                    }
                    sellFlag = false;

                }
            });
        }

    };

    $sellBlock.droppable({
        over: sellDropOver,
        out: sellDropOut,
        drop: sellDropDrop
    });

    function showSellBlock(){

        $sellFormGolds.stop().removeAttr("style").hide();
        $sellFormText.stop().removeAttr("style").show();
        $sellBlock.stop().removeAttr("style").addClass("drag-over").show();
    }


    function hideSellBlock(goldValue){


        if (typeof goldValue === "undefined"){

            $sellBlock.fadeOut(function(){
                $artWorkBlock.removeClass("can-drop");
                $sellBlock.removeAttr("style").removeClass("drag-over").hide();
                $sellFormText.show();
                $sellFormGolds.hide();

                $inventory.draggable("enable");
                $playerSlots.draggable("enable");
            });
        }else{

            $sellFormGolds.hide();
            $sellFormText.fadeOut("slow",function(){
                $sellFormGolds.fadeIn("slow").delay(1000).fadeOut(function(){
                    $sellBlock.fadeOut(function(){
                        $artWorkBlock.removeClass("can-drop");
                        $sellFormText.show();
                        $sellBlock.removeAttr("style");

                        $inventory.draggable("enable");
                        $playerSlots.draggable("enable");
                    });

                });
            });
        }


    }

});