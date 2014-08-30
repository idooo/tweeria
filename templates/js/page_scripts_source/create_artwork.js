$(function(){

    $(".craft-artwork-page select, .craft-artwork-page textarea, .craft-artwork-page input:text").uniform();
    $(".edit-artwork-page select, .edit-artwork-page textarea, .edit-artwork-page input:text").uniform();

    $("#delete-item-button").on("click",function(e){
        e.preventDefault();
        if (confirm("Friend, do you really want delete this artwork?")){
            $(this).parents("form").submit();
        }
    })

});