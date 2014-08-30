$(function(){
    var imgFile = $("#guild-img").data("img") || false;
    $("#guild-img").uniform();

    /*if (imgFile){
        $("#uniform-guild-img .action").css({
            "background-image": "url("+imgFile+")",
            "background-size": "54px"
        });
    }*/

    $("#promote-select").uniform();


    //$(".guild-settings-table tbody tr").addClass("hover");


    $(".guild-settings-table tbody tr").on("mouseenter",function(event){
        $(this).addClass("hover");
    }).on("mouseleave",function(event){
            $(this).removeClass("hover");
        });

});