$(function () {
    var $rightColumn = $(".sub-column-left-inner"),
        $leftColumn = $(".column-left-inner"),
        leftHeight = $leftColumn.height();

    $(".new-items-list li").cluetip({splitTitle:'|'});

    $(".new-items-list li .item-author").on("click", function (e) {
        e.preventDefault();
        document.location = $(this).attr("href");
    });
    $(".new-items-list li .img-cont img, .new-items-list li .item-name").on("click", function (event) {
        event.preventDefault();
        event.stopPropagation();

        if (!$(event.target).hasClass("inline-like-button") && !$(event.target).hasClass("author")) {

            var data = $(this).parents("li").data(),
                bonusparsed = {};

            data.bonus = (data.bonus == undefined) ? "" : data.bonus;

            if (data.bonus != "") {
                bonusparsed = JSON.parse(data.bonus.replace(/'/g, "\""));
            }

            data.bonusparsed = {};
            $.each(bonusparsed, function (index, value) {
                data.bonusparsed[index] = "+" + value['value'] + " " + value['name'];
            });

            $.fancybox($("#shop-item-popup").tmpl(data), {
                closeBtn:false,
                wrapCSS:"tweenk-popup",
                padding:0,
                helpers:{
                    overlay:{
                        css:{
                            "background":"transparent"
                        }
                    }
                }
            });
        }else if($(event.target).hasClass("inline-like-button")) {
            inlineLikeClick($(this));
        }
    });

    $(".main-artwork .main-like-button").on("click",function(e){
        e.preventDefault();
        inlineLikeClick($(this), 'new');
    });

    $(".new-items-list .main-like-button").on("click", function (e) {
        e.preventDefault();
        var $this = $(this);

        inlineLikeClick($this, 'new');
    });

    $(".main-map-info").on("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        document.location = $(this).data("href");
    });
});
