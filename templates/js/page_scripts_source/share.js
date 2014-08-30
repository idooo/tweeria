$(function(){
    var $achvToShare = $(".can-share-acvh"),
        $shareBlockTmpl = $("#share-block"),
        popupOptions = "menubar=no,location=no,resizable=yes,scrollbars=yes,status=no";;

    $achvToShare.on("click",function(event){
        event.preventDefault();
        event.stopPropagation();
        var $img = $(this),
            data = $img.data(),
            tmpl = $shareBlockTmpl.tmpl(data);

        $.fancybox(tmpl[0],{
            autoSize:false,
            closeBtn:false,
            wrapCSS:"tweenk-popup achv-share",
            padding: 0,
            width: 425,
            height: 250,
            helpers:{
                overlay:{
                    css:{
                        "background":"transparent"
                    }
                }
            }
        })

    });


    $(document).on("click",".achv-share-button",function(event){
        event.preventDefault();
        event.stopPropagation();

        var $this = $(this),
            url = $this.attr("href");

        if ($this.hasClass("gp")){
            var data = $this.data();

            $("#gp-widget-title").prop("content",data.title);
            $("#gp-widget-desc").prop("content",data.desc);
            $("#gp-widget-img").prop("content",data.image);

            $("#og-title").prop("content",data.title);
            $("#og-desc").prop("content",data.desc);
            $("#og-url").prop("content",data.url);
            $("#og-img").prop("content",data.image);
        }

        var popup = window.open(url,'Share',"width=565,height=480,"+popupOptions);
        popup.focus();
    });
});