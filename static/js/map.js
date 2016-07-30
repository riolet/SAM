"use strict";

var canvas;
var ctx;
var rect; //render region on screen

//global transform coordinates, with initial values
var tx = 0;
var ty = 0;
var scale = 0.0007;

//mouse interaction variables
var ismdown = false;
var mdownx;
var mdowny;
var mx;
var my;

//store the data displayed in the map
var nodeCollection = {};
var renderCollection = [];
var selection = null;
var currentSubnet = "";

//settings/options data
var filter = "";
var config = {
    "show_clients": true,
    "show_servers": true,
    "show_in": true,
    "show_out": false
};

//Constants.  Used for zoom levels in map::currentLevel and map_render::opacity
var zNodes16 = 0.00231;
var zLinks16 = 0.0111;
var zNodes24 = 0.0555;
var zLinks24 = 0.267;
var zNodes32 = 1.333;
var zLinks32 = 6.667;


function init() {
    canvas = document.getElementById("canvas");
    var navBarHeight = $("#navbar").height();
    $("#output").css("top", navBarHeight);
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight - navBarHeight;
    rect = canvas.getBoundingClientRect();
    tx = rect.width / 2;
    ty = rect.height / 2;
    ctx = canvas.getContext("2d");
    ctx.lineJoin = "bevel";

    //Event listeners for detecting clicks and zooms
    canvas.addEventListener("mousedown", mousedown);
    canvas.addEventListener("mousemove", mousemove);
    canvas.addEventListener("mouseup", mouseup);
    canvas.addEventListener("keydown", mouseup);
    canvas.addEventListener("wheel", wheel);
    window.addEventListener("keydown", keydown, false);

    var filterElement = document.getElementById("filter");
    filterElement.oninput = onfilter;
    filter = filterElement.value;

    var searchElement = document.getElementById("search");
    searchElement.value = "";
    searchElement.oninput = onsearch;

    updateFloatingPanel();

    document.getElementById("show_clients").checked = config.show_clients;
    document.getElementById("show_servers").checked = config.show_servers;
    document.getElementById("show_in").checked = config.show_in;
    document.getElementById("show_out").checked = config.show_out;

    $(".ui.accordion").accordion();
    $(".ui.dropdown").dropdown({
        action: updateConfig
    });
    $(".input.icon").popup();
    $("table.sortable").tablesort();

    loadData();
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

function findNode(ip8, ip16, ip24, ip32) {
    if (ip8 === undefined) {
        ip8 = -1;
    }
    if (ip16 === undefined) {
        ip16 = -1;
    }
    if (ip24 === undefined) {
        ip24 = -1;
    }
    if (ip32 === undefined) {
        ip32 = -1;
    }

    if (ip8 in nodeCollection) {
        if (ip16 in nodeCollection[ip8].children) {
            if (ip24 in nodeCollection[ip8].children[ip16].children) {
                if (ip32 in nodeCollection[ip8].children[ip16].children[ip24].children) {
                    return nodeCollection[ip8].children[ip16].children[ip24].children[ip32];
                } else {
                    return nodeCollection[ip8].children[ip16].children[ip24];
                }
            } else {
                return nodeCollection[ip8].children[ip16];
            }
        } else {
            return nodeCollection[ip8];
        }
    } else {
        return null;
    }
}