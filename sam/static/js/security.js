function deselectText() {
    "use strict";
    if (window.getSelection) {
        if (window.getSelection().empty) {  // Chrome
            window.getSelection().empty();
        } else if (window.getSelection().removeAllRanges) {  // Firefox
            window.getSelection().removeAllRanges();
        }
    } else if (document.selection) {  // IE?
        document.selection.empty();
    }
}

function generic_ajax_failure(xhr, textStatus, errorThrown) {
    "use strict";
    console.error("Failed to load data: " + errorThrown);
    console.log("\tText Status: " + textStatus);
}

function generic_ajax_success(response) {
    if (response.hasOwnProperty("result")) {
        console.log("Result: " + response.result);
    }
}

function normalizeIP(ipString) {
  "use strict";
  var add_sub = ipString.split("/");

  var address = add_sub[0];
  var subnet = add_sub[1];

  var segments = address.split(".");
  var num;
  var final_ip;
  segments = segments.reduce(function (list, element) {
    num = parseInt(element);
    if (!isNaN(num) && list.length < 4) {
      list.push(num);
    }
    return list;
  }, []);

  final_ip = segments.join(".");

  var zeroes_to_add = 4 - segments.length;
  if (zeroes_to_add == 4) {
    final_ip = '0.0.0.0';
  } else {
    while (zeroes_to_add > 0) {
      final_ip += ".0";
      zeroes_to_add -= 1;
    }
  }
  num = parseInt(subnet);
  if (!isNaN(num)) {
    final_ip += "/" + subnet;
  } else {
    final_ip += "/" + (segments.length * 8);
  }
  return final_ip;
}

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

function getConfirmation(msg, confirmCallback, denyCallback) {
    "use strict";
    let modal = document.getElementById("deleteModal");
    let modalMsg = document.getElementById("deleteMessage")
    modalMsg.innerHTML = "";
    modalMsg.appendChild(document.createTextNode(msg));
    $(modal).modal({
        onDeny: denyCallback,
        onApprove: confirmCallback
    })
    .modal("show");
}

//settings
(function () {
  "use strict"
  let user = {
    endpoint: "./settings",
    settings: {},
    datasources: [],
    datasource: {},
    ds: 0,
    callbacks: [],

    GET_settings: function () {
      var requestData = {"headless": 1};
      $.ajax({
          url: user.endpoint,
          type: "GET",
          data: requestData,
          dataType: "json",
          error: generic_ajax_failure,
          success: function (settings) {
            user.settings = settings;
            user.datasources = [];
            Object.keys(settings.datasources).forEach( function (key) {
              user.datasources.push(settings.datasources[key]);
            });
            user.datasource = settings.datasources[settings.datasource];
            user.ds = settings.datasource;

            user.callbacks.forEach( function (cb) { cb(); });
          }
      });
    },

    add_callback: function (cb) {
      if (typeof(cb) === "function") {
        user.callbacks.push(cb);
      }
    }
  }
  window.user = user;
}());

//rules object
(function () {
  "use strict";
  let rules = {
    endpoint: './sec_rules',
    endpoint_new: './sec_rules/new',
    endpoint_edit: './sec_rules/edit',
    endpoint_reapply: './sec_rules/reapply',
    endpoint_timerange: './stats',
    reapply_range: {
      min: 1495500000,
      max: 1495600000,
      start: 1495520000,
      end: 1495580000
    },
    templates: null,

    init: function () {
      //activate modal checkboxes
      $('#er_modal .ui.checkbox')
        .checkbox({
        onChecked: function() {
          console.log("Checked, ", this);
        },
        onUnchecked: function(e) {
          console.log("Unchecked, ", this);
        }
        })
      ;

      //active new rule button
      document.getElementById("add_rule").onclick = rules.new_rule;

      //active reapply rules button
      document.getElementById("reapply_rules").onclick = rules.reapply;

      //register callback for reapply modal ds_list
      user.add_callback(rules.repopulate_ds_list);

      //set reapply modal ds_list to be "loading"
      let input = document.getElementById("rules_ds_input");
      input.parentElement.classList.add("loading");

      //set new rule modal definition list to be "loading"
      input = document.getElementById("newRuleTemplate");
      input.parentElement.classList.add("loading");

      //in reapply modal, hook up text inputs to time slider
      let inputA = document.getElementById('input-start');
      let inputB = document.getElementById('input-end');
      let converter = dateConverter();
      let dateSlider = rules.reapply_update_timeslider(rules.reapply_range);
      inputA.addEventListener('change', function(){
        dateSlider.noUiSlider.set([converter.from(this.value), null]);
      });
      inputB.addEventListener('change', function(){
        dateSlider.noUiSlider.set([null, converter.from(this.value)]);
      });

      //load all rules
      rules.GET_rules();
    },

    GET_rules: function(callback) {
      let loader = document.getElementById("rules_loader");
      loader.classList.add("active");
      $.ajax({
        url: rules.endpoint,
        type: "GET",
        dataType: "json",
        error: generic_ajax_failure,
        success: function (all_rules) {
          rules.update_table(all_rules.all);
          loader.classList.remove("active");
          if (typeof(callback) === "function") {
            callback(all_rules.all);
          }
        }
      });
    },
    GET_templates: function(callback) {
      $.ajax({
          url: rules.endpoint_new,
          type: "GET",
          dataType: "json",
          error: generic_ajax_failure,
          success: function (response) {
            rules.templates = response.templates;
            if (typeof(callback) === "function") {
              callback(response.templates);
            }
          }
      });
    },
    GET_edit_rule: function(rule_id, callback) {
      let requestData = {
        "id": rule_id,
      };
      //details are loading...
      let modalformA = document.getElementById("er_meta");
      modalformA.classList.add("loading");
      let modalformB = document.getElementById("er_actions");
      modalformB.classList.add("loading");
      let modalformC = document.getElementById("er_params");
      modalformC.classList.add("loading");

      $.ajax({
          url: rules.endpoint_edit,
          type: "GET",
          data: requestData,
          dataType: "json",
          error: generic_ajax_failure,
          success: function (response) {
            rules.populate_edit_modal(response);
            modalformA.classList.remove("loading");
            modalformB.classList.remove("loading");
            modalformC.classList.remove("loading");

            if (typeof(callback) === "function") {
              callback(response);
            }
          }
      });
    },
    GET_timerange: function(ds, callback) {
      let requestData = {
        "q": "timerange",
        "ds": ds
      }
      $.ajax({
          url: rules.endpoint_timerange,
          type: "GET",
          data: requestData,
          dataType: "json",
          error: generic_ajax_failure,
          success: function (response) {
            if (response.max == response.min) {
              //cannot have zero range.
              response.max = response.max + 300;
            }
            rules.reapply_range = {
              min: response.min,
              max: response.max,
              start: response.min,
              end: response.max
            }
            rules.reapply_update_timeslider(rules.reapply_range);

            if (typeof(callback) === "function") {
              callback(response);
            }
          }
      });
    },
    POST_new_rule: function(name, desc, template, callback) {
      let postData = {
        'name': name,
        'desc': desc,
        'template': template
      };
      $.ajax({
          url: rules.endpoint_new,
          type: "POST",
          data: postData,
          dataType: "json",
          error: generic_ajax_failure,
          success: function (response) {
            generic_ajax_success(response);
            if (response.result === "success") {
              rules.GET_rules();
            }
            if (typeof(callback) === "function") {
              callback(response);
            }
          }
      });
    },
    POST_delete_rule: function(rule_id, callback) {
      let postData = {
        "method": "delete",
        "id": rule_id,
      };
      $.ajax({
          url: rules.endpoint_edit,
          type: "POST",
          data: postData,
          dataType: "json",
          error: generic_ajax_failure,
          success: function (response) {
            generic_ajax_success(response);
            if (response.result === "success") {
              rules.GET_rules();
            }
            if (typeof(callback) === "function") {
              callback(response);
            }
          }
      });
    },
    POST_edit_rule: function(rule_id, edits) {
      let postData = {
        "method": "edit",
        "id": rule_id,
        "edits": edits
      };
      $.ajax({
          url: rules.endpoint_edit,
          type: "POST",
          data: postData,
          dataType: "json",
          error: generic_ajax_failure,
          success: function (response) {
            generic_ajax_success(response);
            if (response.result === "success") {
              rules.GET_rules();
            }
            if (typeof(callback) === "function") {
              callback(response);
            }
          }
      });
    },
    POST_reapply_rule: function(ds, start, end, callback) {
      let postData = {
        "ds": ds,
        "start": start,
        "end": end,
      };
      $.ajax({
          url: rules.endpoint_reapply,
          type: "POST",
          data: postData,
          dataType: "json",
          error: generic_ajax_failure,
          success: function (response) {
            generic_ajax_success(response);

            if (typeof(callback) === "function") {
              callback(response);
            }
          }
      });
    },

    clear_table: function () {
      let table = document.getElementById("rules_table");
      table.innerHTML = "";
    },
    update_table: function (new_rules) {
      rules.clear_table();
      new_rules.forEach(function (rule) {
        rules.add_rule(rule.id, rule.active, rule.name, rule.desc, rule.template);
      });
    },
    add_rule: function(id, active, name, desc, template) {
      let table = document.getElementById("rules_table");
      let tr = document.createElement("TR");
      let td, div, input, button, i;

      //add active checkbox td
      td = document.createElement("TD");
      div = document.createElement("DIV");
      div.className = "ui rule checkbox";
      input = document.createElement("INPUT");
      input.dataset['rule'] = id;
      input.tabIndex = "0";
      input.className = "hidden"
      input.type = "checkbox"
      if (active) {
        input.checked = "1";
      }
      input.appendChild(document.createElement("LABEL"));
      div.appendChild(input);
      td.appendChild(div);
      tr.appendChild(td);
      $(div).checkbox({
        onChecked: rules.rule_checkbox,
        onUnchecked: rules.rule_checkbox
        })
      ;

      //add name/desc td
      td = document.createElement("TD");
      td.dataset['tooltip'] = desc;
      td.dataset['position'] = "top left";
      td.innerText = name;
      tr.appendChild(td);

      //add template name td
      td = document.createElement("TD");
      td.innerText = template;
      tr.appendChild(td);

      //add edit button td
      td = document.createElement("TD");
      button = document.createElement("BUTTON");
      button.className = "ui small icon button";
      button.dataset['rule_id'] = id;
      button.onclick = rules.edit_rule;
      i = document.createElement("I");
      i.className = "blue edit icon";
      button.appendChild(i);
      td.appendChild(button);
      tr.appendChild(td);

      //add delete button td
      td = document.createElement("TD");
      button = document.createElement("BUTTON");
      button.className = "ui small icon button";
      button.dataset['rule_id'] = id;
      button.onclick = rules.delete_rule;
      i = document.createElement("I");
      i.className = "red remove icon";
      button.appendChild(i);
      td.appendChild(button);
      tr.appendChild(td);

      table.appendChild(tr);
    },
    edit_add_text_param: function (box, name, param) {
      let div = document.createElement("DIV");
      let label = document.createElement("LABEL");
      let input = document.createElement("INPUT");

      div.className = "field";
      label.innerText = param.label;
      input.name = name;
      input.placeholder = param.value;
      input.value = param.value;
      if (param.hasOwnProperty("regex"))
        input.dataset['regex'] = param.regex;
      
      div.appendChild(label);
      div.appendChild(input);
      box.appendChild(div);
    },
    edit_add_checkbox_param: function (box, name, param) {
      let div = document.createElement("DIV");
      let label = document.createElement("LABEL");
      let input = document.createElement("INPUT");

      div.className = "ui checkbox field";
      label.innerText = param.label;
      input.name = name;
      input.type = "checkbox";

      div.appendChild(label);
      div.appendChild(input);

      if (param.value) {
        $(div).checkbox("set checked");
      } else {
        $(div).checkbox("set unchecked");
      }
      
      box.appendChild(div);
    },
    edit_add_dropdown_param: function (box, name, param) {
      let div = document.createElement("DIV");
      let label = document.createElement("LABEL");
      let dd = document.createElement("DIV");
      let input = document.createElement("INPUT");
      let icon = document.createElement("I");
      let ddef = document.createElement("DIV");
      let dmenu = document.createElement("DIV");

      div.className = "field";
      label.innerText = param.label;
      dd.className = "ui selection dropdown";
      input.name = name;
      input.value = param.value;
      input.type = "hidden";
      icon.className = "dropdown icon";
      ddef.className = "default text";
      ddef.innerText = param.label;
      dmenu.className = "menu"

      param.options.forEach(function (option) {
        let ditem = document.createElement("DIV");
        ditem.className = "item";
        ditem.dataset['value'] = option;
        ditem.innerText = option;
        dmenu.appendChild(ditem);
      });

      dd.appendChild(input);
      dd.appendChild(icon);
      dd.appendChild(ddef);
      dd.appendChild(dmenu);
      div.appendChild(label);
      div.appendChild(dd);

      $(dd).dropdown();

      box.appendChild(div);
    },
    reapply_update_timeslider: function (range) {
      let dateSlider = document.getElementById('slider-date');

      if (dateSlider.noUiSlider !== undefined){
        dateSlider.noUiSlider.destroy();
      }

      noUiSlider.create(dateSlider, {
        // Create two timestamps to define a range.
        range: {
          min: range.min,
          max: range.max
        },

        // Steps of 5 minutes
        step: 5 * 60,

        // at least 5 minutes between handles
        margin: 5 * 60,

        // Two more timestamps indicate the default handle starting positions.
        start: [ range.start, range.end],

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
          range.end = Math.round(value);
        } else {
          inputA.value = converter.to(Math.round(value));
          range.start = Math.round(value);
        }
      });
      dateSlider.noUiSlider.on('end', function(){
        console.log("dateSlider event: END");
      });
      return dateSlider;
    },

    repopulate_ds_list: function () {
      let input = document.getElementById("rules_ds_input");
      let dropdown_items = document.getElementById("rules_ds_list");
      dropdown_items.innerHTML = "";

      //set options
      let div;
      user.datasources.forEach(function (datasource) {
          div = document.createElement("DIV");
          div.className = "item";
          div.dataset['value'] = "ds" + datasource.id;
          div.appendChild(document.createTextNode(datasource.name));
          dropdown_items.appendChild(div);
      });

      //set default value
      if (user.datasources.length == 0) {
          input.value = "";
      } else {
          $(input.parentElement)
            .dropdown({
              onChange: rules.GET_timerange
            })
            .dropdown("set selected", "ds"+user.ds)
          ;
      }
      input.parentElement.classList.remove("loading");
    },
    repopulate_templates_list: function () {
      let input = document.getElementById("newRuleTemplate");
      let dropdown_items = document.getElementById("newRuleTemplateList");
      dropdown_items.innerHTML = "";

      //set options
      let div;
      rules.templates.forEach(function (defn) {
          div = document.createElement("DIV");
          div.className = "item";
          div.dataset['value'] = defn
          let nicename = defn;
          if (nicename.substr(0,7) === "plugin:") {
            nicename = substr(7);
          }
          if (nicename.substr(-4).toLocaleLowerCase() === ".yml"){
            nicename = nicename.slice(0, -4);
          }
          div.appendChild(document.createTextNode(nicename));
          dropdown_items.appendChild(div);
      });

      //set default value
      if (user.datasources.length == 0) {
          input.value = "";
      } else {
          $(input.parentElement).dropdown("set selected", "ds"+user.ds);
      }
      input.parentElement.classList.remove("loading");
    },
    populate_edit_modal: function (rule_data) {
      console.log("filling modal with data:");
      console.log(rule_data);

      // populate meta data
      let active = document.getElementById("er_active");
      let name = document.getElementById("er_name");
      let desc = document.getElementById("er_desc");
      let rid = document.getElementById("er_rule_id");
      if (rule_data.active) {
        $(active.parentElement).checkbox("set checked");
      } else {
        $(active.parentElement).checkbox("set unchecked");
      }
      name.value = rule_data.name;
      desc.value = rule_data.desc;
      rid.value = rule_data.id;

      // populate alert data
      active = document.getElementById("er_alert");
      let severity = document.getElementById("er_alert_sev");
      let label = document.getElementById("er_alert_label");
      if (rule_data.actions.alert_active.toLocaleLowerCase() === "true") {
        $(active.parentElement).checkbox("set checked");
      } else {
        $(active.parentElement).checkbox("set unchecked");
      }
      severity.value = rule_data.actions.alert_severity;
      label.value = rule_data.actions.alert_label;

      // populate email data
      active = document.getElementById("er_email");
      let address = document.getElementById("er_email_address");
      let subject = document.getElementById("er_email_subject");
      console.log("rule_data.actions is", rule_data.actions);
      console.log("rule_data.actions.email_active is", rule_data.actions.email_active);
      if (rule_data.actions.email_active.toLocaleLowerCase() === "true") {
        $(active.parentElement).checkbox("set checked");
      } else {
        $(active.parentElement).checkbox("set unchecked");
      }
      address.value = rule_data.actions.email_address;
      subject.value = rule_data.actions.email_subject;

      // populate sms data
      active = document.getElementById("er_sms");
      let number = document.getElementById("er_sms_number");
      let message = document.getElementById("er_sms_message");
      if (rule_data.actions.sms_active.toLocaleLowerCase() === "true") {
        $(active.parentElement).checkbox("set checked");
      } else {
        $(active.parentElement).checkbox("set unchecked");
      }
      number.value = rule_data.actions.sms_number;
      message.value = rule_data.actions.sms_message;

      // populate exposed data values
      let parambox = document.getElementById("er_params");
      parambox.innerHTML = "";
      Object.keys(rule_data.exposed).forEach(function (key) {
        let param = rule_data.exposed[key];
        if (param.format === "text") {
          rules.edit_add_text_param(parambox, key, param);
        } else if (param.format === "checkbox") {
          rules.edit_add_checkbox_param(parambox, key, param);
        } else if (param.format === "dropdown") {
          rules.edit_add_dropdown_param(parambox, key, param);
        }
      });
      if (Object.keys(rule_data.exposed).length == 0) {
        let p = document.createElement("P");
        p.innerText = "No parameters available to adjust.";
        parambox.appendChild(p);
      }
    },

    new_rule: function () {  
      if (rules.templates === null) {
        rules.GET_templates(rules.repopulate_templates_list);
      }
      $(document.getElementById("newRuleModal"))
        .modal({
          onApprove: function() {
            let name = document.getElementById("newRuleName").value;
            let desc = document.getElementById("newRuleDesc").value;
            let template = document.getElementById("newRuleTemplate").value;
            rules.POST_new_rule(name, desc, template);
          }
        })
        .modal('show')
      ;
    },
    edit_rule: function(e) {
      let button = e.target;
      if (button.tagName == "I") {
        button = button.parentElement;
      }
      let rule_id = button.dataset['rule_id'];
      rules.GET_edit_rule(rule_id);
      let modal = document.getElementById("er_modal");
      $(modal)
        .modal({
          onApprove: rules.submit_edits,
        })
        .modal('show')
      ;
    },
    submit_edits: function() {
      let rule_id = document.getElementById("er_rule_id").value;
      let edits = {
        active: document.getElementById("er_active").parentElement.classList.contains("checked"),
        name: document.getElementById("er_name").value,
        desc: document.getElementById("er_desc").value,
        actions: {
          alert_active: document.getElementById("er_alert").parentElement.classList.contains("checked"),
          alert_severity: document.getElementById("er_alert_sev").value,
          alert_label: document.getElementById("er_alert_label").value,
          email_active: document.getElementById("er_email").parentElement.classList.contains("checked"),
          email_address: document.getElementById("er_email_address").value,
          email_subject: document.getElementById("er_email_subject").value,
          sms_active: document.getElementById("er_sms").parentElement.classList.contains("checked"),
          sms_number: document.getElementById("er_sms_number").value,
          sms_message: document.getElementById("er_sms_message").value,
        },
        exposed: {}
      };
      let params = document.getElementById("er_params");
      let inputs = params.getElementsByTagName("INPUT");
      let i = inputs.length - 1;
      for(; i >= 0; i = i - 1) {
        let inp = inputs[i];
        if (inp.type == "checkbox") {
          edits.exposed[inp.name] = inp.parentElement.classList.contains("checked");
        } else {
          edits.exposed[inp.name] = inp.value;
        }
      }
      //console.table(results);
      rules.POST_edit_rule(rule_id, edits);
    },
    delete_rule: function(e) {
      let button = e.target;
      if (button.tagName == "I") {
        button = button.parentElement;
      }
      let rule_id = button.dataset['rule_id'];
      rules.POST_delete_rule(rule_id);
    },
    rule_checkbox: function() {
      let rule_id = this.dataset['rule'];
      let state = this.parentElement.classList.contains("checked");
      rules.POST_edit_rule(rule_id, {'active': state});
    },

    reapply: function() {
      $(document.getElementById("reapplyRulesModal"))
        .modal({
          onApprove: function() {
            //extract choices made:
            let ds = document.getElementById("rules_ds_input").value;
            let slider = document.getElementById("slider-date");
            let range = slider.noUiSlider.get();
            rules.POST_reapply_rule(ds, Math.floor(range[0]), Math.floor(range[1]))
          },
        })
        .modal('show')
      ;
    },
  }
  // Export ports instance to global scope
  window.rules = rules;
}());

//alerts object
(function () {
  "use strict";
  let alerts = {
    endpoint: "./sec_alerts",
    endpoint_details: "./sec_alerts/details",

    init: function () {
      $('#Alerts .ui.filtering.dropdown')
        .dropdown({
          action: 'activate',
          onChange: alerts.GET_alerts,
        })
      ;

      // refresh button
      document.getElementById("alert_refresh").onclick = alerts.GET_alerts;

      // host filter validator
      document.getElementById("alert_host_filter").onchange = alerts.subnet_validator;

      // timerange filter validator
      document.getElementById("alert_time_filter").onchange = alerts.timerange_validator;

      // delete all button
      document.getElementById("alert_del_all").onclick = alerts.confirm_del_all;

      // delete button
      document.getElementById("alert_del").onclick = alerts.confirm_del;

      // column sorting button
      $("#alert_headers th").click(alerts.column_clicked);

      //pagination buttons
      document.getElementById("alert_prev_page").onclick = alerts.prev_page;
      document.getElementById("alert_next_page").onclick = alerts.next_page;

      //populate table!
      alerts.GET_alerts(document.getElementById("alert_page_num").innerText);
    },

    subnet_validator: function () {
      let alert = document.getElementById("alert_host_filter");
      let new_str = normalizeIP(alert.value);
      alert.value = new_str;
      alerts.GET_alerts(document.getElementById("alert_page_num").innerText);
    },

    timerange_validator: function () {
      let timerange = document.getElementById("alert_time_filter");
      let str = timerange.value;
      let old_string = timerange.dataset['old'];
      let new_string = old_string;
      let new_value = {y: 0, w: 0, d: 0, h: 0, m: 0, s: 0}
      const regex = /(\d+)\s?([ywdhms])/gi;
      let m;
      while ((m = regex.exec(str)) !== null) {
        // This is necessary to avoid infinite loops with zero-width matches
        if (m.index === regex.lastIndex) {
            regex.lastIndex++;
        }

        new_value[m[2]] = Number(m[1]);
      }
      if (Object.values(new_value).reduce(function(a,b){return a+b;}, 0) !== 0) {
        new_string = "";
        if (new_value.y) new_string += new_value.y + " years ";
        if (new_value.w) new_string += new_value.w + " weeks ";
        if (new_value.d) new_string += new_value.d + " days ";
        if (new_value.h) new_string += new_value.h + " hours ";
        if (new_value.m) new_string += new_value.m + " minutes ";
        if (new_value.s) new_string += new_value.s + " seconds ";
      }
      timerange.value = new_string;
      timerange.dataset['old'] = new_string;
      alerts.GET_alerts(document.getElementById("alert_page_num").innerText);
    },

    select_alert: function (e) {
      let alert = $(this);
      if (e.ctrlKey) {
        alert
          .toggleClass('active')
        ;
      } else {
        alert
          .addClass('active')
          .siblings()
          .removeClass('active')
        ;
      }
      deselectText();
      let alert_id = parseInt(alert[0].children[0].innerText);
      alerts.GET_details(alert_id);
    },

    deselect_alert: function () {
      // clear the meta details
      alerts.clear_details_meta();
      // clear all values
      document.getElementById("alert_details_name").innerText = "No alert selected.";
      document.getElementById("alert_details_id").innerText = "";
      document.getElementById("alert_details_time").innerText = "";
      document.getElementById("alert_details_host").innerText = "";
      document.getElementById("alert_details_severity").innerText = "";
      document.getElementById("alert_details_desc").innerText = "";
      document.getElementById("alert_del").classList.add("disabled");
    },

    column_clicked: function (column) {
      let heading = $(this);
      if (heading.hasClass("descending")) {
        heading
          .removeClass("descending")
          .addClass("ascending")
        ;
      } else {
        heading
          .removeClass("ascending")
          .addClass("descending")
        ;
      }
      heading
        .addClass('sorted')
        .siblings()
        .removeClass('sorted')
      ;
      deselectText();
      alerts.GET_alerts(document.getElementById("alert_page_num").innerText);
    },

    build_alert_request: function () {
      let host_input = document.getElementById("alert_host_filter");
      let severe_input = document.getElementById("alert_min_severity");
      let time_input = document.getElementById("alert_time_filter");
      let headings = document.getElementById("alert_headers").getElementsByClassName("sorted");

      let request = {
        severity: severe_input.value.substr(3),
        subnet: host_input.value,
        time: time_input.value
      };
      if (headings.length > 0) {
        request.sort = headings[0].dataset['value'];
        request.sort_dir = headings[0].classList.contains("ascending") ? "ASC" : "DESC";
      }

      return request;
    },

    confirm_del_all: function () {
      getConfirmation("Are you sure you want to delete all alerts?", alerts.POST_delete_all);
    },

    confirm_del: function () {
      getConfirmation("Are you sure you want to delete this alert?", function () {
        var id = document.getElementById("alert_details_id").innerText;
        alerts.POST_delete(id);
      });
    },

    GET_alerts_success: function (response, callback) {
    },

    GET_alerts: function (page, callback) {
      let requestData = alerts.build_alert_request();
      requestData.page_num = (typeof(page) == "number" ? page : 1);
      requestData.type = "alerts";
      $.ajax({
        url: alerts.endpoint,
        type: "GET",
        data: requestData,
        dataType: "json",
        error: generic_ajax_failure,
        success: function (response) {
          alerts.clear_alerts();
          console.log(response);
          response.alerts.forEach(function (alert) {
            alerts.add_alert([
              alert.id,
              alert.host,
              alert.report_time,
              alert.severity,
              alert.label,
              alert.rule_name
            ]);
          })
          
          let prev_page = document.getElementById("alert_prev_page");
          let next_page = document.getElementById("alert_next_page");
          let span_page = document.getElementById("alert_page_num");
          let span_pages = document.getElementById("alert_page_count");
          
          if (response.alerts.length == 0) {
            alerts.add_alert(["0 Alerts to Display."]);
          } else {
            span_page.innerText = response.page;
            span_pages.innerText = response.pages;
            if (response.page == 1) {
              prev_page.classList.add("disabled");
            } else {
              prev_page.classList.remove("disabled");
            }
            if (response.page < response.pages) {
              next_page.classList.remove("disabled");
            } else {
              next_page.classList.add("disabled");
            }
          }
          alerts.deselect_alert();
          if (typeof(callback) === "function") {
            callback(alerts);
          }
        }
      });
    },

    GET_details: function (alert_id, callbacks) {
      let loader = document.getElementById("alert_details_loader");
      loader.classList.add("active");
      let requestData = {
        "type": "details",
        "id": alert_id
      };
      $.ajax({
        url: alerts.endpoint_details,
        type: "GET",
        data: requestData,
        dataType: "json",
        error: generic_ajax_failure,
        success: function (details) {
          alerts.update_details(details);

          loader.classList.remove("active");
          document.getElementById("alert_del").classList.remove("disabled")
          if (typeof(callback) === "function") {
            callback(details);
          }
        }
      });
    },

    POST_status: function (alert_id, status) {
      let requestData = {
        "method": "update_status",
        "id": alert_id,
        "status": status,
      };
      $.ajax({
        url: alerts.endpoint,
        type: "POST",
        data: requestData,
        dataType: "json",
        error: generic_ajax_failure,
        success: generic_ajax_success
      });
    },

    POST_delete_all: function () {
      let requestData = {
        "method": "delete_all"
      };
      $.ajax({
        url: alerts.endpoint,
        type: "POST",
        data: requestData,
        dataType: "json",
        error: generic_ajax_failure,
        success: alerts.GET_alerts
      });
    },

    POST_delete: function (alert_id) {
      let requestData = {
        "method": "delete",
        "id": alert_id,
      };
      $.ajax({
        url: alerts.endpoint,
        type: "POST",
        data: requestData,
        dataType: "json",
        error: generic_ajax_failure,
        success: alerts.GET_alerts
      });
    },

    prev_page: function () {
      alerts.GET_alerts(parseInt(document.getElementById("alert_page_num").innerText) - 1);
    },
    next_page: function () {
      alerts.GET_alerts(parseInt(document.getElementById("alert_page_num").innerText) + 1);
    },
    clear_alerts: function () {
      let alert_window = document.getElementById("alert_table_body")
      alert_window.innerHTML = "";
    },
    add_alert: function (columns) {
      let alert_window = document.getElementById("alert_table_body")
      let tr = document.createElement("TR");
      if (columns.length == 1) {
        let td = document.createElement("TD");
        td.innerText = columns[0];
        td.colSpan = "6";
        tr.appendChild(td);
      } else {
        columns.forEach(function (column) {
          let td = document.createElement("TD");
          if (!column) {
            column = "unknown";
          }

          if (column.length === 4 && column.substring(0, 3) === "sev") {
            let icon = document.createElement("I");
            icon.className = "circle icon severe" + column.substr(3);
            td.appendChild(icon);
            td.appendChild(document.createTextNode(column.substr(3)));
          } else {
            td.innerText = column;
          }
          tr.onclick = alerts.select_alert;
          tr.appendChild(td);
        });
      }
      alert_window.appendChild(tr);
    },
    clear_details_meta: function () {
      let details_window = document.getElementById("alert_details_details")
      details_window.innerHTML = "";
    },
    add_details_meta: function (key, value) {
      let details_window = document.getElementById("alert_details_details")
      let tr = document.createElement("TR");

      let td = document.createElement("TD");
      td.innerText = key;
      tr.appendChild(td);

      td = document.createElement("TD");
      td.innerText = value;
      tr.appendChild(td);

      details_window.appendChild(tr);
    },
    update_details: function (details) {
      /*
      'for', 'rule_name', 'time', 'host', 'severity', 'status', 'description', 'details'
      */
      document.getElementById("alert_details_name").innerText = details.label;
      document.getElementById("alert_details_id").innerText = details["for"];
      document.getElementById("alert_details_time").innerText = details.time;
      document.getElementById("alert_details_host").innerText = details.host;
      document.getElementById("alert_details_severity").innerText = details.severity;
      document.getElementById("alert_details_desc").innerText = details.description;

      alerts.clear_details_meta();
      Object.keys(details.details).forEach(function (key) {
        let value = details.details[key];
        alerts.add_details_meta(key, value);
      });
    },
  }
  window.alerts = alerts;
}());

function init() {
  "use strict";
  alerts.init();
  rules.init();

  $('.ui.sticky')
    .sticky({
      context: '#stickyrailcontext'
    })
  ;

  user.GET_settings();
}