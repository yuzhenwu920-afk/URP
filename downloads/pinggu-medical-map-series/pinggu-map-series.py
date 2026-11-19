from collections import Counter
from math import fsum
from pathlib import Path
from tempfile import mkdtemp

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor, QFont
from qgis.core import (
    Qgis, QgsFeature, QgsField, QgsFillSymbol, QgsGeometry,
    QgsLayoutExporter, QgsLayoutItemLabel, QgsLayoutItemMap, QgsLayoutItemMapOverview,
    QgsLayoutItemScaleBar, QgsLayoutItemShape, QgsLayoutPoint, QgsLayoutSize,
    QgsMapLayerStyle, QgsMarkerSymbol, QgsPalLayerSettings, QgsPrintLayout, QgsProject,
    QgsRectangle, QgsSingleSymbolRenderer, QgsTextFormat, QgsUnitTypes,
    QgsVectorFileWriter, QgsVectorLayer, QgsVectorLayerSimpleLabeling,
)

SITES = {
    1: ("峪口镇", 140, 12, "核实现有卫生室和公共服务用房，",
        "比较固定服务点与定期巡诊。"),
    2: ("镇罗营镇", 633, 10, "核实进村道路和季节性通行条件，",
        "确认巡诊车辆可到达的服务点。"),
    3: ("金海湖镇", 1387, 16, "核对边缘居民点到候选点的实际路线，",
        "确认周边现有医疗点的服务能力。"),
}
CLASSES = ("现状 3 km 内覆盖", "模拟新增覆盖", "仍超过 3 km", "模型无路径")
INK, MUTED, TEAL, BRICK = "#172F42", "#4D6470", "#478F83", "#AE4438"


def inputs(project):
    layouts = sorted(
        (layout for layout in project.layoutManager().layouts()
         if layout.name().startswith("峪口镇候选点1_现场核查图")),
        key=lambda layout: layout.name(),
    )
    candidates = [layer for layer in project.mapLayersByName("模拟补点候选点") if layer.isValid()]
    if not layouts or len(candidates) != 1:
        raise RuntimeError("请先打开含原峪口镇现场核查图及唯一「模拟补点候选点」图层的工程。")
    maps = [item for item in layouts[-1].items() if isinstance(item, QgsLayoutItemMap)]
    if len(maps) != 1 or len(maps[0].layers()) != 4:
        raise RuntimeError("原现场核查图应有一张主图和四个数据图层。")
    _, facilities, roads, grid = maps[0].layers()
    return facilities, roads, grid, candidates[0]


def make_points(source, folder, project):
    point_layer = QgsVectorLayer(f"Point?crs={source.crs().authid()}", "候选点", "memory")
    provider = point_layer.dataProvider()
    provider.addAttributes([QgsField("cand", QVariant.Int)])
    point_layer.updateFields()
    features = []
    selected = set()
    for row in source.getFeatures():
        number = int(row["cand"])
        if number not in SITES or number in selected or not row.hasGeometry():
            raise RuntimeError("候选点编号或几何异常。")
        selected.add(number)
        feature = QgsFeature(point_layer.fields())
        feature.setGeometry(row.geometry())
        feature["cand"] = number
        features.append(feature)
    if selected != set(SITES) or not provider.addFeatures(features)[0]:
        raise RuntimeError("应有三个候选点。")
    point_layer.updateExtents()
    path = folder / "report_candidates.gpkg"
    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GPKG"
    opts.layerName = "candidates"
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        point_layer, str(path), project.transformContext(), opts
    )
    if result[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"写入候选点失败：{result}")
    result_layers = {}
    for number in (0, 1, 2, 3):
        layer = QgsVectorLayer(str(path), f"汇报图候选点 {number or '1–3'}", "ogr")
        if number:
            layer.setSubsetString(f'"cand" = {number}')
        if not layer.isValid() or layer.featureCount() != (1 if number else 3):
            raise RuntimeError("候选点回读失败。")
        symbol = QgsMarkerSymbol.createSimple({
            "name": "circle", "color": BRICK, "outline_color": "#FFFFFF",
            "outline_width": "0.45", "size": "7.5",
        })
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        settings = QgsPalLayerSettings()
        settings.fieldName = "cand"
        settings.placement = Qgis.LabelPlacement.OverPoint
        fmt = QgsTextFormat()
        font = QFont("Microsoft YaHei")
        font.setBold(True)
        fmt.setFont(font)
        fmt.setSize(12)
        fmt.setColor(QColor("#FFFFFF"))
        settings.setFormat(fmt)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
        layer.setLabelsEnabled(True)
        result_layers[number] = layer
    return result_layers


class Report:
    def __init__(self, project, title, subtitle, folder):
        self.layout = QgsPrintLayout(project)
        self.layout.initializeDefaults()
        self.layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(320, 204))
        self.layout.setName(f"{title} · {folder.name}")
        self.shape(0, 0, 320, 204, "#F7F7F3")
        self.shape(0, 0, 320, 34, INK)
        self.shape(12, 7, 1.3, 19, "#83C4AC")
        self.text(title, 17, 4, 240, 17, 29, "#FFFFFF", True)
        self.text(subtitle, 17, 22, 240, 8, 14, "#DCE9E8")
        self.text("北京市平谷区", 266, 13, 46, 9, 14, "#DCE9E8")
        self.shape(207, 42, 101, 145, "#FFFFFF")

    def place(self, item, x, y, w, h):
        self.layout.addLayoutItem(item)
        item.attemptMove(QgsLayoutPoint(x, y))
        item.attemptResize(QgsLayoutSize(w, h))
        return item

    def text(self, value, x, y, w, h, size=13, color=INK, bold=False):
        item = QgsLayoutItemLabel(self.layout)
        font = QFont("Microsoft YaHei", size)
        font.setBold(bold)
        item.setFont(font)
        item.setFontColor(QColor(color))
        item.setMargin(0)
        item.setText(value)
        return self.place(item, x, y, w, h)

    def shape(self, x, y, w, h, color, style="solid", circle=False):
        item = QgsLayoutItemShape(self.layout)
        item.setShapeType(item.Ellipse if circle else item.Rectangle)
        item.setSymbol(QgsFillSymbol.createSimple(
            {"color": color, "style": style, "outline_style": "no"}
        ))
        return self.place(item, x, y, w, h)

    def map(self, layers, crs, extent, x=12, y=42, w=188, h=133):
        item = self.place(QgsLayoutItemMap(self.layout), x, y, w, h)
        item.setCrs(crs)
        item.setLayers(layers)
        item.setKeepLayerSet(True)
        item.zoomToExtent(extent)
        item.setFrameEnabled(True)
        item.setFrameStrokeColor(QColor("#D7E0DE"))
        return item

    def legend(self, main, overview):
        self.shape(12, 176, 188, 11, "#FFFFFF")
        items = [
            ("现状覆盖", "#E4E7E9", "solid", 15),
            ("模拟新增", TEAL, "solid", 46),
            ("仍超 3 km", "#DDB9A6", "solid", 77),
            ("模型无路径", "#8E6453", "b_diagonal", 109),
        ]
        if not overview:
            items.append(("现有医疗点", INK, "solid", 145))
        items.append(("候选点", BRICK, "solid", 176 if not overview else 150))
        for label, color, style, x in items:
            self.shape(x, 179.8, 3.5, 3.5, color, style, label in ("现有医疗点", "候选点"))
            self.text(label, x + 4.6, 178, 31, 8, 11)
        scale = QgsLayoutItemScaleBar(self.layout)
        scale.setStyle("Single Box")
        scale.setLinkedMap(main)
        scale.setUnits(QgsUnitTypes.DistanceKilometers)
        scale.setUnitsPerSegment(5 if overview else 1)
        scale.setNumberOfSegments(1)
        scale.setNumberOfSegmentsLeft(0)
        scale.setUnitLabel("km")
        self.place(scale, 12, 188, 35, 9)
        self.text("1 km 人口网格 · 3 km 路网距离 · 试算结果",
                  65, 189, 135, 8, 11, MUTED)

    def inset(self, grid, main):
        self.text("平谷区定位", 266, 45, 41, 8, 12, MUTED)
        extent = QgsRectangle(grid.extent())
        extent.scale(1.10)
        inset = self.map([grid], grid.crs(), extent, 263, 53, 41, 39)
        neutral = grid.clone()
        neutral.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({
            "color": "#DDE7E4", "outline_style": "no"
        })))
        style = QgsMapLayerStyle()
        style.readFromLayer(neutral)
        inset.setLayerStyleOverrides({grid.id(): style.xmlData()})
        inset.setKeepLayerStyles(True)
        overview = QgsLayoutItemMapOverview("局部主图范围", inset)
        overview.setLinkedMap(main)
        overview.setFrameSymbol(QgsFillSymbol.createSimple({
            "style": "no", "outline_color": BRICK, "outline_width": "0.65"
        }))
        inset.overviews().addOverview(overview)

    def export(self, folder, name):
        exporter = QgsLayoutExporter(self.layout)
        image = QgsLayoutExporter.ImageExportSettings()
        image.dpi = 300
        for suffix, save, settings in (
            ("png", exporter.exportToImage, image),
            ("pdf", exporter.exportToPdf, QgsLayoutExporter.PdfExportSettings()),
        ):
            path = folder / f"{name}.{suffix}"
            if save(str(path), settings) != QgsLayoutExporter.Success or not path.stat().st_size:
                raise RuntimeError(f"导出失败：{path}")
            print(path)


def run(output_root=None):
    project = QgsProject.instance()
    facilities, roads, grid, candidates = inputs(project)
    rows = list(grid.getFeatures())
    if Counter(str(row["cls4"]) for row in rows) != dict(zip(CLASSES, (633, 38, 328, 40))):
        raise RuntimeError("全区四类格数与 633、38、328、40 不符。")

    info = {}
    for number, (town, gid, count, a, b) in SITES.items():
        benefit = [row for row in rows if row["cls4"] == CLASSES[1] and row["sim_cand"] == number]
        candidate = next((row for row in benefit if row["gid"] == gid), None)
        if len(benefit) != count or candidate is None:
            raise RuntimeError(f"候选点 {number} 的新增格数或 gid 核对失败。")
        extent = QgsGeometry.unaryUnion([row.geometry() for row in benefit]).boundingBox()
        extent.grow(800)
        gain = fsum(float(row["pop_cal"]) for row in benefit)
        info[number] = town, gid, count, gain, float(candidate["net_dist_m"]) / 1000, extent, a, b

    total = fsum(float(row["pop_cal"]) for row in rows)
    baseline = fsum(float(row["pop_cal"]) for row in rows if row["cls4"] == CLASSES[0])
    gain_total = fsum(item[3] for item in info.values())
    initial, completed = 100 * baseline / total, 100 * (baseline + gain_total) / total

    parent = Path(output_root or Path(grid.source().split("|", 1)[0]).parent)
    folder = Path(mkdtemp(prefix="pinggu_map_series_", dir=parent))
    points = make_points(candidates, folder, project)
    reports = []

    overview = Report(project, "平谷区基层医疗补点总图",
                      "全区 1 km 人口网格 · 三处补点后的 3 km 路网覆盖", folder)
    full = QgsRectangle(grid.extent())
    full.scale(1.06)
    main = overview.map([points[0], grid], grid.crs(), full)
    overview.legend(main, True)
    overview.text("全区人口权重覆盖率", 212, 45, 91, 9, 14, INK, True)
    overview.text(f"{initial:.2f}% → {completed:.2f}%",
                  212, 55, 95, 17, 28, "#25685D", True)
    overview.text(f"+{completed-initial:.2f} 个百分点 · 新增 38 格",
                  212, 74, 93, 9, 13, MUTED)
    overview.text(f"累计新增覆盖人口权重约 {gain_total:,.0f}",
                  212, 84, 93, 9, 13, MUTED)
    overview.shape(212, 96, 91, .35, "#D7E0DE")
    overview.text("模拟补点顺序与新增收益", 212, 99, 90, 9, 15, INK, True)
    for index, (town, gid, count, gain, _, _, _, _) in info.items():
        overview.text(f"{index}  {town}　+{count} 格 · 权重 {gain:,.0f}",
                      212, 107 + index * 11, 92, 9, 13)
    overview.shape(212, 152, 91, 31, "#EAF2EE")
    overview.text("剩余缺口", 216, 154, 83, 8, 14, "#25685D", True)
    overview.text("328 格仍超 3 km，40 格模型无路径。\n先核查道路连通和医疗点接入。",
                  216, 164, 84, 17, 12, INK)
    reports.append((overview, "00_pinggu_1km_overview"))

    for number, (town, gid, count, gain, distance, extent, a, b) in info.items():
        report = Report(project, f"{town}基层医疗补点方案",
                        f"候选点 {number} · 3 km 路网覆盖试算与现场核查", folder)
        main = report.map([points[number], facilities, roads, grid], grid.crs(), extent)
        report.legend(main, False)
        report.inset(grid, main)
        report.text("模拟新增覆盖", 212, 45, 48, 9, 14, INK, True)
        report.text(f"{count} 格", 212, 55, 47, 17, 34, "#25685D", True)
        report.text(f"{gain:,.0f}  人口权重", 212, 73, 52, 9, 16, INK, True)
        report.text(f"候选格现状路网距离\n{distance:.2f} km",
                    212, 83, 53, 15, 12, MUTED)
        report.shape(212, 101, 91, .35, "#D7E0DE")
        report.text("现场优先核查", 212, 105, 90, 9, 15, INK, True)
        report.text(a, 212, 118, 90, 9, 13)
        report.text(b, 212, 130, 90, 9, 13)
        report.shape(212, 152, 91, 31, "#EAF2EE")
        report.text("解释口径", 216, 154, 83, 8, 14, "#25685D", True)
        report.text("新增覆盖按模拟顺序计算。\n村庄居民点及实际通行情况待核查。",
                    216, 164, 83, 17, 12)
        report.text(f"候选网格 gid {gid}", 207, 189, 101, 8, 11, MUTED)
        reports.append((report, f"0{number}_candidate_{number}"))

    for report, name in reports:
        report.export(folder, name)
    for layer in points.values():
        project.addMapLayer(layer, False)
    for report, _ in reports:
        project.layoutManager().addLayout(report.layout)
    print(f"四张汇报图均已导出：{folder}")
    return reports[0][0].layout, folder


if "iface" in globals() and iface is not None:
    overview_layout, _ = run()
    iface.openLayoutDesigner(overview_layout)
