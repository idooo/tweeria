$(function () {
    $("body").on("click", ".like-button", function (e) {
        e.preventDefault();
        var $this = $(this);


        if ($this.hasClass("liked-button")) return false;


        var likes = parseInt($this.data("likes")) + 1,
            $parent = $("#" + $this.data("parent")),
            $form = $this.parents("form[name='like-form']"),
            $likesCount = $parent.find(".likes-count"),
            $inlineForm = $parent.find("form[name='like-form']"),
            $inlineRatings = $inlineForm.parents(".rating"),
            $inlineButton = $inlineForm.find(".inline-like-button"),
            $inlineLiked = $('<span></span><span class="likes-count">' + likes + '</span> likes <i></i></span>'),
            $liked = $('<a href="#like" class="like-button liked-button">Liked<span class="like-counter">' + likes + '</span></a>');

        $.ajax({
            url:$form.attr("action"),
            type:"post",
            dataType:"json",
            data:$form.serialize() + "&ajax=1",
            success:function (data) {
                if (data.liked = 1) {

                    $parent.data("is_like", "True").data("likes", likes);

                    $likesCount.text(likes).parent().addClass("plus").addClass("liked");

                    $this.remove();
                    $liked.insertBefore($form);
                    $form.remove();
                    $inlineButton.remove();
                    $inlineRatings.addClass("plus").addClass("liked");
                    $inlineLiked.prependTo($inlineForm);
                }
            }
        });
    });

/*    $("#main").on("click", ".inline-like-button", function (e) {
        e.preventDefault();

        var $this = $(this);

        inlineLikeClick($this);
    });*/
});


function inlineLikeClick($this, type) {
    var $parent = $("#" + $this.data("parent")),
        $form = $this.parents("form[name='like-form']"),
        likes = parseInt($this.data("likes")) + 1,
        $liked = $('<span></span><span class="likes-count">' + likes + '</span> likes <i></i></span>'),
        $likesCount = $parent.find(".likes-count");

    if (type = 'new') {
        $liked = $('<span class="main-like-button liked">Liked</span>');
        $likesCount = $parent.find(".main-likes-count");
    }

    var $rating = $likesCount.parents(".rating");

    //console.log($this[0],$parent[0],$form[0],$likesCount[0], $rating[0]);
    //return false;
    $.ajax({
        url:$form.attr("action"),
        type:"post",
        dataType:"json",
        data:$form.serialize() + "&ajax=1",
        success:function (data) {
            if (data.liked = 1) {

                $parent.data("is_like", "True").data("likes", likes);

                $likesCount.text(likes);
                $rating.addClass("plus").addClass("liked");

                $this.remove();
                $liked.prependTo($form);
            }
        }
    });
}