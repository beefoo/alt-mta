'use strict';

var AppLines = (function() {

  function AppLines(config) {
    var defaults = {
      routeData: "/preprocess_mta/output/routes.json",
      urouteData: "/preprocess_mta/usergen/routes.json"
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  AppLines.prototype.init = function(){
    var _this = this;
    var opt = this.opt;

    this.$map = $('#map');
    this.$overlay = $('#overlay');
    this.$symbols = $('#symbols');
    this.$lines = $('#lines');
    this.$select = $('#select-line');
    this.$opacitySelect = $('#map-opacity');
    this.$toggleMap = $('#toggle-map');
    this.$draggable = $('#draggable');
    this.$dragWindow = $('#drag-window');

    this.saveDataQueue = [];

    $.when(
      $.getJSON(opt.routeData),
      $.getJSON(opt.urouteData)

    ).done(function(routes, uroutes){
      routes = routes[0];
      uroutes = uroutes[0];

      console.log(routes.length + " routes loaded.");
      console.log(_.keys(uroutes).length + " user-generated routes loaded.");

      _this.loadData(routes, uroutes);
      _this.loadView();
      _this.loadListeners();
      _this.onRouteChange(-1);
    });

  };

  AppLines.prototype.drag = function(x1, y1){
    var x0 = this.dragStartX;
    var y0 = this.dragStartY;
    var x = x0;
    var y = y0;
    var w = x1 - x0;
    var h = y1 - y0;

    if (w < 0) {
      x = x1;
      w = x0 - x1;
    }

    if (h < 0) {
      y = y1;
      h = y0 - y1;
    }

    this.$dragWindow.css({
      top: y + "px",
      left: x + "px",
      height: h + "px",
      width: w + "px"
    });
  };

  AppLines.prototype.dragEnd = function(){
    this.dragging = false;
    this.$dragWindow.removeClass('active');
  };

  AppLines.prototype.dragStart = function(x, y){
    this.dragging = true;
    this.dragStartX = x;
    this.dragStartY = y;
    this.$dragWindow.css({
      top: y + "px",
      left: x + "px",
      height: "0px",
      width: "0px"
    });
    this.$dragWindow.addClass('active');
  };

  AppLines.prototype.drawLines = function(){
    var routes = this.routes;

    _.each(routes, function(route){
      var g = route.graphics;
      var lineWidth = 5;
      var color = parseInt("0x" + route.color.slice(1));
      // color = 0x000000;
      var alpha = 1.0;
      g.lineStyle(lineWidth, color, alpha);

      // get route's groups
      var groups = [route.stations];
      if (route.groups && route.groups.length > 1) {
        groups = route.groups
      }

      _.each(groups, function(group, i){
        _.each(group, function(station, j){
          var p = station.point;
          var s = station.size;
          var x = p[0] + s[0] * 0.5;
          var y = p[1] + s[1] * 0.5;
          if (j===0) {
            g.moveTo(x, y);
          } else {
            g.lineTo(x, y);
          }
        });
      });

    });
  };

  AppLines.prototype.loadData = function(routes, uroutes){
    // Combined routes and uroutes
    _.each(routes, function(route, i){
      var uroute = uroutes[route.id];
      if (uroute) {
        _.each(route.stations, function(station, j){
          var ustation = uroute.stations[station.id];
          if (ustation) {
            routes[i].stations[j] = _.extend({}, station, ustation);
          }
        });
      }
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
    this.routes = routes;
    // console.log(routes);
  };

  AppLines.prototype.loadListeners = function(){
    var _this = this;
    var $document = $(document);

    this.$select.on('change', function(e){
      _this.onRouteChange(parseInt($(this).val()));
    });

    this.$toggleMap.on('change', function(e){
      var checked = $(this).is(':checked');
      _this.toggleMap(checked);
    });

    $document.on('input', '#map-opacity', function() {
      _this.$overlay.css("opacity", 1-_this.$opacitySelect.val());
    });

    this.$draggable.on('mousedown', function(e){
      if (_this.currentRoute) {
        // console.log('down')
        _this.dragStart(e.pageX, e.pageY);
      }
    });

    this.$draggable.on('mousemove', function(e){
      if (_this.dragging && _this.currentRoute) {
        _this.drag(e.pageX, e.pageY);
      }
    });

    this.$draggable.on('mouseup', function(e){
      if (_this.currentRoute) {
        // console.log('up')
        _this.dragEnd();
      }
    });
  };

  AppLines.prototype.loadView = function(){
    var $map = this.$map;
    var width = $map.width();
    var height = $map.height();
    var routes = this.routes;
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
      var $symbol = $('<div class="symbol" data-id="'+station.id+'"></div>');
      $symbol.css({
        top: station.point[1],
        left: station.point[0],
        width: station.size[0],
        height: station.size[1]
      });
      $container.append($symbol);
    });
    this.$symbols.append($container);

    // init select route
    var $select = this.$select;
    _.each(routes, function(route, i){
      var $option = $('<option value="'+i+'">'+route.id+'</option>');
      $select.append($option);
    });

    // init lines
    var _this = this;
    var app = new PIXI.Application(width, height, {antialias: true, transparent: true});
    _.each(routes, function(route, i){
      var graphics = new PIXI.Graphics();
      graphics.visible = false;
      app.stage.addChild(graphics);
      routes[i].graphics = graphics;
    })
    this.$lines.append(app.view);
    this.drawLines();
  };

  AppLines.prototype.onRouteChange = function(index){
    if (index < 0) {
      _.each(this.routes, function(route){
        route.graphics.visible = true;
      });
      this.currentRouteIndex = index;
      this.currentRoute = false;
      $('.symbol').addClass('active');
      return false;
    }

    if (this.currentRoute) {
      this.currentRoute.graphics.visible = false;

    } else if (this.currentRouteIndex < 0) {
      _.each(this.routes, function(route){
        route.graphics.visible = false;
      });
    }

    this.currentRouteIndex = index;
    this.currentRoute = this.routes[index];
    this.currentRoute.graphics.visible = true;

    $('.symbol').removeClass('active');

    // select symbols for this route
    _.each(this.currentRoute.stations, function(s){
      $('.symbol[data-id="'+s.id+'"]').addClass('active');
    });
  };

  AppLines.prototype.toggleMap = function(on){
    if (on) {
      this.$overlay.css("opacity", 1-this.$opacitySelect.val());
    } else {
      this.$overlay.css("opacity", 1);
    }
  };

  return AppLines;

})();

$(function() {
  var app = new AppLines({});
});
