$(function(){
    $(".item-popuped tbody tr td").on("click", function (event) {
        event.preventDefault();
        event.stopPropagation();

        var data = $(this).parent().data(),
            bonusparsed = {};

        data.bonus = (data.bonus == undefined) ? "" : data.bonus;

        if (data.bonus != "") {
            bonusparsed = JSON.parse(data.bonus.replace(/'/g, "\""));
        }

        data.bonusparsed = {};
        $.each(bonusparsed, function (index, value) {
            data.bonusparsed[index] = "+" + value['value'] + " " + value['name'];
        });

        $.fancybox($("#admin-item-popup").tmpl(data), {
            closeBtn:false,
            wrapCSS:"tweenk-popup",
            padding: 0,
            helpers:{
                overlay:{
                    css:{
                        "background":"transparent"
                    }
                }
            }
        });
        $.fancybox.update()
    });

    $(".spell-popuped tbody tr td").on("click",function(event){
        event.preventDefault();
        event.stopPropagation();

        var data = $(this).parent().data(),
            bonusparsed = {};



        $.fancybox($("#admin-spell-popup").tmpl(data), {
            closeBtn:false,
            wrapCSS:"tweenk-popup",
            padding: 0,
            helpers:{
                overlay:{
                    css:{
                        "background":"transparent"
                    }
                }
            }
        });
        $.fancybox.update()
    });



    $(".artwork-popuped a").on("click", function (event) {
        event.preventDefault();
        event.stopPropagation();

        var data = $(this).data();

        $.fancybox($("#admin-artwork-popup").tmpl(data), {
                autoSize:false,
                width:750,
                height:500,
                closeBtn:false,
                wrapCSS:"tweenk-popup",
                padding: 0,
                helpers:{
                    overlay:{
                        css:{
                            "background":"transparent"
                        }
                    }
                },
            afterShow : function(){
                $(".fancybox-wrap").css({
                    "height" : $(".fancybox-wrap").height()+40
                })
                $(".fancybox-inner").css({
                   "height": $(".fancybox-inner").height()+40
                });
            }
        });

    });

    $(".cluetip_popup_shop").cluetip({splitTitle:'|'});
});