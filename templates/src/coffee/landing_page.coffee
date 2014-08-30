$ ->
  checkbox = $('#join_guild')
  links = $('a.reg-link')

  guild_name = $('#guild_name').html()

  baselink = '/registration?' + $('#player_name').html()

  if checkbox
    checkbox.on 'change', (event) ->
      link = baselink
      if checkbox.is(':checked')
        link = link + '&guild='+ guild_name

      for _item in links
        $(_item).attr('href', link)

