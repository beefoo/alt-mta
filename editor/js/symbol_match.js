'use strict';

var AppSymbolMatch = (function() {

  function AppSymbolMatch(config) {
    var defaults = {
      routeData: "/preprocess_mta/output/routes.json",
      symbolData: "/preprocess_mta/output/symbols.json",
      saveData: "/preprocess_mta/usergen/routes.json"
    };
    this.opt = _.extend({}, defaults, config);
    this.init();
  }

  AppSymbolMatch.prototype.init = function(){
    var _this = this;
    var opt = this.opt;

    this.$symbols = $('#symbols');
    this.$select = $('#select-line');
    this.$station = $('#station');
    this.saveDataQueue = [];

    $.when(
      $.getJSON(opt.routeData),
      $.getJSON(opt.symbolData),
      $.getJSON(opt.saveData)

    ).done(function(routes, symbols, uroutes){
      routes = routes[0];
      symbols = symbols[0];
      uroutes = uroutes[0];

      console.log(routes.length + " routes loaded.");
      console.log(symbols.length + " symbols loaded.");
      console.log(_.keys(uroutes).length + " user-generated routes loaded.");

      _this.symbols = symbols;
      _this.routes = routes;
      _this.uroutes = uroutes;

      _this.loadData(routes, uroutes);
      _this.loadView(symbols, routes);
      _this.loadListeners();
      _this.onRouteChange(0);
    });

  };

  AppSymbolMatch.prototype.loadData = function(routes, uroutes){
    // Initialize uroutes
    _.each(routes, function(route){
      var uroute = uroutes[route.id];

      // route found, make sure stations exist
      if (uroute) {
        _.each(route.stations, function(station){
          var ustation = uroute.stations[station.id];
          if (!ustation) {
            uroute.stations[station.id] = {};
          }
        });

      // route not found, add empty route and stations
      } else {
        uroutes[route.id] = {
          stations: _.object(_.map(route.stations, function(s){ return [s.id, {}]; }))
        }
      }
    });
  };

  AppSymbolMatch.prototype.loadListeners = function(){
    var _this = this;

    this.$symbols.on('click', '.symbol', function(e){
      _this.onClickSymbol($(this));
    });

    this.$select.on('change', function(e){
      _this.onRouteChange(parseInt($(this).val()));
    });
  };

  AppSymbolMatch.prototype.loadView = function(symbols, routes){
    var $container = $('<div />');

    _.each(symbols, function(symbol, i){
      var $symbol = $('<div class="symbol" data-index="'+i+'"></div>');
      $symbol.css({
        top: symbol.point[1],
        left: symbol.point[0],
        width: symbol.size[0],
        height: symbol.size[1]
      });
      $container.append($symbol);
      symbols[i].$el = $symbol;
    });
    this.$symbols.append($container);

    var $select = this.$select;
    _.each(routes, function(route, i){
      var selected = i === 0 ? ' selected' : '';
      var $option = $('<option value="'+i+'"'+selected+'>'+route.id+'</option>');
      $select.append($option);
    });
  };

  AppSymbolMatch.prototype.onClickSymbol = function($symbol){
    var index = parseInt($symbol.attr('data-index'));
    var selected = $symbol.hasClass('selected');

    $symbol.toggleClass('selected');

    if (!selected) {
      this.symbolAttach(this.symbols[index]);
    } else {
      this.symbolDetach(this.symbols[index]);
    }

    this.saveData();
  };

  AppSymbolMatch.prototype.onRouteChange = function(index){
    this.currentRouteIndex = index;
    this.currentRoute = this.routes[index];
    this.currentURoute = this.uroutes[this.currentRoute.id];

    // console.log(this.currentURoute)
    $('.symbol').removeClass('selected');

    // select symbols for this route
    var symbols = this.symbols;
    var ustations = _.pick(this.currentURoute.stations, function(s, key) { return s.point && s.size; });
    _.each(ustations, function(s, key){
      var symbol = _.find(symbols, function(sb){ return sb.point[0]===s.point[0] && sb.point[1]===s.point[1]; });
      if (symbol) {
        symbol.$el.addClass('selected');
      }
    });

    this.showNextStation();
  };

  AppSymbolMatch.prototype.saveData = function(){
    var filename = this.opt.saveData;
    var data = JSON.parse(JSON.stringify(this.uroutes));

    this.saveDataQueue.push({
      filename: filename,
      data: data
    });

    this.saveQueue();
  };

  AppSymbolMatch.prototype.saveQueue = function(){
    if (this.isSaving || !this.saveDataQueue.length) return false;
    var _this = this;

    this.isSaving = true;
    var nextData = this.saveDataQueue.shift();

    $.ajax({
      type: 'POST',
      url: '/symbol_match/save',
      data: JSON.stringify(nextData),
      contentType: 'application/json',
      complete: function(jqXHR, textStatus){
        _this.isSaving = false;
        _this.saveQueue();
      },
      success: function(){ console.log('Data saved'); },
      error: function(){ console.log('Error with saving data'); }
    });
  };

  AppSymbolMatch.prototype.showNextStation = function(){
    this.$station.text("--");
    var key = _.findKey(this.currentURoute.stations, function(s){ return !s.point || !s.size; });
    var currentUStation = key ? this.currentURoute.stations[key] : false;
    this.currentUStation = currentUStation;

    if (currentUStation) {
      this.showStation(key);
    } else {
      this.$station.text("[route is complete]");
    }
  };

  AppSymbolMatch.prototype.showStation = function(ustationKey){
    var station = _.find(this.currentRoute.stations, function(s){ return s.id===ustationKey; });
    this.currentStation = station;

    if (!station) {
      console.log("Could not find "+ustationKey);
      return false;
    }

    this.$station.text(station.label);
  };

  AppSymbolMatch.prototype.symbolAttach = function(symbol){
    if (!this.currentStation || !symbol) return false;

    // set the symbol's position and size to current station
    this.currentUStation.point = _.clone(symbol.point);
    this.currentUStation.size = _.clone(symbol.size);
    // console.log(this.currentUStation);

    // find stations in other routes of same color that do not have  position/size defined
    var rcolor = this.currentRoute.color;
    var rid = this.currentRoute.id;
    var sid = this.currentStation.id;
    var uroutes = this.uroutes;
    var otherRoutes = _.filter(this.routes, function(r){ return r.color===rcolor && r.id !== rid; });
    _.each(otherRoutes, function(r){
      var uroute = uroutes[r.id];
      if (uroute) {
        _.each(uroute.stations, function(s, key){
          if (!s.point && key===sid) {
            uroute.stations[key].point = _.clone(symbol.point);
            uroute.stations[key].size = _.clone(symbol.size);
          }
        });
      }
    });
    // console.log(this.uroutes);

    this.showNextStation();
  };

  AppSymbolMatch.prototype.symbolDetach = function(symbol){
    if (!symbol) return false;
    var _this = this;

    _.each(this.currentURoute.stations, function(station, key){
      if (station.point && station.point[0]===symbol.point[0] && station.point[1]===symbol.point[1]) {
        _this.currentURoute.stations[key] = _.omit(station, ['point', 'size']);
      }
    });

    this.showNextStation();
  };

  return AppSymbolMatch;

})();

$(function() {
  var app = new AppSymbolMatch({});
});
