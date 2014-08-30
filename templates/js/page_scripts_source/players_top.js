$(function(){
	$(".ratings-table tbody tr td").on("click",function(event){
        var $this = $(this);
        if (!$this.hasClass("player-guild")){
            event.stopPropagation();
            event.preventDefault();

            var $a = $this.parent().find("a:first");
            document.location = $a.attr("href");
        }

    });
});