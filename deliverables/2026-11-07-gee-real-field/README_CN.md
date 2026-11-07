# URP：中国—甘肃定位及真实农田影像组合图

将 `URP_RealImagery_Combined.js` 整段复制到 Google Earth Engine Code Editor，点击 Run。

- 左图：中国行政区图，突出甘肃省，标记论文所报石羊河实验站。
- 右图：2021 年 6 月 15 日至 8 月 31 日的 Sentinel-2 SR 真彩色中值合成，原始空间分辨率 10 m，附北箭头及真实米制比例尺。
- 导出：Console 的 FULL PNG DOWNLOAD 链接；初次运行另建立一个 Drive TIFF 任务。
- 可在真实地图上平移到目标农田中心，点击右上角 Update figure from current map center 更新组合图。此操作只调整取景，不修改论文实验站参考点。
- 有经核实的田界时，将 GEE polygon 资产 ID 填入 `CFG.fieldBoundaryAsset` 即可叠加边界。

来源：王尚今（2023）学位论文，印刷第 8—9 页：37°52′N、102°52′E，海拔 1581 m，DI 观测区 400 m × 200 m，覆膜率 75%。该坐标精确到分，不能自动确定田块四角，因此默认没有叠加假定的田界或行向。

影像为真实卫星观测的季节合成，并非某一天的单景，也不是田间拍摄照片。排版放大不改变其原始 10 m 分辨率。

本版本不对行政区调用 `geometry.coordinates()`，通过栅格重定位完成排版，避免 GeometryCollection 的坐标列表错误。`Point()` 均只传入坐标及可选投影。

代码使用公开文字模块 `users/gena/packages:text`。已做本地 JavaScript 语法及版面仿射坐标换算检查；未使用用户 GEE 账户进行服务端执行或实际影像导出。
