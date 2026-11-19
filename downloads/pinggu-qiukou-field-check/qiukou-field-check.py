from collections import Counter
from datetime import datetime
from math import fsum, isfinite
from pathlib import Path
from tempfile import mkdtemp

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor, QFont
from qgis.core import (
    QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsFeature, QgsField, QgsFillSymbol, QgsGeometry, QgsLayoutExporter,
    QgsLayoutItemLabel, QgsLayoutItemLegend, QgsLayoutItemMap, QgsLayoutItemScaleBar,
    QgsLayoutPoint, QgsLayoutSize, QgsLineSymbol, QgsMarkerSymbol, QgsPrintLayout,
    QgsProject, QgsRectangle, QgsRendererCategory, QgsSingleSymbolRenderer,
    QgsUnitTypes, QgsVariantUtils, QgsVectorFileWriter, QgsVectorLayer, QgsWkbTypes,
)


def run(parent=None):
    project = QgsProject.instance()

    def find(*names):
        for name in names:
            found = [layer for layer in project.mapLayersByName(name) if layer.isValid()]
            if len(found) == 1:
                return found[0]
            if len(found) > 1:
                raise RuntimeError(f"发现多个同名图层 {name}，请在图层面板区分名称。")
        raise RuntimeError(f"缺少源图层：{' / '.join(names)}")

    def integer(value):
        return None if QgsVariantUtils.isNull(value) else int(value)

    def indexed(layer):
        result = {}
        for feature in layer.getFeatures():
            gid = integer(feature["gid"])
            if gid is None or gid in result:
                raise ValueError(f"{layer.name()} 有空值或重复 gid：{gid}")
            result[gid] = feature
        return result

    source = find("服务缺口与模拟补点网格_制图", "服务缺口与模拟补点网格")
    base = find("accessibility_grid_v0")
    points = find("模拟补点候选点")
    road_source = find("pinggu_b_delivery_v0 — roads", "roads")
    facility_source = find("pinggu_b_delivery_v0 — facilities_primary", "facilities_primary")
    grid, baseline = indexed(source), indexed(base)
    if grid.keys() != baseline.keys():
        raise ValueError(f"gid 未匹配：制图侧 {len(grid.keys()-baseline.keys())}，基线侧 {len(baseline.keys()-grid.keys())}")

    classes = ("现状 3 km 内覆盖", "模拟新增覆盖", "仍超过 3 km", "模型无路径")
    by_gid, stage_one = {}, []
    for gid, feature in grid.items():
        row = baseline[gid]
        status = str(row["status"])
        raw = row["net_dist_m"]
        distance = None if QgsVariantUtils.isNull(raw) else float(raw)
        stage = integer(feature["sim_cand"])
        if stage not in (None, 0, 1, 2, 3):
            raise ValueError(f"gid {gid} 的 sim_cand 无效：{stage}")
        if distance is None:
            if status == "可达" or stage in (1, 2, 3):
                raise ValueError(f"gid {gid} 的空距离与状态或补点阶段冲突")
            code = 3
        elif not isfinite(distance) or distance < 0 or status != "可达":
            raise ValueError(f"gid {gid} 的基线距离或状态异常：{distance} / {status}")
        elif distance <= 3000:
            if stage in (1, 2, 3):
                raise ValueError(f"gid {gid} 已处于 3 km 覆盖内，同时被标为新增")
            code = 0
        elif stage in (1, 2, 3):
            code = 1
            if stage == 1:
                stage_one.append(gid)
        else:
            code = 2
        by_gid[gid] = code
    counts = Counter(by_gid.values())
    actual = [counts[i] for i in range(4)]
    print(f"分类 {actual}，未匹配 0，候选点 1 新增 {len(stage_one)} 格")
    if actual != [633, 38, 328, 40] or len(stage_one) != 12 or 140 not in stage_one:
        raise ValueError("分类或候选点 1 格数与验收值不符，未写出成果。")
    gains = fsum(float(baseline[gid]["pop_cal"]) for gid in stage_one)
    distance = float(baseline[140]["net_dist_m"])
    candidates = [f for f in points.getFeatures() if integer(f["cand"]) == 1]
    if len(candidates) != 1:
        raise ValueError(f"编号 1 候选点应有 1 个，实际有 {len(candidates)} 个。")

    crs = QgsCoordinateReferenceSystem("EPSG:32650")
    transform = QgsCoordinateTransform(source.crs(), crs, project)
    extent = QgsGeometry.unaryUnion([grid[gid].geometry() for gid in stage_one])
    extent.transform(transform)
    if extent.isEmpty():
        raise ValueError("候选点 1 的受益网格没有有效几何。")
    bbox = extent.boundingBox()
    bbox.grow(800)

    memory = QgsVectorLayer(
        f"{QgsWkbTypes.displayString(source.wkbType())}?crs={source.crs().authid()}",
        "补点覆盖分类", "memory"
    )
    provider = memory.dataProvider()
    if not provider.addAttributes([
        QgsField("gid", QVariant.Int), QgsField("cls4", QVariant.String),
        QgsField("sim_cand", QVariant.Int), QgsField("pop_cal", QVariant.Double),
        QgsField("net_dist_m", QVariant.Double),
    ]):
        raise RuntimeError("未能建立制图字段。")
    memory.updateFields()
    new_features = []
    for gid, feature in grid.items():
        f = QgsFeature(memory.fields())
        f.setGeometry(feature.geometry())
        f.setAttributes([gid, classes[by_gid[gid]], integer(feature["sim_cand"]),
                         baseline[gid]["pop_cal"], baseline[gid]["net_dist_m"]])
        new_features.append(f)
    if not provider.addFeatures(new_features)[0] or memory.featureCount() != 1039:
        raise RuntimeError("未能写入完整制图网格。")

    parent = Path(parent) if parent else Path.home() / "Desktop" / "pinggu_delivery"
    parent.mkdir(parents=True, exist_ok=True)
    output = Path(mkdtemp(prefix="qiukou_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_", dir=parent))
    gpkg = output / "coverage.gpkg"
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GPKG"
    opts.layerName = "coverage"
    result = QgsVectorFileWriter.writeAsVectorFormatV3(memory, str(gpkg), project.transformContext(), opts)
    if result[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"GeoPackage 写入失败：{result}")
    layer = QgsVectorLayer(str(gpkg) + "|layername=coverage", "服务缺口与模拟补点网格_核验版", "ogr")
    if not layer.isValid() or Counter(f["cls4"] for f in layer.getFeatures()) != Counter(dict(zip(classes, actual))):
        raise RuntimeError("GeoPackage 回读分类不符。")
    fills = [
        {"color": "#E4E7E9"}, {"color": "#478F83"}, {"color": "#DDB9A6"},
        {"color": "#8E6453", "style": "b_diagonal"},
    ]
    categories = [QgsRendererCategory(c, QgsFillSymbol.createSimple(dict(p, outline_style="no")), c)
                  for c, p in zip(classes, fills)]
    layer.setRenderer(QgsCategorizedSymbolRenderer("cls4", categories))

    roads = road_source.clone()
    roads.setName("道路")
    roads.setLabelsEnabled(False)
    roads.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(
        {"line_color": "#828992", "line_width": "0.14"})))
    facilities = facility_source.clone()
    facilities.setName("现有基层医疗点")
    facilities.setLabelsEnabled(False)
    facilities.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": "#173651", "outline_color": "#FFFFFF",
         "outline_width": "0.24", "size": "2.4"})))
    if points.providerType() == "memory":
        candidate = QgsVectorLayer(f"Point?crs={points.crs().authid()}", "候选点 1（gid 140）", "memory")
        f = QgsFeature()
        f.setGeometry(candidates[0].geometry())
        if not candidate.dataProvider().addFeatures([f])[0]:
            raise RuntimeError("未能复制候选点。")
        candidate.updateExtents()
    else:
        candidate = points.clone()
        candidate.setName("候选点 1（gid 140）")
        if not candidate.setSubsetString('"cand" = 1') or candidate.featureCount() != 1:
            raise RuntimeError("候选点图层筛选失败。")
    candidate.setLabelsEnabled(False)
    candidate.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "diamond", "color": "#AE4438", "outline_color": "#FFFFFF",
         "outline_width": "0.4", "size": "4.4"})))

    point_opts = QgsVectorFileWriter.SaveVectorOptions()
    point_opts.driverName = "GPKG"
    point_opts.layerName = "candidate_1"
    point_opts.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    result = QgsVectorFileWriter.writeAsVectorFormatV3(candidate, str(gpkg), project.transformContext(), point_opts)
    if result[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"候选点写入失败：{result}")
    persistent = QgsVectorLayer(str(gpkg) + "|layername=candidate_1", candidate.name(), "ogr")
    if not persistent.isValid() or persistent.featureCount() != 1:
        raise RuntimeError("候选点回读失败。")
    persistent.setRenderer(candidate.renderer().clone())
    candidate = persistent

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.pageCollection().pages()[0].setPageSize("A4", layout.pageCollection().pages()[0].Landscape)
    layout.setName("峪口镇候选点1_现场核查图 " + output.name.removeprefix("qiukou_"))

    def place(item, x, y, width, height):
        layout.addLayoutItem(item)
        item.attemptMove(QgsLayoutPoint(x, y))
        item.attemptResize(QgsLayoutSize(width, height))

    def label(content, size, color, x, y, width, height, bold=False):
        item = QgsLayoutItemLabel(layout)
        font = QFont("Microsoft YaHei", size)
        font.setBold(bold)
        item.setFont(font)
        item.setFontColor(QColor(color))
        item.setText(content)
        place(item, x, y, width, height)

    label("峪口镇候选点 1 现场核查图", 19, "#173651", 13, 8, 270, 13, True)
    label("平谷区基层医疗补点试算  /  3 km 路网距离  /  1 km 人口网格",
          10, "#566674", 13, 24, 270, 8)
    map_item = QgsLayoutItemMap(layout)
    map_item.setCrs(crs)
    place(map_item, 13, 38, 186, 150)
    map_item.setLayers([candidate, facilities, roads, layer])
    map_item.setKeepLayerSet(True)
    map_item.zoomToExtent(bbox)
    map_item.setFrameEnabled(True)
    map_item.setFrameStrokeColor(QColor("#B3BDC2"))

    label(f"新增覆盖 {len(stage_one)} 格", 15, "#173651", 207, 39, 77, 10, True)
    label(f"候选点 1 · gid 140\n新增人口权重约 {gains:,.0f}\n候选网格现状路网距离 {distance / 1000:.2f} km",
          10, "#25394A", 207, 52, 77, 25)
    legend = QgsLayoutItemLegend(layout)
    legend.setTitle("图例")
    legend.setLinkedMap(map_item)
    legend.setAutoUpdateModel(False)
    root = legend.model().rootGroup()
    root.removeAllChildren()
    for item in (candidate, facilities, roads, layer):
        root.addLayer(item)
    place(legend, 207, 85, 76, 78)
    scale = QgsLayoutItemScaleBar(layout)
    scale.setStyle("Single Box")
    scale.setLinkedMap(map_item)
    scale.setUnits(QgsUnitTypes.DistanceMeters)
    scale.setUnitsPerSegment(500)
    scale.setNumberOfSegments(2)
    scale.setNumberOfSegmentsLeft(0)
    scale.setUnitLabel("m")
    place(scale, 14, 189, 35, 9)
    label("现场核查  /  进村道路连通性 · 现有卫生室 · 可利用场地", 9, "#566674", 207, 166, 77, 20)
    label("资料口径  /  现有路网与基层医疗点数据 · 村庄居民点待核查", 9, "#566674", 82, 191, 205, 10)

    png, pdf = (output / "qiukou_candidate_1.png", output / "qiukou_candidate_1.pdf")
    exporter = QgsLayoutExporter(layout)
    img = QgsLayoutExporter.ImageExportSettings()
    img.dpi = 240
    for path, code in (
        (png, exporter.exportToImage(str(png), img)),
        (pdf, exporter.exportToPdf(str(pdf), QgsLayoutExporter.PdfExportSettings())),
    ):
        if code != QgsLayoutExporter.Success or not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"导出失败：{path}，返回码 {code}")
    for display_layer in (layer, roads, facilities, candidate):
        project.addMapLayer(display_layer, False)
    group = project.layerTreeRoot().insertGroup(0, layout.name())
    for display_layer in (candidate, facilities, roads, layer):
        group.addLayer(display_layer)
    for old_name in ("服务缺口与模拟补点网格", "服务缺口与模拟补点网格_制图"):
        for old_layer in project.mapLayersByName(old_name):
            node = project.layerTreeRoot().findLayer(old_layer.id())
            if node is not None:
                node.setItemVisibilityChecked(False)
    project.layoutManager().addLayout(layout)
    print(f"PNG：{png}\nPDF：{pdf}\nGeoPackage：{gpkg}")
    print("村庄居民点待核查。若需在当前工程保留可编辑布局，请按 Ctrl+S 保存工程。")
    return layout, output
