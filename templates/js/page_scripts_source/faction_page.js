$(function(){
    $(".like-button").on("click",function(e){
        e.preventDefault();
        var $this = $(this),
            text = $this.html(),
            $counter = $this.find(".like-counter"),
            count = parseInt($counter.text());
        if (strpos(text,"Liked") === 0){//Unliked
            text = text.replace("Liked","Like");
            count = count-1;
        }else{//Liked
            text = text.replace("Like","Liked");
            count = count+1;
        }
        $this.toggleClass("liked-button").html(text).find(".like-counter").text(count);

    });
});