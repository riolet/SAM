var canvas;
var ctx;
var width;
var height;
var rect;
var navBarHeight;

var ismdown = false;
var mdownx, mdowny;
var mx, my;
var tx = 532;
var ty = 288;
var scale = 0.0007;

var map = {};

var nodeCollection = {};
var renderCollection = [];
var currentSubnet = "";
var selection = null;
var filter = "";
var config = {
    "show_clients": true,
    "show_servers": true,
    "show_in": true,
    "show_out": false};

//Constant.  Used for zoom levels in map::currentLevel and map_render::opacity
var zNodes16 = 0.00231;
var zLinks16 = 0.0111;
var zNodes24 = 0.0555;
var zLinks24 = 0.267;
var zNodes32 = 1.333;
var zLinks32 = 6.667;

function init() {
    canvas = document.getElementById("canvas");
    navBarHeight = $('#navbar').height();
    $('#output').css('top', navBarHeight);
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    rect = canvas.getBoundingClientRect();
    tx = rect.width / 2;
    ty = rect.height / 2;
    ctx = canvas.getContext("2d");
    ctx.lineJoin = "bevel";


    //Event listeners for detecting clicks and zooms
    canvas.addEventListener('mousedown', mousedown);
    canvas.addEventListener('mousemove', mousemove);
    canvas.addEventListener('mouseup', mouseup);
    canvas.addEventListener('keydown', mouseup);
    canvas.addEventListener('wheel', wheel);
    window.addEventListener('keydown',keydown,false);

    filterElement = document.getElementById("filter");
    filterElement.oninput = onfilter;
    filter = filterElement.value;

    filterElement = document.getElementById("search");
    filterElement.value = "";
    filterElement.oninput = onsearch;

    updateFloatingPanel();

    document.getElementById("show_clients").checked = config.show_clients;
    document.getElementById("show_servers").checked = config.show_servers;
    document.getElementById("show_in").checked = config.show_in;
    document.getElementById("show_out").checked = config.show_out;

    $('.ui.accordion').accordion();
    $('.ui.dropdown')
    .dropdown({
        //action: 'none'
        action: updateConfig
    });
    $('.input.icon').popup();
    $('table.sortable').tablesort();

    loadData();

    render(tx, ty, scale);
}

function currentLevel() {
    if (scale < zNodes16) {
        return 8;
    }
    if (scale < zNodes24) {
        return 16;
    }
    if (scale < zNodes32) {
        return 24;
    }
    return 32;
}

function findNode(seg1=-1, seg2=-1, seg3=-1, seg4=-1) {
    if (seg1 in nodeCollection) {
        if (seg2 in nodeCollection[seg1].children) {
            if (seg3 in nodeCollection[seg1].children[seg2].children) {
                if (seg4 in nodeCollection[seg1].children[seg2].children[seg3].children) {
                    return nodeCollection[seg1].children[seg2].children[seg3].children[seg4];
                } else {
                    return nodeCollection[seg1].children[seg2].children[seg3];
                }
            } else {
                return nodeCollection[seg1].children[seg2];
            }
        } else {
            return nodeCollection[seg1];
        }
    } else {
        return null;
    }
}