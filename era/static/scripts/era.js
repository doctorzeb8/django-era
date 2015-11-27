function Form(cls, props) {
    if (props.spinner) {
        $('form[action="' + props.action + '"]').submit(function(event) {
            $(this).find('.actions').html(props.spinner);
        })
    }
}

function SearchLine(cls, props) {
    $(cls).val($.query.get('search'));
    $(cls).keypress(function (e) {
        if (e.which == 13) {
            var value = $(this).val();
            if (value) {
                window.location.search = $.query.set("search", value);
            } else {
                window.location.search = $.query.REMOVE("search");
            }
        }
    })
}
