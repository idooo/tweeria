$(function(){
    var $selects = $(".hero-settings-page select");

    $('#titles').change(function() {
        if (this.value != 0) {
            $('#title_UID').val(this.value);
            $('#titles_change_form').submit();
        }
    })

    $('#artworks').change(function() {
        $('#artwork_UID').val(this.value);
        $('#artworks_change_form').submit();
    })

    $('#reset-button').click(function() {
            if (!confirm('Are you sure that you want change race/class?')) {
                return false;
            }
        }
    )

    $selects.uniform();
});