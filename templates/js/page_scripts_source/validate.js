$(function(){
//    $.validator.addMethod("name", function(value, element) {
//        return this.optional(element) || /^[A-Za-z\d]+$/i.test(value);
//    }, "Name can contain only latin letters and numbers");

    jQuery.validator.addMethod(
        'regexp',
        function(value, element, regexp) {
            var re = new RegExp(regexp);
            return this.optional(element) || re.test(value);
        },
        "Please check your input."
    );

    var $form = (typeof validateForm === "undefined") ? $form = $("form:first") : $form = $(validateForm),
        validateOptions = {
            errorLabelContainer: $(".error-message div"),
            errorClass : "error_field",
            messages : {
                "name"  : {
                    required: "Name must be longer",
                    minlength: "Name must be at least 5 characters",
                    maxlength: "Name must be less than 40 characters",
                    regexp: "Name can contain only latin letters and numbers"
                },
                "desc"  : {
                    required: "Description must be longer",
                    minlength: "Description must be at least 4 characters",
                    regexp: "Description can contain only latin letters and numbers"
                },
                "img"   : {
                    required: "Image must not be empty"
                },
                "item_type"  : {
                    required: "You must select item type",
                    minlength: "You must select item type"
                },
                "cost"  : {
                    required: "Cost must not be empty",
                    number: "Cost must be a number",
                    min: jQuery.format("Cost cant be lesser than {0}")
                },
                "ore_count" : {
                    required: "You should add at least one effect on your spell",
                    min: "You should add at least one effect on your spell",
                    max: "You cant add more effects than scroll you have(1)"
                },
                "img_author" : {
                    required: "Image author field must be longer",
                    minlength: "Image author field must be at least 5 characters",
                    maxlength: "Image author field must be less than 40 characters",
                    regexp: "Image author field can contain only latin letters and numbers"
                },
                "keyword" : {
                    required: "Word field must be longer",
                    minlength: "Word field must be at least 5 characters",
                    maxlength: "Word field must be less than 40 characters",
                    regexp: "Word field can contain only latin letters and numbers"
                },
                "img_source" : {
                    regexp: "Image source should be a valid url address"
                },
                "action1": {
                    required: "At least one spell effect must be selected"
                }
            },
            submitHandler: function(form) {
                form.submit();
            }
        };

    if (typeof validateAdditionalOptions=="undefined"){
        validateAdditionalOptions = {};
    }
    validateOptions = $.extend({},validateOptions,validateAdditionalOptions);

    $form.validate(validateOptions);

    $("#item-level").on("change",function(){
        var $this = $(this),
            item_level = $this.val(),
            minCost = parseInt(item_level * (10 + item_level / 10 ));

        $("#item-cost-gold").rules("add",{
            min: minCost
        });
    }).change();
});