// Create a string representation of the date.
function formatDate ( date ) {
    return formatPip().to(date.valueOf());
}


function dateConverter() {
    cnv = {}
    cnv.to = function(val) {
        var date = new Date(val);
        var year    = date.getFullYear();
        var month   = date.getMonth()+1;
        var day     = date.getDate();
        var hour    = date.getHours();
        var minute  = date.getMinutes();
        var second  = date.getSeconds();
        if(month.toString().length == 1) {
            var month = '0'+month;
        }
        if(day.toString().length == 1) {
            var day = '0'+day;
        }
        if(hour.toString().length == 1) {
            var hour = '0'+hour;
        }
        if(minute.toString().length == 1) {
            var minute = '0'+minute;
        }
        if(second.toString().length == 1) {
            var second = '0'+second;
        }
        var dateTime = year+'-'+month+'-'+day+' '+hour+':'+minute;
        return dateTime;
    };
    cnv.from = function(datetimestring) {
        return new Date(datetimestring).getTime();
    };
    return cnv;
}

function slider_init() {
    $.ajax({
        url: "/stats",
        type: "GET",
        data: {'q': 'timerange'},
        dataType: "json",
        error: onNotLoadData,
        success: function (response) {
            create_slider(Math.floor(response.min * 1000), Math.floor(response.max * 1000));
        }
    });
}

function create_slider(dtmin, dtmax) {
    var dateSlider = document.getElementById('slider-date');

    noUiSlider.create(dateSlider, {
        // Create two timestamps to define a range.
        range: {
            min: dtmin,
            max: dtmax
        },

        // Steps of 5 minutes
        step: 5 * 60 * 1000,

        // at least 5 minutes between handles
        margin: 5 * 60 * 1000,

        // Two more timestamps indicate the handle starting positions.
        start: [ dtmin, dtmax ],


        // Shade the selection
        connect: true,
        // Allow range draggin
        behaviour: "drag",

        pips: {
            mode: 'count',
            values: 5,
            stepped: true,
            density: 6,
            format: {"to": function(v) { return ""; } } //no labels
        }
    });

    var inputA = document.getElementById('input-start');
    var inputB = document.getElementById('input-end');
    var converter = dateConverter();

    dateSlider.noUiSlider.on('update', function( values, handle ) {
        var value = values[handle];
        if ( handle ) {
            inputB.value = converter.to(Math.round(value));
        } else {
            inputA.value = converter.to(Math.round(value));
        }
    });

    inputA.addEventListener('change', function(){
        dateSlider.noUiSlider.set([converter.from(this.value), null]);
    });

    inputB.addEventListener('change', function(){
        dateSlider.noUiSlider.set([null, converter.from(this.value)]);
    });
}

$(slider_init);