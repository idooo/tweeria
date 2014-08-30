$(function(){
    $(".list-spells .spell-item").on("click",function(){
        var $this = $(this),
            $form = $this.parents("form"),
            $input = $form.find("input[name='type_of_form']"),
            params = $form.serialize();
        $.post("/spellbook",
            params,
            function(data){
                data = JSON.parse(data);

                if (data.changed){
                    ($input.val()=="move_spell_from_book") ? $input.val("move_spell_to_book") : $input.val("move_spell_from_book");
                    $this.toggleClass("active");
                }
            })
    });
    $(".spell-item").cluetip({
        titleAttribute : "data-title",
        splitTitle : "|"
    });
});