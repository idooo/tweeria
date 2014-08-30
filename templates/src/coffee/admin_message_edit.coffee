$ ->

  $('#delete_button').on 'click', (event) ->
    if (!confirm('Are you really want delete this message?'))
      return false

  $('.message-edit select').uniform()