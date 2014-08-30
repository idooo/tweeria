$(function(){
    $(".cc-item-table tr[title]").cluetip({splitTitle:"|"});

    $(".cc-item-table tr").on("click",function(e){
        e.preventDefault();
        var href = $(this).find("a:first").attr("href");
        if (typeof href!=='undefined'){
            document.location=href;
        }
    });
});