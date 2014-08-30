$(function () {

    $(".item-rating span.plus, .item-rating span.minus").on("click", function (e) {
        e.preventDefault();
        $(this).toggleClass("active");
    });
});