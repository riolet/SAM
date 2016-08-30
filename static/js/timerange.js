// Create a new date from a string, return as a timestamp.
function timestamp(str){
    return new Date(str).getTime();
}

// Create a string representation of the date.
function formatDate ( date ) {
    return formatPip().to(date.valueOf());
}


function formatPip () {
    bob = {}
    bob.to = function(val) {
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
    bob.from = function(datetimestring) {
        return new Date(datetimestring).getTime();
    };
    return bob;
}

function slider2_init() {
    var dateSlider = document.getElementById('slider-date');

    noUiSlider.create(dateSlider, {
        // Create two timestamps to define a range.
        range: {
            min: timestamp('2016-06-19 00:00'),
            max: timestamp('2016-06-21 23:55')
        },

        // Steps of 5 minutes
        step: 5 * 60 * 1000,

        // at least 5 minutes between handles
        margin: 5 * 60 * 1000,

        // Two more timestamps indicate the handle starting positions.
        start: [ timestamp('2016-06-19 19:00'), timestamp('2016-06-20 08:00') ],

        // Shade the selection
        connect: true,
        // Allow range draggin
        behaviour: "drag",

        pips: {
            mode: 'count',
            values: 5,
            stepped: true,
            density: 6,
            format: {"to": function(v) { return ""; } }
        }
    });


    var inputA = document.getElementById('input-start');
    var inputB = document.getElementById('input-end');
    var converter = formatPip();

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

$(slider2_init);