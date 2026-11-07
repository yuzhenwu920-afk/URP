/***************************************************************
 * URP: China / Gansu -> real Sentinel-2 field-context image
 * Run in https://code.earthengine.google.com/
 *
 * Station: 37 deg 52 min N, 102 deg 52 min E; 1581 m.
 * Source: Wang (2023), thesis pp. 8-9.
 * The station reference is not a surveyed DI parcel boundary.
 * The right panel uses real 2021 Sentinel-2 SR imagery (10 m).
 * No schematic field, synthetic rows or assumed parcel are drawn.
 *
 * Uses public text module users/gena/packages:text.
 * All administrative geometry is rasterized before layout.
 * GeometryCollection coordinate extraction is not used.
 ***************************************************************/

var CFG = {
  stationLon: 102 + 52 / 60,
  stationLat: 37 + 52 / 60,
  startDate: '2021-06-15',
  endDate: '2021-09-01', // Exclusive end date.
  sceneCloudLimit: 50,
  viewWidthM: 3000,
  fieldBoundaryAsset: '', // Optional: verified polygon asset ID.
  widthPx: 3200,
  heightPx: 1700,
  driveFolder: 'URP_Figures',
  exportName: 'URP_China_Gansu_Real_Field_Image_EN',
  createInitialTiffTask: true
};

var TEXT = require('users/gena/packages:text');
var COL = {
  white: 'FFFFFF', panel: 'F7FAF9', border: 'D1DED8',
  dark: '193D36', muted: '5D736B', country: 'E4EEE9',
  province: 'ACBDB5', gansu: '78AE9C', gansuEdge: '376E5C',
  orange: 'D47B24'
};

var PAGE_PROJ = ee.Projection('EPSG:3857', [1, 0, 0, 0, -1, 0]);
var PAGE = ee.Geometry.Rectangle(
  [0, -CFG.heightPx, CFG.widthPx, 0], 'EPSG:3857', false
);
var MAPBOX = {x: 120, y: 420, w: 1270, h: 870};
var GEO = {west: 73, east: 136, south: 17, north: 55};
var SATBOX = {x: 1700, y: 475, w: 1380, h: 970};
var station = ee.Geometry.Point([CFG.stationLon, CFG.stationLat]);
var UTM = 'EPSG:32648';

function rgb(hex) {
  return [parseInt(hex.slice(0, 2), 16),
          parseInt(hex.slice(2, 4), 16),
          parseInt(hex.slice(4, 6), 16)];
}
function colour(hex) {
  return ee.Image.constant(rgb(hex)).toUint8()
    .rename(['R', 'G', 'B']).setDefaultProjection(PAGE_PROJ);
}
function pt(x, y) {
  return ee.Geometry.Point([x, -y], 'EPSG:3857');
}
function rect(x, y, w, h) {
  return ee.Geometry.Rectangle([x, -y-h, x+w, -y], 'EPSG:3857', false);
}
function line(points) {
  return ee.Geometry.LineString(points.map(function(p) {
    return [p[0], -p[1]];
  }), 'EPSG:3857', false);
}
function poly(points) {
  var ring = points.map(function(p) { return [p[0], -p[1]]; });
  ring.push(ring[0]);
  return ee.Geometry.Polygon([ring], 'EPSG:3857', false);
}
function fill(geom, hex) { return colour(hex).clip(geom); }
function stroke(geom, hex, width) {
  var mask = ee.Image.constant(0).toByte()
    .setDefaultProjection(PAGE_PROJ)
    .paint(ee.FeatureCollection([ee.Feature(geom)]), 1, width);
  return colour(hex).updateMask(mask);
}
function label(str, x, y, size, hex) {
  return TEXT.draw(str, pt(x, y).transform('EPSG:4326', 1), size / 32, {
    fontSize: 32, textColor: hex, outlineWidth: 0, outlineOpacity: 0
  }).select([0, 1, 2], ['R', 'G', 'B']);
}
function arrowHead(x, y, angle, size, hex) {
  var ux = Math.cos(angle), uy = Math.sin(angle);
  return fill(poly([
    [x, y],
    [x-size*ux-size*0.43*uy, y-size*uy+size*0.43*ux],
    [x-size*ux+size*0.43*uy, y-size*uy-size*0.43*ux]
  ]), hex);
}
function star(x, y, radius, hex) {
  var points = [];
  for (var i = 0; i < 10; i++) {
    var a = -Math.PI/2 + i*Math.PI/5;
    var r = i % 2 === 0 ? radius : radius*0.43;
    points.push([x+r*Math.cos(a), y+r*Math.sin(a)]);
  }
  return fill(poly(points), hex);
}
function pageGrid(x, y) {
  return ee.Projection('EPSG:3857', [1, 0, x, 0, -1, -y]);
}

// RASTER relocation: source and destination share pixel indices.
// This supports administrative GeometryCollections without reading
// their coordinate arrays. It is a figure-layout operation only.
function placeRaster(image, sourceGrid, box) {
  return image.select([0, 1, 2], ['R', 'G', 'B'])
    .reproject(sourceGrid)
    .changeProj(sourceGrid, pageGrid(box.x, box.y))
    .clip(rect(box.x, box.y, box.w, box.h));
}

// Administrative map. Earth Engine handles geometry types internally.
var countries = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level0');
var provinces = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level1')
  .filter(ee.Filter.eq('ADM0_NAME', 'China'));
var china = countries.filter(ee.Filter.eq('ADM0_NAME', 'China'));
var gansu = provinces.filterBounds(station);
var chinaGrid = ee.Projection('EPSG:4326', [
  (GEO.east-GEO.west)/MAPBOX.w, 0, GEO.west,
  0, -(GEO.north-GEO.south)/MAPBOX.h, GEO.north
]);
var locatorRGB = ee.Image.constant(rgb(COL.panel)).toUint8()
  .blend(china.style({
    color: COL.province, fillColor: COL.country, width: 2
  }))
  .blend(provinces.style({
    color: COL.province, fillColor: '00000000', width: 1
  }))
  .blend(gansu.style({
    color: COL.gansuEdge, fillColor: COL.gansu, width: 2
  }));
var locator = placeRaster(locatorRGB, chinaGrid, MAPBOX);
print('Province containing the reported station:', gansu.aggregate_array('ADM1_NAME'));

// SCL cloud / shadow / snow mask. Reflectance bands remain in their
// native DN scale; 0-3000 is a display stretch, not a data correction.
function clearS2(image) {
  var scl = image.select('SCL');
  var clear = scl.neq(0).and(scl.neq(1)).and(scl.neq(3))
    .and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
  return image.updateMask(clear).select(['B4', 'B3', 'B2']);
}
// The 20-km acquisition buffer allows small manual crop adjustments.
var scenes = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(station.buffer(20000))
  .filterDate(CFG.startDate, CFG.endDate)
  .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', CFG.sceneCloudLimit));
var nativeGrid = ee.Image(scenes.first()).select('B4').projection();
var composite = scenes.map(clearS2).median().setDefaultProjection(nativeGrid);
var vis = {bands: ['B4', 'B3', 'B2'], min: 0, max: 3000, gamma: 1.15};
var satelliteRGB = composite.visualize(vis).resample('bilinear');
var verifiedBoundary = null;
if (CFG.fieldBoundaryAsset) {
  verifiedBoundary = ee.FeatureCollection(CFG.fieldBoundaryAsset);
  satelliteRGB = satelliteRGB.blend(verifiedBoundary.style({
    color: 'FFB347', fillColor: '00000000', width: 3
  }));
}

var status = ui.Label('Loading real Sentinel-2 imagery...');
var pngLink = ui.Label('PNG download link will appear here.');
var revision = 0;

function composeFigure(lon, lat) {
  var center = ee.Geometry.Point([lon, lat]);
  // coordinates() is used on a Point only, never on admin polygons.
  var utmXY = ee.List(center.transform(UTM, 1).coordinates());
  var metersPerPixel = CFG.viewWidthM / SATBOX.w;
  var viewHeightM = metersPerPixel * SATBOX.h;
  var west = ee.Number(utmXY.get(0)).subtract(CFG.viewWidthM / 2);
  var north = ee.Number(utmXY.get(1)).add(viewHeightM / 2);
  var sourceGrid = ee.Projection(UTM, ee.List([
    metersPerPixel, 0, west, 0, -metersPerPixel, north
  ]));
  // White fills any genuinely masked pixels; no synthetic imagery.
  var photo = placeRaster(
    satelliteRGB.unmask(255), sourceGrid, SATBOX
  );
  var layers = [
    fill(PAGE, COL.white),
    fill(rect(60, 260, 1390, 1270), COL.panel),
    fill(rect(1650, 260, 1480, 1270), COL.panel),
    locator, photo,
    stroke(rect(60, 260, 1390, 1270), COL.border, 2),
    stroke(rect(1650, 260, 1480, 1270), COL.border, 2),
    stroke(rect(SATBOX.x, SATBOX.y, SATBOX.w, SATBOX.h), COL.border, 3),
    label('Study-site location and agricultural landscape', 100, 100, 52, COL.dark),
    label('Shiyanghe Experimental Station | Wuwei, Gansu, China', 100, 180, 32, COL.muted),
    label('(a) China and Gansu Province', 110, 345, 40, COL.dark),
    label('(b) Real satellite image', 1700, 345, 40, COL.dark),
    label('Sentinel-2 SR | Summer 2021 | Native resolution: 10 m', 1700, 415, 28, COL.muted),
    label('Shiyanghe station', 770, 505, 38, COL.dark),
    label('37.8667 N, 102.8667 E | 1581 m', 770, 565, 28, COL.muted)
  ];
  var sx = MAPBOX.x + (CFG.stationLon-GEO.west)/(GEO.east-GEO.west)*MAPBOX.w;
  var sy = MAPBOX.y + (GEO.north-CFG.stationLat)/(GEO.north-GEO.south)*MAPBOX.h;
  var connectorY = SATBOX.y + SATBOX.h/2;
  var connector = line([
    [sx+28, sy], [1430, sy], [1580, connectorY], [SATBOX.x-8, connectorY]
  ]);
  layers.push(stroke(line([[800, 595], [760, 650], [sx+10, sy-25]]), COL.muted, 2));
  layers.push(stroke(connector, COL.white, 11));
  layers.push(stroke(connector, COL.orange, 5));
  layers.push(arrowHead(SATBOX.x-5, connectorY, 0, 27, COL.orange));
  layers.push(fill(pt(sx, sy).buffer(29, 1), COL.white));
  layers.push(star(sx, sy, 23, COL.orange));
  layers.push(fill(rect(145, 1380, 42, 30), COL.gansu));
  layers.push(label('Gansu Province', 210, 1410, 30, COL.dark));

  // Reported station reference on the real image, if inside the view.
  // This point is deliberately not labelled as a verified DI parcel.
  var stationUTM = ee.List(station.transform(UTM, 1).coordinates());
  var markerX = ee.Number(stationUTM.get(0)).subtract(west)
    .divide(metersPerPixel).add(SATBOX.x);
  var markerY = north.subtract(ee.Number(stationUTM.get(1)))
    .divide(metersPerPixel).add(SATBOX.y);
  var marker = ee.Geometry.Point(
    ee.List([markerX, markerY.multiply(-1)]), 'EPSG:3857'
  );
  var insidePhoto = rect(SATBOX.x, SATBOX.y, SATBOX.w, SATBOX.h);
  layers.push(fill(marker.buffer(18, 1), COL.white).clip(insidePhoto));
  layers.push(fill(marker.buffer(11, 1), COL.orange).clip(insidePhoto));

  // North arrow, true to the north-up UTM satellite grid.
  var nx = SATBOX.x + SATBOX.w - 65;
  var ny = SATBOX.y + 85;
  layers.push(fill(rect(nx-43, ny-58, 85, 195), COL.white));
  layers.push(label('N', nx-13, ny-12, 33, COL.dark));
  layers.push(stroke(line([[nx, ny+103], [nx, ny+15]]), COL.dark, 4));
  layers.push(arrowHead(nx, ny+8, -Math.PI/2, 23, COL.dark));

  // Metric scale bar computed from the actual local UTM grid.
  var scaleM = 500;
  var barW = scaleM / metersPerPixel;
  var bx = SATBOX.x+45, by = SATBOX.y+SATBOX.h-75;
  layers.push(fill(rect(bx-20, by-30, barW+85, 91), COL.white));
  for (var b=0; b<4; b++) {
    layers.push(fill(rect(bx+b*barW/4, by, barW/4, 16), b%2===0 ? COL.dark : COL.white));
  }
  layers.push(stroke(rect(bx, by, barW, 16), COL.dark, 2));
  layers.push(label('0', bx, by+51, 25, COL.dark));
  layers.push(label('500 m', bx+barW-55, by+51, 25, COL.dark));
  layers.push(label('Orange point: reported station reference', 1700, 1500, 27, COL.muted));
  layers.push(label('Boundaries: FAO GAUL 2015 | Site reference: Wang (2023)', 100, 1630, 26, COL.muted));
  layers.push(label('Image: Copernicus Sentinel-2 surface reflectance', 1700, 1630, 26, COL.muted));
  return ee.ImageCollection.fromImages(layers.map(function(im) {
    return ee.Image(im).select([0, 1, 2], ['R', 'G', 'B']);
  })).mosaic().toUint8().setDefaultProjection(PAGE_PROJ).clip(PAGE);
}

function showFigure(lon, lat, addTiffTask) {
  revision += 1;
  status.setValue('Generating the combined figure...');
  var figure = composeFigure(lon, lat);
  var params = {
    region: PAGE, crs: 'EPSG:3857', dimensions: '3200x1700',
    format: 'png', min: 0, max: 255
  };
  print('Combined figure preview ' + revision, ui.Thumbnail({
    image: figure,
    params: {
      region: PAGE, crs: 'EPSG:3857', dimensions: '1600x850',
      format: 'png', min: 0, max: 255
    },
    style: {width: '1000px', height: '531px'}
  }));
  var url = figure.getThumbURL(params);
  pngLink.setValue('Download combined PNG (' + revision + ')');
  pngLink.setUrl(url);
  print('FULL PNG DOWNLOAD ' + revision, url);
  print('Satellite crop center — not a surveyed boundary:', lon, lat);
  status.setValue('Ready. Open the PNG link to save the complete figure.');
  if (addTiffTask) {
    Export.image.toDrive({
      image: figure,
      description: CFG.exportName + '_v' + revision,
      folder: CFG.driveFolder,
      fileNamePrefix: CFG.exportName + '_v' + revision,
      region: PAGE, crs: 'EPSG:3857',
      crsTransform: [1, 0, 0, 0, -1, 0],
      maxPixels: 100000000, fileFormat: 'GeoTIFF',
      formatOptions: {cloudOptimized: true}
    });
  }
}

// Actual geographic map for visual inspection / crop adjustment.
Map.clear();
Map.setOptions('SATELLITE');
Map.setCenter(CFG.stationLon, CFG.stationLat, 15);
var controls = ui.Panel({style: {
  position: 'top-right', width: '350px', padding: '12px', backgroundColor: '#ffffff'
}});
controls.add(ui.Label('URP | Real field-context image', {
  fontWeight: 'bold', fontSize: '17px', color: '#' + COL.dark
}));
controls.add(ui.Label('Pan to the field vicinity. The button below updates only the right-hand image crop. The orange station reference stays at the published coordinates.'));
controls.add(status);
controls.add(pngLink);
var updateButton = ui.Button({
  label: 'Update figure from current map center', disabled: true,
  onClick: function() {
    var c = Map.getCenter();
    // Map.getCenter() returns an ee.Geometry.Point in the Code Editor.
    // Also accept clients exposing a plain {lon, lat} center object.
    if (c && typeof c.coordinates === 'function') {
      status.setValue('Reading the selected image center...');
      c.coordinates().evaluate(function(xy, error) {
        if (error || !xy) {
          status.setValue('Could not read the map center. Try again.');
          print('Map center error:', error);
          return;
        }
        showFigure(xy[0], xy[1], false);
      });
    } else if (c && typeof c.lon === 'number' && typeof c.lat === 'number') {
      showFigure(c.lon, c.lat, false);
    } else {
      status.setValue('Could not read the map center.');
    }
  }
});
controls.add(updateButton);
Map.add(controls);

// Guard the initial run against an empty scene collection.
scenes.size().evaluate(function(n, error) {
  if (error || !n) {
    status.setValue('No image collection available. Check dates, permissions and cloud limit.');
    print('Image loading error:', error);
    return;
  }
  print('Input Sentinel-2 scenes:', n);
  Map.addLayer(composite, vis, '2021 Sentinel-2 true colour', true);
  Map.addLayer(station, {color: COL.orange}, 'Reported station reference');
  if (verifiedBoundary !== null) {
    Map.addLayer(verifiedBoundary, {color: 'FFB347'}, 'Verified DI boundary');
  }
  updateButton.setDisabled(false);
  showFigure(CFG.stationLon, CFG.stationLat, CFG.createInitialTiffTask);
});
