function dateConverter() {
    "use strict";
    var cnv = {};
    cnv.to = function(val) {
        var date = new Date(val * 1000);
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
        var val = new Date(datetimestring).getTime()
        return val / 1000;
    };
    return cnv;
}

/*
	Main function responsible for the time slider, It creates the slider if it hasn't been made, otherwise it updates the slider.
*/
function slider_init() {
  "use strict";
  let newMin = config.tmin;
  let newMax = config.tmax;
  let newStart = config.tstart;
  let newEnd = config.tend;

  //dateslider object in the menu
  let dateSlider = document.getElementById('slider-date');

  //if the slider doesn't exist, create it.
  if (dateSlider.noUiSlider === undefined) {
    create_slider(newMin, newMax, newStart, newEnd);
  }

  //Otherwise, update time range and selection.
  else {
    update_slider(newMin, newMax, newStart, newEnd);
  }
}

function create_slider(tmin, tmax, tstart, tend) {
  "use strict";
  var dateSlider = document.getElementById('slider-date');

  noUiSlider.create(dateSlider, {
    // Create two timestamps to define a range.
    range: {
      min: tmin,
      max: tmax
    },

    // Steps of 5 minutes
    step: 5 * 60,

    // at least 5 minutes between handles
    margin: 5 * 60,

    // Two more timestamps indicate the default handle starting positions.
    start: [ tstart, tend],

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
      config.tend = Math.round(value);
    } else {
      inputA.value = converter.to(Math.round(value));
      config.tstart = Math.round(value);
    }
  });
  dateSlider.noUiSlider.on('end', function(){
    sel_remove_all(m_nodes);
    sel_set_selection(m_selection.selection)
    links_reset();
    updateRenderRoot();
    render_all();
  });

  inputA.addEventListener('change', function(){
    dateSlider.noUiSlider.set([converter.from(this.value), null]);
  });

  inputB.addEventListener('change', function(){
    dateSlider.noUiSlider.set([null, converter.from(this.value)]);
  });
}

function update_slider(tmin, tmax, tstart, tend) {
  "use strict";
  var dateSlider = document.getElementById('slider-date');

  //set slider handles
  dateSlider.noUiSlider.updateOptions({
		range: {
			'min': tmin,
			'max': tmax
		}
	});
  dateSlider.noUiSlider.set([tstart, tend]);
}