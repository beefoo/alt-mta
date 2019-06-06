'use strict';

var AppLines = (function() {

  var opt, routes, uroutes;
  var $map, $lines, $overlay, $symbols, $svg, $select;
  var $opacitySelect, $toggleMap, $toggleLines;

  function AppLines(config) {
    var defaults = {
      routeData: "/output/routes.json",
      urouteData: "/usergen/routes.json",
      lineWidth: 5,
      curviness: 0.3 // probably between 0.1 and 0.5
    };
    opt = _.extend({}, defaults, config);
    this.init();
  }

  function distance(p1, p2) {
    var deltaX = p2.x - p1.x;
    var deltaY = p2.y - p1.y;
    return Math.hypot(deltaX, deltaY);
  }

  function getRouteGroups(route) {
    // get route's groups
    var groups = [route.stations];
    if (route.groups && route.groups.length > 1) {
      groups = route.groups
    }
    return groups;
  }

  function radiansBetweenPoints(p1, p2) {
    var deltaX = p2.x - p1.x;
    var deltaY = p2.y - p1.y;
    return Math.atan2(deltaY, deltaX);
  }

  function translatePoint(p, radians, distance) {
    var x2 = p.x + distance * Math.cos(radians);
    var y2 = p.y + distance * Math.sin(radians);
    return {
      x: x2,
      y: y2
    };
  }

  function routesToHTML(){
    var html = '';
    _.each(routes, function(route, i){
      html += '<g class="route active" id="route-'+route.id+'" stroke="'+route.color+'" stroke-width="'+opt.lineWidth+'" stroke-linecap="round" fill="none">';

      var groups = getRouteGroups(route);

      _.each(groups, function(group, i){
        var id = "route-group-" + route.id + (i+1);
        html += stationsToHTML(group, id);
      });

      html += '</g>';
    });
    return html;
  };

  function stationPosition(station) {
    var p = station.point;
    var s = station.size;
    var x = p[0] + s[0] * 0.5;
    var y = p[1] + s[1] * 0.5;
    return {
      x: x,
      y: y
    }
  }

  function stationsToHTML(stations, id) {
    var d = "";
    var count = stations.length;
    _.each(stations, function(station, i){
      var p = stationPosition(station);
      if (i<=0) {
        d += "M"+p.x+" "+p.y;
      } else {
        var s0 = stations[i-1]; // prev
        var cp0 = s0.cp[1];
        var cp2 = station.cp[0];
        if (!cp0 || !cp2) {
          console.log("No control point for station " + station.label);
          console.log(cp0, cp2)
          return;
        }
        // use shorthand if possible
        if (i > 1) d += " S"+cp2.x+","+cp2.y+" "+p.x+","+p.y;
        else d += " C"+cp0.x+","+cp0.y+" "+cp2.x+","+cp2.y+" "+p.x+","+p.y;
      }
    });
    return '<path id="'+id+'" d="'+d+'" />';
  }

  AppLines.prototype.init = function(){
    var _this = this;

    $map = $('#map');
    $overlay = $('#overlay');
    $symbols = $('#symbols');
    $lines = $("#lines");
    $svg = $('#svg');
    $select = $('#select-line');
    $opacitySelect = $('#map-opacity');
    $toggleMap = $('#toggle-map');
    $toggleLines = $('#toggle-lines');

    $.when(
      $.getJSON(opt.routeData),
      $.getJSON(opt.urouteData)

    ).done(function(_routes, _uroutes){
      routes = _routes[0];
      uroutes = _uroutes[0];

      console.log(routes.length + " routes loaded.");
      console.log(_.keys(uroutes).length + " user-generated routes loaded.");

      _this.parseData();
      _this.loadView();
      _this.loadListeners();
      _this.onRouteChange(-1);
    });

  };

  AppLines.prototype.loadListeners = function(){
    var _this = this;
    var $document = $(document);

    $select.on('change', function(e){
      _this.onRouteChange(parseInt($(this).val()));
    });

    $toggleMap.on('change', function(e){
      var checked = $(this).is(':checked');
      _this.toggleMap(checked);
    });

    $toggleLines.on('change', function(e){
      var checked = $(this).is(':checked');
      _this.toggleLines(checked);
    });

    $document.on('input', '#map-opacity', function() {
      $overlay.css("opacity", 1-$opacitySelect.val());
    });

    $document.on('click', '.symbol', function(e) {
      e.preventDefault();
      _this.onSymbolClick($(this));
    });
  };

  AppLines.prototype.loadView = function(){
    var width = $map.width();
    var height = $map.height();
    var $container = $('<div />');

    // get unique station symbols
    var stations = _.pluck(routes, "stations");
    stations = _.flatten(stations, true);
    stations = _.filter(stations, function(station){ return station.point && station.size; });
    // stations = _.map(stations, function(station){
    //   station.point_id = station.point[0] + "_" + station.point[1];
    //   return station;
    // });
    stations = _.uniq(stations, function(station) { return station.id; });

    // draw symbols
    _.each(stations, function(station){
      var $symbol = $('<a href="#" class="symbol" data-id="'+station.id+'" data-index="'+station.index+'" data-rindex="'+station.routeIndex+'"></a>');
      $symbol.css({
        top: station.point[1],
        left: station.point[0],
        width: station.size[0],
        height: station.size[1]
      });
      $container.append($symbol);
    });
    $symbols.append($container);

    // init select route
    _.each(routes, function(route, i){
      var $option = $('<option value="'+i+'">'+route.id+'</option>');
      $select.append($option);
    });

    // init lines
    $svg.attr('width', width);
    $svg.attr('height', height);
    $svg.html(routesToHTML());

    _.each(routes, function(route, i){
      routes[i].$group = $('#route-'+route.id);
    });
  };

  AppLines.prototype.onRouteChange = function(index){
    if (index < 0) {
      $(".route").addClass("active");
      $('.symbol').addClass('active');
      return false;
    }

    var currentRoute = routes[index];
    $('.symbol').removeClass('active');
    $('.route').removeClass('active');

    currentRoute.$group.addClass('active');

    // select symbols for this route
    _.each(currentRoute.stations, function(s){
      $('.symbol[data-id="'+s.id+'"]').addClass('active');
    });
  };

  AppLines.prototype.onSymbolClick = function($el){
    var id = $el.attr("data-id");
    var stationIndex = parseInt($el.attr("data-index"));
    var routeIndex = parseInt($el.attr("data-rindex"));
    var station = routes[routeIndex].stations[stationIndex];

    this.showForm(station);
  };

  AppLines.prototype.parseData = function(){
    // Combined routes and uroutes
    _.each(routes, function(route, i){
      var uroute = uroutes[route.id];
      // add values to stations
      _.each(route.stations, function(station, j){
        routes[i].stations[j].index = j;
        routes[i].stations[j].routeIndex = i;
        // add user generated data
        if (uroute) {
          var ustation = uroute.stations[station.id];
          if (ustation) {
            routes[i].stations[j] = _.extend({}, station, ustation);
          }
        }
      });
      // put stations into groups if necessary
      if (route.groups && route.groups.length > 0) {
        var routeGroups = [];
        var stations = routes[i].stations;
        _.each(route.groups, function(group){
          var gstations = _.filter(stations, function(station){
            return station.groups && _.indexOf(station.groups, group) >= 0;
          });
          routeGroups.push(gstations);
        });
        routes[i].groups = routeGroups;
      }
    });

    // generate control points if they don't exist
    var autoControlPoints = {};
    _.each(routes, function(route, i){
      var groups = getRouteGroups(route);
      _.each(groups, function(stations, j){
        var stationCount = stations.length;
        _.each(stations, function(station, k){
          if (station.cp && station.cp.length) return;
          var p = stationPosition(station);
          // skip if control point already defined
          var p0 = false, p2 = false, cp0 = false, cp2 = false; // each point will have two control points, except for the beginning and end
          if (k > 0) p0 = stationPosition(stations[k-1]);
          if (k < stationCount-1) p2 = stationPosition(stations[k+1]);

          var radians = 0, pd = 0;
          if (p0 && p2) {
            radians = radiansBetweenPoints(p2, p0);
            pd = Math.min(distance(p2, p0), distance(p, p0), distance(p2, p)) * opt.curviness;
            cp0 = translatePoint(p, radians, pd);
            cp2 = translatePoint(p, radians, -pd);
          } else if (p2) {
            radians = radiansBetweenPoints(p2, p) ; // first point
            pd = distance(p2, p) * opt.curviness;
            cp2 = translatePoint(p, radians, -pd);
          } else if (p0) {
            radians = radiansBetweenPoints(p, p0) ; // last point
            pd = distance(p, p0) * opt.curviness;
            cp0 = translatePoint(p, radians, pd);
          }
          if (autoControlPoints[station.id]===undefined || !autoControlPoints[station.id][0] || !autoControlPoints[station.id][1]) {
            autoControlPoints[station.id] = [cp0, cp2];
          }
        });
      });
    });

    // add control points to stations
    _.each(routes, function(route, i){
      // get route's groups
      if (route.groups && route.groups.length > 1) {
        _.each(route.groups, function(stations, j) {
          _.each(stations, function(station, k) {
            if (station.cp && station.cp.length) return;
            routes[i].groups[j][k].cp = autoControlPoints[station.id];
          });
        });
      } else {
        _.each(route.stations, function(station, k) {
          if (station.cp && station.cp.length) return;
          routes[i].stations[k].cp = autoControlPoints[station.id];
        });
      }
    });
  };

  AppLines.prototype.showForm = function(station){
    $("#station-index").text(station.id);
    $('#station-name').val(station.label);
    $('#station-pos-x').val(station.point[0]);
    $('#station-pos-y').val(station.point[1]);
  };

  AppLines.prototype.toggleLines = function(on){
    if (on) {
      $lines.css("opacity", 1);
    } else {
      $lines.css("opacity", 0);
    }
  };

  AppLines.prototype.toggleMap = function(on){
    if (on) {
      $overlay.css("opacity", 1-$opacitySelect.val());
    } else {
      $overlay.css("opacity", 1);
    }
  };

  return AppLines;

})();

$(function() {
  var app = new AppLines({});
});
