$(function(){
    /**
     * create_item
     */
    $("#create-item-form select, #create-item-form input:text, #item-type").uniform();



    /**
     * Cлайдеры
     * @type {*}
     */

    /**
     * Параметры
     */
    var $inputs         = $(".left-params input.params,.right-params input.params"), //инпуты с параметрами
        $runeInput      = $("#item-rune"), //инпут рун
        $cost           = $("input[name=cost]"), //результирующий инпут
        $params         = $("#params"),
        $typeSelect     = $('#item-type'),
        $iLvlSelect     = $("#item-level"),
        $paramsSpan     = $params.find(".left-params span.param-span, .right-params span.param-span"), //параметры
        $runeSlider     = $(".rune-slider"),
        $summarySpan    = $(".current-stat-summ"),
        $enchOreCount   = $("#ench-ore-count"),
        maxSumm         = $params.data("max-value"),
        maxSummValue    = 0,
        tmpSumm         = 0, //Временная сумма для слайдеров
        sliders         = {}; //Слайдеры

    function setCurSum(value){
        $summarySpan.text(value);
    }

    $iLvlSelect.on("change",function(event){
        var selectedOption = $iLvlSelect.find("option:selected")
        if (selectedOption.size()==1){
            updateMaxSumm();
        }
        if (tmpSumm != 0) {
            recalculateMinimum($typeSelect);
        }
        updateSlidersValue();

    });
    $iLvlSelect.change();

    function changeSlidesByMax(tmpSumm,maxSumm,ui,maxValue,$input,$maxInput,$thisSlider,value){

        $inputs.each(function(){
            var $this = $(this),
                value = parseInt($this.val()) || 0;
            tmpSumm += value;
            if (value>=maxValue && $(ui.handle.parentNode).attr("id")!=$this.attr("name")){
                maxValue = value;
                $maxInput = $this;
            }
        });
        $cost.val(tmpSumm);
        $input.val(ui.value);


        if (tmpSumm>maxSumm && $maxInput.val()>0){
            var value = $maxInput.val()-(tmpSumm-maxSumm),
                tmp = $("#params span#"+$maxInput.attr("name")).slider();
            $maxInput.val(value);
            tmp.slider("option","animate",true);
            tmp.slider("option", "value", value);
            tmp.slider("option","animate",false);
        }

        if (value>maxSumm){
            $thisSlider.slider("value",maxSumm);
            tmpSumm = maxSumm;
        }

        return tmpSumm;
    }

    function updateSlidersValue(currentSlider){//this is a new function
        var tmpSumm         = 0,
            maxInputValue   = 0,
            maxInputId      = "";

        currentSlider = (currentSlider==undefined) ? "" : currentSlider;

        if (parseInt($summarySpan.text())>maxSummValue){
            setCurSum(maxSummValue);
        }

        $inputs.each(function(index){
            var $this = $(this),
                name = $this.attr("name"),
                value = ($this.val()=="") ? 0 : parseInt($this.val());
            tmpSumm += value;


            if (value>maxInputValue && value>0 && name!=currentSlider){
                maxInputValue = value;
                maxInputId = name;
            }
        });

        if (tmpSumm>maxSummValue && maxInputId!=""){
            var newValue = maxInputValue-(tmpSumm-maxSumm);
            tmpSumm-=newValue;
            sliders[maxInputId].slider("value",newValue);
        }else if (tmpSumm>maxSummValue && maxInputId=="" && currentSlider!=""){

            sliders[currentSlider].slider("value",maxSummValue);
            tmpSumm = maxSummValue;
        }


        tmpSumm = 0;
        $.each(sliders,function(index){
            tmpSumm += sliders[index].slider("option","value");
        });
        setCurSum(tmpSumm);
    }

    function updateMaxSumm(value){
        var modifier = $runeInput.data("maxsumm-modifier");
        maxSumm = (value == undefined) ? $iLvlSelect.find("option:selected").data("max-stats") : value;
        if ($runeInput.val()>0){
            maxSumm = maxSumm+(modifier*$runeInput.val());
        }
        $(".max-stat-summ").text("/"+maxSumm);
        var keys = Object.keys(sliders);
        if (sliders[keys[0]] != undefined) {

            var sliderValue = sliders[keys[0]].slider("option","value"),
                slider = {
                    "handle" : sliders[keys[0]].slider().data().slider.handle[0],
                    "value"  : sliderValue
                };

            sliderSlideHandler("",slider);
        }
        maxSummValue = maxSumm;

    }

    /**
     * @description handler создания для слайдеров
     *
     * @param event
     * @param ui
     */
    function sliderCreateHandler(event,ui){
        var $this       = $(this),
            thisValue   = $this.data("default-value") || $this.data("min-value") || 0,
            $activeSpan = $("<span />",{
                "class"   : "active-bg"
            });

        $activeSpan.appendTo($this);

        $this.next().val(thisValue);
    }
    function runeSliderCreateHandler(event,ui){
        var $this       = $(this),
            $activeSpan = $("<span />",{
                "class"   : "active-bg"
            });

        $activeSpan.appendTo($this);
        $runeInput.val(0);
    }

    /**
     * @description хендлер для управления изменениями параметров
     * @param event
     * @param ui
     */
    function sliderSlideHandler(event,ui){
        var $thisSlider     = $(this), //текущий слайдер
            aLeft           = $thisSlider.find("a").css("left"), //отступ каретки
            $activeSpan     = $thisSlider.find(".active-bg"), //спан, закрашивающий выбранную область
            maxSliderValue  = $thisSlider.slider("option","max"), //Максимальное значение статов
            value           = ui.value, //Текущее значение слайдера
            thisId          = $thisSlider.attr("id"), //id слайдера
            $input          = $inputs.filter("[name="+thisId+"]"), //связанный инпут(имя_инпута=id_слайдера)
            maxValue        = 0, //максимальное значение среди слайдеров
            $maxInput       = $inputs.filter(":first"); //инпут с максимальным значением;

        $activeSpan.width(aLeft);
        tmpSumm = 0;

        $input.val(value);
        tmpSumm = updateSlidersValue(thisId);
    }
    function runeSliderSlideHandler (event,ui){
        var $this = $(this),
            aLeft           = $this.find("a").css("left"), //отступ каретки
            $activeSpan     = $this.find(".active-bg"), //спан, закрашивающий выбранную область
            maxSliderValue  = $this.slider("option","max"), //Максимальное значение статов
            value           = ui.value, //Текущее значение слайдера
            thisId          = $this.attr("id"), //id слайдера
            $input          = $inputs.filter("[name="+thisId+"]"), //связанный инпут(имя_инпута=id_слайдера)
            maxValue        = 0, //максимальное значение среди слайдеров
            $maxInput       = $inputs.filter(":first"); //инпут с максимальным значением;

        $activeSpan.width(aLeft);
        $runeInput.val(value);
        updateMaxSumm();
        updateSlidersValue();
    }

    /**
     * @description хендлер про истановке слайдера
     * @param event
     * @param ui
     */
    function slideStopHandler(event,ui){
        var $this           = $(this), //текущий слайдер
            aLeft           = $this.find("a").css("left"),  //отступ каретки
            $activeSpan     = $this.find(".active-bg"), //спан, закрашивающий выбранную область
            tmpSumm         = 0;

        $.each(sliders,function(index){
            tmpSumm += this.slider("value") || 0;
        });

        $activeSpan.width(aLeft);
        setCurSum(tmpSumm);
    }
    function runeSlideStopHandler(event,ui){
        var $this           = $(this), //текущий слайдер
            aLeft           = $this.find("a").css("left"),  //отступ каретки
            $activeSpan     = $this.find(".active-bg"); //спан, закрашивающий выбранную область

        $activeSpan.width(aLeft);
        $enchOreCount.text(ui.value);
        updateMaxSumm();
    }


    /**
     * @description Инициализируем слайдеры
     */
    tmpSumm = 0;
    $paramsSpan.empty().each(function(){
        var $this = $(this),
            id = $this.attr("id"),
            thisValue = $this.data("default-value") || $this.data("min-value") || 0;

        sliders[id] = $this.slider({
            min     : $this.data("min-value") || 0,
            max     : $this.data("max-value"),
            value   : thisValue,
            animate : false,
            create  : sliderCreateHandler,
            change  : sliderSlideHandler,
            stop    : slideStopHandler
        });
        tmpSumm += thisValue;
    });
    setCurSum(tmpSumm);

    $runeSlider.each(function(){
        var $this = $(this);
        $this.slider({
            min     : $this.data("min-value") || 0,
            max     : $this.data("max-value") || 3,
            animate : false,
            create  : runeSliderCreateHandler,
            change  : runeSliderSlideHandler,
            stop    : runeSlideStopHandler
        });
    });

    $inputs.on("change",function(event){
        var $this = $(this),
            id = $this.attr('name'),
            value = $this.val();

        sliders[id].slider("option","value",value);
    });

    /**
     * END слайдеры
     */

    $("#create-item-form").on("submit",function(e){
        var $form = $(this);
        $form.find("input.params.text[disabled]").each(function(){
            $(this).removeAttr("disabled");
        });
    });

    $("#delete-item-button").on("click",function(e){
        e.preventDefault();
        if (confirm("Friend, do you really want delete this item?")){
            $(this).parents("form").submit();
        }
    })

    /**
     * Динамическая смена ограничений по типу
     */

    function recalculateMinimum(obj) {
        var selected = obj.find('option:selected');
        var data = selected.data('things')

        var attrs = ['DMG', 'DEF', 'int', 'str', 'dex', 'luck', 'HP', 'MP']
        for (var stat in attrs) {
            sliders[attrs[stat]].slider('enable')
            sliders[attrs[stat]].slider("option", "min", 0 );
        }

        for (var stat in data) {
            if (data[stat] == false) {
                sliders[stat].slider('disable')
                sliders[stat].slider("value", 0 );
            }
            else {
                var force_value = parseInt( maxSumm / 100* data[stat])
                sliders[stat].slider("option", "min", force_value );
                sliders[stat].slider("value", force_value );
            }
        }
    }

    $typeSelect.change( function(e) {
        recalculateMinimum($(this))
    })
});