$(function(){
    var $li = $('<a href="#" class="inviting"><div></div></a>'),
        $span = $('<span class="invited">Invited</span>'),
        $wasInvSpan = $(".was-invited"),
        $preloader = $('<li class="preloader"><img src="/style/img/ajax-loader_2.gif" alt=""></li>'),
        $more = $(".more"),
        $friendList = $("#friend-list");
    $.getJSON(
        "/Elfrey?type_of_form=get_friends",
        function(data){
            $(".preloader").remove();
            var $tmpl = $("#friends-list-template").tmpl(data);
            $friendList.append($tmpl);
            $more.data("skip","25");
        }
    );

    $more.on("click",function(e){
        e.preventDefault();
        $("html, body").animate({ scrollTop: 0 }, 600);
        var skip = $(this).data("skip"),
            old = $friendList.html();
        $friendList.html($preloader)

        $.getJSON(
            "/Elfrey?type_of_form=get_friends&skip="+skip,
            function(data){
                $(".preloader").remove();
                if ($(data).size()==0){
                    $friendList.html(old);
                    $more.remove();
                }else{
                    var $tmpl = $("#friends-list-template").tmpl(data);
                    $friendList.html($tmpl);
                    $more.data("skip",parseInt(skip)+25);
                }

            }
        );
    });

    $(document).on("submit",".invite-form",function(e){
        e.preventDefault();
        var $this = $(this);
        $this.find("input:submit").remove();
        $this.append($li);
        $.post($this.attr("action"),
            $this.serialize(),
            function(data){
                if (data.invited){
                    $this.find(".inviting").remove();
                    $this.append($span);
                }
            }
        )
    });

    $(".invite-target-form").on("submit",function(e){
        e.preventDefault();
        var $this = $(this),
            $button = $this.find("input:submit"),
            name = $this.find("input:text").val();
        console.log(name,$this.find("input:text"));
        $button.addClass("inviting").attr("disabled","disabled").val("Sending");
        $.post($this.attr("action"),
            $this.serialize(),
            function(data){
                if (data.invited){
                    $button.removeClass("inviting").removeAttr("disabled").val("Send");
                    $wasInvSpan.text(name+' was invited');
                }else{
                    $button.removeClass("inviting").removeAttr("disabled").val("Send");
                    $wasInvSpan.text('Something goes wrong!');
                }
            }
        )
            .error(function(){
                $button.removeClass("inviting").removeAttr("disabled").val("Send");
                $wasInvSpan.text('Something goes wrong!');
            });
    });
});