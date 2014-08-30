$(function(){
    var $currentPlayerLink = $(".last-events-list li .player"),
        $playerLinks    = $(".last-events-list li .is-player-False, .last-events-list li .is-player-True"),
        $popupTmpl      = $("#player-popup-template"),
        $popupNotInGameTmpl = $("#player-popup-template-not-in-game");

    $currentPlayerLink.on("click",function(e){
        e.preventDefault();
        return false;
    });

    $playerLinks.on("click",function(event){
        event.preventDefault();
        event.stopPropagation();
        var $this   = $(this),
            link    = $this.text().replace("@",""),
            $popup = {},
            linkOb  = {
                "gameLink"          : "/"+link,
                "gameLinkText"      : "Profile on Tweenk",
                "twitterLink"       : "http://twitter.com/"+link,
                "twitterLinkText"   : "Twitter @"+link,
                "inviteText"        : "Invite @"+link,
                "name"              : link
            },
            $tmpl = {},
            $parent = $this.parents("li");

        if ($this.hasClass("is-player-False")){
            $tmpl = $popupNotInGameTmpl;
        }else{
            $tmpl = $popupTmpl
        }


        if ($parent.find(".event-list-popup").size()==0){
            $popup = $tmpl.tmpl(linkOb).insertAfter($this);
        }else{
            $popup = $parent.find(".event-list-popup");
        }
        $popup.css({
            "left": event.pageX-60,
            "top": event.pageY+15
        }).toggle();

        $(document).on("click.popup",function(event){
            var $target = $(event.target);
            if ($target.parents(".event-list-popup").size()==0){
                $popup.hide();
                $(document).off(".popup");
            }
        });
    });

    $(".last-events-list li").on("mouseenter",function(){
        var $this = $(this),
            $shareButton = $this.find(".achv-share-button,.event-achv-share-button");

        $shareButton.addClass('active');
    }).on("mouseleave",function(){
            var $this = $(this),
                $shareButton = $this.find(".achv-share-button,.event-achv-share-button");

            $shareButton.removeClass('active');
        });

    $(".event-achv-share-button").on("click",function(){
        var $this = $(this);
        $(".can-share-acvh[data-achvId='"+$this.data("aid")+"']").click();
    });

    $(document).on("click",".invite-profile",function(e){
        e.preventDefault();
        var $this = $(this),
            data = {
            "type_of_form": "send_mention_invite",
            "name"        : $this.data("name")
        };
        $this.removeClass("invite-profile").addClass("inviting").text("Inviting...").off("click").on("click",function(e){
            e.preventDefault();
            $(this).removeAttr("href");
            return false;
        });
        $.post($this.attr("href"),data,function(data){
            if (data.invited){
                $this.removeClass("inviting").addClass("invited").text("Invited");
            }else{
                $this.removeClass("inviting").addClass("invited").text("Something goes wrong");
            }

        });
    });

    $(".upcoming-event-toggler").click(function(e){
        e.preventDefault();
        var $this = $(this),
            $list = $(".upcoming-events-list");
        $this.toggleClass("active");
        if ($this.hasClass("active")){
            $list.css("display","inline-block");
        }else{
            $list.hide();
        }
    });
});
