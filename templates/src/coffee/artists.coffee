$ ->
  selects = $('#ugc_requests .reasons_selector')

  for item in selects
    $(item).change ->
      if $(this).val() == '...'
        display = 'block'
      else
        display = 'none'

      $(this).next().css('display': display)