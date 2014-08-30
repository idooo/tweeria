$(function () {

    var $tabContainer = $("#shop-tabs")
        , $tabContentDiv = $tabContainer.find(".shop-tab-content")
        , $shopHeaderTitle = $(".shop-head-title")
        , $tabHead = $(".shop-tabs-head")
        , $tabHeadItem = $tabHead.find("li")
        , $tabOverlay = $("#tab-overlay")
        , $form = $(".item-filter form")
        , $goldContainer = $("#player-gold span")
        , $shopTabContent = $(".shop-tab-content")
        , $triviaButtonSelled = $("<div class=\"applyed\"></div>")
        , $shopLoader = $("<div class='shop-loader'><img src='/style/img/ajax-loader_2.gif' /></div>")
        , filterToggleFields = [
            "search", "author",
            "cost_min", "cost_max",
            "level_min", "level_max",
            "type", "race", "class",
            "keyword", "tag"
        ]
        ,
    /* templates */
        $pagerTmpl = $("#shop-pager-tmpl"),

        $successMessage = $("#success-message-tmpl"),
        $errorMessage = $("#error-message-tmpl"),

        itemBonusText = {
            'DEF':"Defense",
            'DMG':"Damage",
            'HP':"Hit Points",
            'MP':"Mana Points",
            'dex':"Dexterity",
            'int':"Intelect",
            'luck':"Luck",
            'str':"Strength"
        },
        tabsByCode = {
            "#!tab-new":0,
            "#!tab-items":1,
            "#!tab-spells":2,
            "#!tab-artworks":3,
            "#!tab-fun":4,
            "#tab-new":0,
            "#tab-items":1,
            "#tab-spells":2,
            "#tab-artworks":3,
            "#tab-fun":4
        },
        popupedSelector = {
            "item":".cluetip_popup_shop",
            "spell":".popuped_spells",
            "artwork":".artwork"
        },
        indexTab = (document.location.hash === "") ? 0 : tabsByCode[document.location.hash],
        openArtworkPopup = function ($this) {
            var data = $this.data(),
                $tmpl = $("#shop-artwork-popup").tmpl(data);

            $.fancybox($tmpl, {
                closeBtn:false,
                wrapCSS:"tweenk-popup",
                padding:0,
                helpers:{
                    overlay:{
                        css:{
                            "background":"transparent"
                        }
                    }
                }
            });
        },
        openSpellPopup = function ($this) {
            var data = $this.data();


            $.fancybox($("#shop-spell-popup").tmpl(data), {
                closeBtn:false,
                wrapCSS:"tweenk-popup",
                padding:0,
                helpers:{
                    overlay:{
                        css:{
                            "background":"transparent"
                        }
                    }
                }
            });
        },
        openItemPopup = function ($this) {
            var data = $this.data(),
                bonusparsed = {};

            data.bonus = (data.bonus == undefined) ? "" : data.bonus;

            if (data.bonus != "") {
                if (data.need_parse_bonus == "N") {
                    bonusparsed = data.bonus;
                } else {
                    bonusparsed = JSON.parse(data.bonus.replace(/'/g, "\""));
                }
            }

            data.bonusparsed = {};
            $.each(bonusparsed, function (index, value) {
                data.bonusparsed[index] = "+" + value['value'] + " " + value['name'];
            });

            $.fancybox($("#shop-item-popup").tmpl(data), {//item popup
                closeBtn:false,
                wrapCSS:"tweenk-popup",
                padding:0,
                autoSize:true,
                helpers:{
                    overlay:{
                        css:{
                            "background":"transparent"
                        }
                    }
                }
            });
        },

        /**
         * functions
         * */

        updatePager = function (data, $tab, type) {

            var page_type = 0;
            if (type == "spell") {
                page_type = data.param_ps
            }
            else if (type == "artwork") {
                page_type = data.param_pa
            }
            else {
                page_type = data.param_pi
            }

            var $pager = $tab.find(".pager"),
                tmplData = {
                    pagesToShow:data["display_" + type + "s_pages"],
                    currentPage:page_type,
                    totalPages:data[type + "_pages"],
                    type:type
                },

                html = (tmplData.totalPages > 1) ? $pagerTmpl.tmpl(tmplData) : "";

            //console.log(tmplData);
            if (tmplData.totalPages > 1) {
                $pager.html(html).show();
            } else {
                $pager.html(html).hide();
            }
        },
        prepareFilterForm = function ($form, formData) {
            var toggleFilter = false;

            if (formData) {
                $.each(formData, function (index, value) {
                    $form.find("[name='" + value.name + "']").val(value.value);
                    if (in_array(value.name, filterToggleFields)
                        && value.value!=""
                        //&& (value.name=="race" && value.value!="-1:-1")
                        //&& (value.name=="class" && value.value!="0")
                        ) {
                        toggleFilter = true;
                    }
                });
                if (toggleFilter) {
                    $form.find(".clear_filter_btn").fadeIn();
                    $form.parents(".shop-option-block").find(".shop-filter-button").addClass("active");
                    $form.parents(".item-filter").show();
                }
            }
        },
        getShopTriviaNewData = function (type, $tab) {
            var view = "list",
                $cont = $("#shop-" + type + "s-" + view);
            $cont.html($shopLoader);

            $("html, body").animate({ scrollTop:0 }, 600, function () {

                $.ajax({
                    url:"/u/shop/?page_type=" + type,
                    dataType:'json',
                    success:function (data) {

                        var $tmpl = $("#shop-" + type + "s-" + view + "-tmpl"),
                            html = (typeof data.html === "undefined") ? $tmpl.tmpl(data) : data.html;

                        $cont.html(html.html);

                        console.log("#shop-" + type + "s-" + view + " .cluetip_popup_shop")
                        $("#shop-" + type + "s-" + view + " .cluetip_popup_shop").cluetip({splitTitle:'|'});
                    }
                });

            });
        },
        getShopData = function (type, view, viewCode, $form, $tab) {


            var $cont = $("#shop-" + type + "s-" + view),
                formParamsString = JSON.stringify($form.serializeArray());

            sessionStorage.setItem($form[0].id, formParamsString);

            $cont.html($shopLoader);

            $("html, body").animate({ scrollTop:0 }, 600, function () {

                //$.getJSON("/u/shop/?page_type=" + type + "s&view=" + viewCode, $form.serialize(), function (data) {
                $.ajax({
                    url:"/u/shop/?page_type=" + type + "s&view=" + viewCode,
                    dataType:'json',
                    data:$form.serialize(),
                    success:function (data) {

                        var $tmpl = $("#shop-" + type + "s-" + view + "-tmpl"),
                            html = (typeof data.html === "undefined") ? $tmpl.tmpl(data) : data.html;

                        //console.log(type,view,data, $tab[0], html[0]); //TODO удалить

                        $cont.html(html.html);

                        //if (typeof data.artwork == "undefined"){
                        updatePager(data, $tab, type);

                        if (type != "artwork") {
                            $("#shop-" + type + "s-" + view + " .cluetip_popup_shop").cluetip({splitTitle:'|'});
                        }

                        $form.find("#item_page").val("1").end().find("#spell_page").val("1");
                    }
                });

            });
        },
        showMessage = function (messageHtml, data, noFb) {
            $shopHeaderTitle.append(messageHtml);
            if (typeof noFb === "undefined" || noFb == true) {
                $.fancybox.close();
            }
            $goldContainer.html(data.gold);
            messageHtml.delay(5000).fadeOut("slow", function () {
                $(this).remove();
            });

        };

    var tabHandlerShow = function (event, ui) {
        var iL = $tabHeadItem.length;

        $tabOverlay.hide();
        $shopHeaderTitle.show();
        $tabHead.show();
        $tabContentDiv.show();


        $tabHeadItem.each(function (index) {
            var $this = $(this);

            if ($this.hasClass("ui-tabs-selected")) {
                $this.css({
                    "position":"relative",
                    "z-index":iL + 1
                });
            } else {
                $this.css({
                    "position":"relative",
                    "z-index":iL - index
                });
            }
        });


    };

    var tabHandlerCreate = function (event, ui) {
        tabHandlerShow(event, ui);

        //ui.panel = $shopTabContent[indexTab];
        ui.panel = $("#shop-tabs .shop-tab-content")[indexTab];

        //Загружаем нужный блок через ajax
        if (indexTab == 0 || indexTab == 4) {
            var type = "new";
            if (indexTab == 4) {
                type = "trivia"
            }
            getShopTriviaNewData(type);
        } else {
            type = "item";

            var $tab = $(ui.panel),
                $form = $tab.find(".item-filter form"),
                view = "table",
                viewCode = 0,
                sessionParams = sessionStorage.getItem($form[0].id);

            //Проверяем данные в sessionStorage и подставляем данные в форму
            if (sessionParams != "null") {
                sessionParams = JSON.parse(sessionParams);
                prepareFilterForm($form, sessionParams);
            }

            if (strpos(ui.panel.id, "spell") === 0 || strpos(ui.panel.id, "spell") > 0) {
                type = "spell";
            } else if (strpos(ui.panel.id, "artwork") === 0 || strpos(ui.panel.id, "artwork") > 0) {
                type = "artwork";
                view = "list";
            }
            if ($("#" + type + "-view-list").hasClass("active")) {
                view = "list";
                viewCode = 1;
            }
            getShopData(type, view, viewCode, $form, $tab);
        }
    };

    var tabSelectHandler = function (event, ui) {
        var scroll = $(document).scrollTop(),
            selected = tabs.tabs("option", "selected"),
            href = ui.tab.pathname + ui.tab.hash.replace("#", "#!");


        if (ui.index == selected) {
            event.preventDefault();
            if (selected > 0)
                document.location = href;
        }
        document.location.hash = (ui.tab.hash != undefined) ? "!" + ui.tab.hash.substr(1) : "";

        $(document).scrollTop(scroll);


        //Загружаем нужный блок через ajax
        var type = "";
        if (ui.index == 0 || ui.index == 4) {
            type = "new";
            if (ui.index == 4) {
                type = "trivia"
            }
            getShopTriviaNewData(type);
        } else {
            type = "item";

            var $tab = $(ui.panel),
                $form = $tab.find(".item-filter form"),
                view = "table",
                viewCode = 0,
                sessionParams = sessionStorage.getItem($form[0].id);


            //при переходе по табам очищаем  sessionStorage
            sessionStorage.clear();
            $form.find("input:text").each(function () {
                $(this).val("");
            }).end().find("select").each(function () {
                    $(this).val("");
                });

            //Проверяем данные в sessionStorage и подставляем данные в форму
            if (sessionParams != "null") {
                sessionParams = JSON.parse(sessionParams);
                prepareFilterForm($form, sessionParams);
            }


            if (strpos(ui.panel.id, "spell") === 0 || strpos(ui.panel.id, "spell") > 0) {
                type = "spell";
            } else if (strpos(ui.panel.id, "artwork") === 0 || strpos(ui.panel.id, "artwork") > 0) {
                type = "artwork";
                view = "list";
            }
            if ($("#" + type + "-view-list").hasClass("active")) {
                view = "list";
                viewCode = 1;
            }
            getShopData(type, view, viewCode, $form, $tab);
        }
    };

    var tabs = $tabContainer.tabs({
        selected:indexTab,
        show:tabHandlerShow,
        create:tabHandlerCreate,
        select:tabSelectHandler,
        collapsible:true
    });

    $form.find("select").uniform({
        selectWidth:225
    });
    $(".selector").show();

    $(".shop-item-table .cluetip_popup_shop").cluetip({splitTitle:'|'});
    $(".shop-item-list li img").cluetip({splitTitle:'|'});

    /**
     * @description Сортировка
     */
    $shopTabContent.on("click", ".shop-item-table th a", function (e) {
        e.preventDefault();
        var $this = $(this),
            sortField = $this.data("field"),
            sortOrder = $this.data("order") || "1",
            newOrder = (sortOrder == "1") ? "-1" : "1",
            type = $this.data("type") || "item";

        $("#" + type + "_sorting_field").val(sortField);
        $("#" + type + "_sorting_order").val(sortOrder);
        $this.data("order", newOrder);

        $("#" + type + "_filter").submit();
    });

    /**
     * @description Пагинация
     */
    $shopTabContent.on("click", ".pager a", function (e) {

        e.preventDefault();
        var $this = $(this),
            page = $this.data("page") || parseInt($this.text()) || 1,
            type = $this.data("type") || "item";

        $("#" + type + "_page").val(page);
        $("#" + type + "_filter").submit();
        return false;
    });


    /**
     * @description шаринг
     * @type {String}
     */
    var popupOptions = "menubar=no,location=no,resizable=yes,scrollbars=yes,status=no";
    $shopTabContent.on("click", ".achv-share-button", function (e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this),
            url = $this.attr("href");

        if ($this.hasClass("gp")) {
            var data = $this.data();

            $("#gp-widget-title").prop("content", data.title);
            $("#gp-widget-desc").prop("content", data.desc);
            $("#gp-widget-img").prop("content", data.image);

            $("#og-title").prop("content", data.title);
            $("#og-desc").prop("content", data.desc);
            $("#og-url").prop("content", data.url);
            $("#og-img").prop("content", data.image);
        }

        var popup = window.open(url, 'Share', "width=565,height=480," + popupOptions);
        popup.focus();
    });

    var $filterButton = {
            "item":$("#item-filter-button"),
            "spell":$("#spell-filter-button"),
            "artwork":$("#artwork-filter-button"),
            "selectors":".shop-filter-button"

        },
        $filterBlock = {
            "item":$("#item-filter"),
            "spell":$("#spell-filter"),
            "artwork":$("#artwork-filter")
        },
        $viewButton = {
            "item":{
                "list":$("#item-view-list"),
                "table":$("#item-view-table")
            },
            "spell":{
                "list":$("#spell-view-list"),
                "table":$("#spell-view-table")
            },
            "selector":".shop-view-list,.shop-view-table"
        },
        $viewCotainer = {
            "item":{
                "list":$("#shop-items-list"),
                "table":$("#shop-items-table")
            },
            "spell":{
                "list":$("#shop-spells-list"),
                "table":$("#shop-spells-table")
            }};


    $shopTabContent.on("click", $filterButton['selectors'], function (e) {//Клик на кнлпку фильтра

        e.preventDefault();

        var type = "spell";
        if ($(this)[0].id == "item-filter-button") {
            type = "item";
        } else if ($(this)[0].id == "artwork-filter-button") {
            type = "artwork";
        }

        $filterBlock[type].toggle();
        $filterButton[type].toggleClass("active");
    })
        .on("click", $viewButton["selector"], function (e) {
            e.preventDefault();
            var $this = $(this);

            if ($this.hasClass("active")) {
                return false;
            }

            var type = "item",
                view = ["table", "list"],
                viewCode = 0,
                $parent = $this.parents(".shop-option-block"),
                $tab = $parent.parents(".shop-tab-content"),
                $form = $parent.find(".item-filter form");

            if (strpos($(this)[0].id, "spell") === 0 || strpos($(this)[0].id, "spell") > 0) {
                type = "spell";
            }
            if (strpos($(this)[0].id, "list") === 0 || strpos($(this)[0].id, "list") > 0) {
                view = ["list", "table"];
                viewCode = 1;
            }

            $this.addClass("active");
            $viewButton[type][view[1]].removeClass("active");
            $viewCotainer[type][view[1]].hide();
            $viewCotainer[type][view[0]].show();

            //console.log("STR 416");
            getShopData(type, view[0], viewCode, $form, $tab);
        })
        .on("submit", ".item-filter form", function (e) {
            e.preventDefault();
            var $this = $(this),
                $parent = $this.parents(".item-filter"),
                $tab = $parent.parents(".shop-tab-content"),
                $form = $this,
                type = "item",
                view = "table",
                viewCode = 0;

            if (strpos($parent[0].id, "spell") === 0 || strpos($parent[0].id, "spell") > 0) {
                type = "spell";
            } else if (strpos($parent[0].id, "artwork") === 0 || strpos($parent[0].id, "artwork") > 0) {
                type = "artwork";
                view = "list";
            }
            if ($("#" + type + "-view-list").hasClass("active")) {
                view = "list";
                viewCode = 1;
            }

            //console.log("STR 440");
            getShopData(type, view, viewCode, $form, $tab);
            $form.find(".clear_filter_btn").fadeIn("fast");

        })
        .on("click", ".clear_filter_btn", function (e) {

            e.preventDefault();
            var $form = $(this).parents("form");

            $form.find("input:text").each(function () {
                $(this).val("");
            }).end().find("select").each(function () {
                    $(this).val("");
                });

            $.uniform.update();
            $form.submit();
            $(this).fadeOut();


        })
        .on("click", ".trivia-item .can-buy", function (e) {

            e.preventDefault();

            var $this = $(this),
                $form = $this.parents("form");


            $.ajax({
                type:'POST',
                url:$form.attr("action"),
                data:$form.serialize() + "&ajax=1",
                success:function (data) {
                    var html = "";
                    //console.log(data);
                    if (data.success == 1) {
                        html = $successMessage.tmpl(data);
                        getShopTriviaNewData("trivia");
                        //$triviaButtonSelled.clone().insertAfter($this);
                        //$this.remove();
                    } else if (data.error == 1) {
                        html = $errorMessage.tmpl(data);
                    }
                    showMessage(html, data, true);
                },
                error:function (tmp) {
                    //console.log(tmp);
                },
                dataType:"json"
            });
        });


    $("body").on("click", ".buy-button", function (e) {

        e.preventDefault();

        var $this = $(this),
            $form = $this.parents("form"),
            type = "item",
            view = "list",
            viewCode = 1,
            tabIndex = tabs.tabs("option").selected,
            $tab = $(tabs.find(".shop-tab-content")[tabIndex]),
            $activeButton = $tab.find(".shop-view-toggler.active"),
            $filterForm = $tab.find(".item-filter form");

        if (tabIndex == 2) {
            type = "spell";
        } else if (tabIndex == 3) {
            type = "artwork";
        }
        if ($activeButton.size() > 0) {
            view = $activeButton.text().toLowerCase();
            viewCode = (view == "list") ? 1 : 0;
        } else {
            view = "list";
        }

        //console.log($form[0],$form.serialize());

        $.ajax({
            type:'POST',
            url:$form.attr("action"),
            data:$form.serialize() + "&ajax=1",
            success:function (data) {
                var html = "";
                //console.log(data);
                if (data.success == 1) {
                    html = $successMessage.tmpl(data);
                } else if (data.error == 1) {
                    html = $errorMessage.tmpl(data);
                }
                showMessage(html, data);
                //console.log("GET DATA AFTER BUY");
                //console.log("STR 532");
                getShopData(type, view, viewCode, $filterForm, $tab);
            },
            error:function (tmp) {
                //console.log(tmp);
            },
            dataType:"json"
        });
    });
    $shopTabContent.on("click", ".inline-like-button", function (e) {
        e.preventDefault();

        inlineLikeClick($(this));
    }).on("click","table.shop-item-table tbody tr, table.shop-spell-table tbody tr",function(e){
            e.preventDefault();
            var href = $(this).find("a:first").attr("href");
            if (typeof href!=='undefined'){
                document.location=href;
            }
        });



});
