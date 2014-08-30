$(function(){
    var $errorMessage = $('<div class="error-approve-message"></div>'),
        $approveBlock = $("#approve-block"),
        $nothingBlock = $(".nothing-to-approve");


    $approveBlock.find("select").uniform();

    $approveBlock.on("submit","form",function(e){
        e.preventDefault();

        var $form   = $(this),
            $parent = $form.parents(".approve-item-wrapper"),
            action  = $form.attr("action"),
            data    = $form.serialize()+"&ajax=1",
            type    = $form.find("input[name='type_of_form']").val();

        $.post(
            action,
            data,
            function(data){
                console.log(data);
                if (data.error==1){
                    $errorMessage.clone().append(data.message).prependTo($approveBlock).delay(2000).fadeOut();

                }else if (data.success==1){
                    $parent.animate({height: 'toggle'},"slow",function(){
                        $parent.remove();
                        if ($approveBlock.find(".approve-item").size()==0){
                            $approveBlock.hide();
                            $nothingBlock.show();
                        }
                    });
                }


            },
            "json"
        );
        console.log($form[0],$form.serialize(),type);
    });
});