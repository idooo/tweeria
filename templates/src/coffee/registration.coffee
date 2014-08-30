$ ->

  raceSelectors   = $(".choose_race .race")
  raceInput       = $("#race")
  classSelectors  = $(".choose_class .class_caption")
  classInput      = $("#class")
  sexSelectors    = $(".choose_sex .sex")
  sexInput        = $("#sex")

  raceInput.val(raceSelectors.filter(".selected").data("id") || false)
  classInput.val(classSelectors.filter(".selected").data("id") || false)
  sexInput.val(sexSelectors.filter(".selected").data("id") || false)

  selectorFunction = (event, inp, selector, current) ->
    event.preventDefault()
    event.stopPropagation()

    current = $(current)
    inp.val(current.data("id"))
    selector.removeClass("selected")
    current.addClass("selected")

  raceSelectors.on "click", (event) ->
    selectorFunction(event, raceInput, raceSelectors, this)

  classSelectors.on "click", (event) ->
    selectorFunction(event, classInput, classSelectors, this)

  sexSelectors.on "click", (event) ->
    selectorFunction(event, sexInput, sexSelectors, this)


