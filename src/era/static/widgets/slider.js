$(function() {
    $("[data-slider-min]").each(function() {
        var $this = $(this);
        var options = {};
        ["precision", "reversed", "tooltip"].map(function(k) {
            options[k] = $this.data("slider-" + k);
        })
        $this.slider(options);
    })
    $(".slider-handle").each(function() {
        $(this).addClass("input-group-addon");
        $(this).css("background", $(this).css("color"));
        $(this).removeClass("input-group-addon");
    })
    $(".slider-selection").each(function() {
        $(this).addClass("input-group-addon");
        $(this).css("background", $(this).css("background-color"));
        $(this).removeClass("input-group-addon");
    })
})
