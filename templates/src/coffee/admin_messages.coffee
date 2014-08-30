$ ->

  loading_container = $('#loading_message')
  content_part = $('#content_part')
  selector = $('#action_selector')
  form = $('#action_select_form')

  selector.uniform()
  selector.on 'change', (event) ->

    request = $.ajax({
      url: '/a/get_ajax_messages',
      type: 'post',
      data: form.serialize()
    })

    loading_container.show()

    request.done (response) ->
      loading_container.hide()
      content_part.html(response)

