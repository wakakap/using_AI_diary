# AE使用记录

以前零零散散学了一些，快速实践了一些特效，尤其是mmd的伪3d用的比较多。现在打算认真系统地学一下，目标是达到熟练高效地做文字特效，从而配合音乐做PV的水平。

## 快捷键

- `home`：时间轴回到初始
- `n`：输出结尾设为当前位置
- `u`：收起当前layer参数
- `ctrl + home`：shape layer刚画出来时，锚点anchor移动到画面中心。
- `ctrl + alt + home`：锚点移到layer的中心。
- `ctrl + d`：layer复制


## 教程

打算从[PuttiMW](https://www.youtube.com/@PuttiMW)这个频道作为主线，讲解是女声，比较容易入耳。
- [x] #01 这个视频是一些界面介绍，我已经掌握，没有太多可说的。
- [x] #02 设定相关。缓存盘用SSD。右侧的panel可以solo模式，点开新的旧的关闭。
- [ ] #03 shape layer相关
  - [ ] 关于'fill'和'Stroke'的一些操作。双击椭圆形能创建出 elipse的锚点位置和位置都是0的圆，这样能保证shape layer的锚点位置和elipse的相同都是0。可能这里需要阐明。'fill'涂和'Stroke'线都能分开展示。
- [ ] #04
- [ ] #05
- [x] #06 关于导出设置，`B` 确定范围开头 `N` 确定范围结尾。
  - 渲染队列（在AE内渲染）：视频中用了 `QuickTime - Apple ProRes 422HQ` （我只尝试`QuickTime - 动画`，体积比较大）
  - 创建模板：点击输出模块三角形，保存设置模板。
  - 关于alpha视频的渲染设置：目前用不上先不管。
  - 另一种渲染mp4，导出到 `Adobe Media Encoder` 渲染。适合 `H264` ，试了下默认的，质量、大小和渲染速度都比较合适。渲染时内存占用不高，可以干别的，推荐。（如果报错，可以直接打开AME导入AE项目选择合成）

## 脚本

**批量导入脚本**：试用了几款，最后从插入方便，简洁等角度选择了Transcriptive SRT Importer

**自动截取声音片段**：VØID - Silence Remover 可以选择是否保留空隙，反转。
- 参数经验：padding越大保留两侧越多；tolerance越小声音越多 `13, 0.6` 比较好。

**去除空隙**：removeGap.jsx 可以去除空隙，目前执行单次，不能连续执行。