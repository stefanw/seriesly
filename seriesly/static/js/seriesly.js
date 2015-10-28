var checkSubscriptionCookie;
$(document).ready(function(){
    var SHOW_ITEM = '<li><a href="#toggle-{1}" class="label-minus">{0}</a></li>';
    var SUBSCRIPTION_MADE = '<section id="subscription-note" style="display:none" class="step">Note: You created a subscription recently. <a href="/{0}/">Go there now!</a></section>';

    var filter_list = function(e){
      var query = $("#search").val().toLowerCase();
      if (query == ""){
        $("#clear-search").hide();
        // Show all shows that have are not checked (i.e. are in the other box)
        $("#allshows-list li").show();
        return;
      }
      if (!$.browser.webkit){
          // Webkit has its own clear button in html5
        $("#clear-search").show();
      }
      // Check all list items that are not checked
      $("#allshows-list li").each(function(i, el){
          var text = $(el).find("label").text().toLowerCase().replace(/^\s(.*)$/, "$1");
          var alttext = text.replace(/^(.*), the$/, "the $1");
          if (text.indexOf(query) == -1 && alttext.indexOf(query) == -1){
              $(el).hide();
          } else {
              $(el).show();
        }
      });
    };

    var clear_search = function(e){
      if(e){e.preventDefault();}
      $("#search").val("");
      filter_list(e);
    };

    var order_lis = function(ul){
        var lis = ul.find("li");
        lis.sort(function(a,b){
            a = $(a).text().toLowerCase();
            b = $(b).text().toLowerCase();
            if (a <  b){
                return -1;
            }
            if (a > b){
                return 1;
            }
            return 0;
        });
        ul.empty().append(lis);
    };

    var add_li = function(li){
        var label = li.find("label").text();
        var show_id = li.find("label").attr("for").split("_")[2];
        $("#chosenshows-list").prepend(SHOW_ITEM.replace(/\{0\}/,label).replace(/\{1\}/, show_id));
        order_lis($("#chosenshows-list"));
        li.css({"backgroundColor": "#ffff99"}).find("label").addClass("label-minus");
        li.find("input").attr("checked", "checked");
    };

    var remove_li = function(show_id){
        var li = $("#id_shows_"+show_id).attr("checked", "").parent().parent();
        li.css({"backgroundColor": null})
            .find("label").removeClass("label-minus");
        $("#chosenshows-list li a[href='#toggle-"+show_id+"']").parent().remove();
    };

    var toggle_show = function(e){
      var show_id;
      if(e){e.preventDefault();}
      var li = $(this);
      var list_id = li.parent().attr("id");
      if (list_id == "chosenshows-list" || (list_id == "allshows-list" && li.find("input").attr("checked"))){

        if(list_id == "allshows-list"){
            show_id = li.find("label").attr("for").split("_")[2];
        } else {
            show_id = li.find("a").attr("href").split("-")[1];
        }
        remove_li(show_id);

      } else {
        // Select clicked show
        add_li(li);
      }
      checks();
    };

    var checks = function(){
        // Hide "no shows" error, if it was last error
        if($(".select-shows .errorlist").text().indexOf("least") != -1){
            $(".select-shows .errorlist").hide("fast");
        }
        // Remind user of his current too many shows error
        if ($("#chosenshows-list li").length > 90){
            if($(".select-shows .errorlist").text().indexOf("maximum") != -1){
                $(".select-shows .errorlist").show();
            }
        }
        $("#chosenshows-label").text("You have chosen these shows:");
        // Clear search if there are no shows visible and the search box is not empty
        if ($("#allshows-list li:visible").length == 0 && $("#search").val() != ""){
            clear_search();
        }
          // No more shows selected:
        if ($("#chosenshows-list li").length == 0){
          $("#chosenshows-label").text("You haven't chosen any shows yet.");
          // If last error was "no shows", remind user
          if($(".select-shows .errorlist").text().indexOf("least") != -1){
              $(".select-shows .errorlist").show();
          }
        }
        // Hide too many shows error, when user complies
        if ($("#chosenshows-list li").length <= 90){
            if($(".select-shows .errorlist").text().indexOf("maximum") != -1){
                $(".select-shows .errorlist").hide();
            }
        }
    };

    checkSubscriptionCookie = function(){
      var subkey = readCookie("subkey");
      if (subkey != null){
          $("#content").prepend(SUBSCRIPTION_MADE.replace(/\{0\}/, subkey));
          $("#subscription-note").slideDown();
          $("#subscription-note").css("background-color", "#ffd");
          window.setTimeout(function(){
              $("#subscription-note").css("background-color", "#fff");
          },1000);
      }
    };

    var readCookie = function (name){
        /* Too lazy to use a jquery plugin for this */
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for(var i=0;i < ca.length;i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1,c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
        }
        return null;
    };

    $("#chosenshows").show();
    $("#search-fields").show();
    $(".show-list li input").hide();
    // i can haz placeholder attribute?
    var i = document.createElement('input');
    if (!('placeholder' in i)){
    // No? Emulating...
        $(".default-value").focus(function(e){
          if($(this).val() == $(this).attr("placeholder")){
            $(this).removeClass("greyish");
            $(this).val("");
          }
        });
        $(".default-value").blur(function(e){
          if($(this).val() == ""){
            $(this).addClass("greyish");
            $(this).val($(this).attr("placeholder"));
          }
        });
        $(".default-value").each(function(i, el){
            $(this).val($(this).attr("placeholder")).addClass("greyish");
        });
    }
    // Simple Div-Toggling with no-smart text replace
    // Show is missing? becomes Hide is missing? -> Interface Easter Egg
    $(".toggle").click(function(e){
    e.preventDefault();
    // Magic here: #some-anchor becomes id css-selector
    var label = $(this);
    var div = $(label.attr("href"));
    if (div.css("display") == "none"){
      label.text(label.text().replace(/Show/, "Hide"));
      div.show();
    } else {
      label.text(label.text().replace(/Hide/, "Show"));
      div.hide();
    }
    });
    $("#search").keyup(filter_list);
    $("#search").click(filter_list); // For mac clear search
    $("#search").change(filter_list);
    $("#search").keydown(function(e){
        // Hitting Return should not submit, but search
        if (e.keyCode == 13){e.preventDefault();}
        if (e.keyCode == 27){$("#search").val("");}
        filter_list(e);
    });
    $("#clear-search").click(clear_search);
    $(".show-list li").live("click",toggle_show);
    // Put checked shows in chosen-shows box
    $("#allshows-list li input:checked").each(function(i, el){
      add_li($(el).parent().parent());
    });
    checks();
    if(document.location.hash !== "" && document.location.hash.indexOf("shows=") != -1){
        var shows = document.location.hash;
        shows = shows.replace(/#?shows=/,'');
        shows = shows.split(',');
        $('#allshows-list input').each(function(){
            if($.inArray($(this).attr("data-tvrage"), shows) != -1){
                add_li($(this).parent().parent());
            }
        });
        checks();
    }
});
