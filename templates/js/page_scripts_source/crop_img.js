
$(function(){
    /*
     CROP картинки для предмета
     */

    /**
     * @description Координаты для кропа картинки
     * @param c - объект с координатами
     */
    function showCoords(c){
        $('#x1').val(c.x);
        $('#y1').val(c.y);
        $('#x2').val(c.x2);
        $('#y2').val(c.y2);
        $('#w').val(c.w);
        $('#h').val(c.h);
    }

    /**
     * @description очистка координат
     */
    function clearCoords(){
        $('#coords input').val('');
    }

    /**
     * @description параметры для кропа с ajax
     * @type {*}
     */



    var $form           = $("#upload-image-form"),
        $thumb          = $("#thumb"),
        //imgInputId      = pageImgInputId || "item-image",
        imgInputId      = $("#upload-image-form input:file").attr("id"),
        $imgInput       = $("#"+imgInputId),
        $imgHiddenInput = $("#img-link"),
        $cropButton     = $("#crop-image"),
        $cropCont       = $("#crop-cont"),
        imgSize         = ($imgInput.data("imgsize") == undefined) ? "54px" : $imgInput.data("imgsize"),
        optAspect       = ($imgInput.data('aspect') == undefined) ? 1 : $imgInput.data('aspect'),
        ajaxLoader      = {
            src		: "/style/img/ajax-loader.gif",
            width	: 24,
            height	: 24
        },
        ajaxFormOptions = {
            //target			: "#output1",   // target element(s) to be updated with server response
            beforeSubmit	: showRequest,  // pre-submit callback
            success			: showResponse,  // post-submit callback
            error           : showResponse,

            url				: "/u/ajax/?action=prepareImageToCrop",         // override for form's 'action' attribute
            type			: "POST",        // 'get' or 'post', override for form's 'method' attribute
            dataType		: "json" // 'xml', 'script', or 'json' (expected server response type)
            //clearForm: true        // clear all form fields after successful submit
            //resetForm: true        // reset the form after successful submit

            // $.ajax options can be used here too, for example:
            //timeout:   3000
        },
        jcrop_api       = false;

    /**
     * инициализация плагина для файлового инпута
     */
    $imgInput.uniform({
        fileDefaultText : "",
        fileBtnText     : "",
        fileBackground : (typeof $imgInput.data("src")==="undefined") ? "" : "url("+$imgInput.data("src")+") no-repeat 0 0",
        fileSizeW: (typeof $imgInput.data("fsizew")==="undefined") ? "" : $imgInput.data("fsizew"),
        fileSizeH: (typeof $imgInput.data("fsizeh")==="undefined") ? "" : $imgInput.data("fsizeh")
    });
    var $uniformImage = $("#uniform-"+imgInputId+" .action");


    /**
     * @description pre-submit callback
     * @param formData
     * @param jqForm
     * @param options
     * @return {Boolean}
     */
    function showRequest(formData, jqForm, options) {
        var queryString = $.param(formData);


        $.fancybox($cropCont,{
            onUpdate: function(){
                $(".fancybox-inner").width(function(){
                    return $(this).width()+5
                })
            }
        });
        if ($(".imgload-error").size()>0){
            $(".imgload-error").hide();
        }
        $cropButton.show();

        if (jcrop_api){
            jcrop_api.destroy();
            jcrop_api = false;
        }
        $thumb.attr({
            src		: ajaxLoader.src,
            width	: ajaxLoader.width,
            height	: ajaxLoader.height
        })
            .css({
                "width"	    : ajaxLoader.width,
                "height"	: ajaxLoader.height,
                "display"   :"block",
                "margin"    : "0 auto 20px"
            });


        return true;
    }

    /**
     * @description post-submit callback
     * @param responseText
     * @param statusText
     * @param xhr
     * @param $form
     */
    function showResponse(responseText, statusText, xhr, $form)  {
        if (responseText.responseText != undefined ) {
            responseText = responseText.responseText.replace(/'/g,'"');
            responseText = JSON.parse(responseText);
        }
        if (responseText.error=="img.big_size"){
            if ($(".imgload-error").size()==0){
                var $text = $("<span />").addClass("imgload-error")
                    .css({
                        "display" : "block",
                        "width" : 270,
                        "height" :50,
                        "margin" : "0 auto 20px"
                    })
                    .text("Image is too big").insertAfter($thumb);
            }else{
                $(".imgload-error").show();
            }

            $cropButton.hide();
            $thumb.hide();
            setTimeout(function(){$.fancybox.update();},200);
            return false;
        }

        if (jcrop_api){
            jcrop_api.destroy();
            jcrop_api = false;
        }

        $thumb.attr({
            src		: responseText.src,
            width	: responseText.width,
            height	: responseText.height
        })
            .css({
                width	: responseText.width,
                height	: responseText.height
            })
            .Jcrop({
                aspectRatio: optAspect,
                onChange:   showCoords,
                onSelect:   showCoords,
                onRelease:  clearCoords
            },function(){
                jcrop_api = this;
                jcrop_api.animateTo([10,10,responseText.width-10,responseText.height-10]);
                setTimeout(function(){$.fancybox.update();},200);
            });
        $imgHiddenInput.val(responseText.src).trigger("change");



    }

    /**
     * @description ajax загрузка картинки для кропа
     */
    $imgInput.change(function(event){
        event.preventDefault();
        $form.ajaxForm(ajaxFormOptions).submit();

        return false;
    });

    /**
     * @description вырезаем картинку
     */

    $cropButton.on("click",function(event){
        event.preventDefault();
        var $this = $(this);


        $("#img_to_crop").val($thumb.attr("src"));

        $.ajax({
            url		: $this.attr("href"),
            type	: "POST",
            data	: $form.serialize(),
            success	: function(data){
                //$("#dest-img").attr("src",data).show();
                $imgHiddenInput.val(data);

                $uniformImage.css({
                    "background-image" : "url("+data+")",
                    "background-size" : imgSize
                });
                $.fancybox.close();

            }
        })
    });
    /*
     END CROP картинки для предмета
     */

});