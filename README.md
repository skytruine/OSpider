# OSpider
OSpider是GPL协议下的开源桌面软件及python库，致力于提供便捷的矢量地理数据获取和预处理体验。目前已不对v3以前版本进一步维护，需要老版的小伙伴加入用户群自行下载。

## 尝鲜版本
**暂无**
## 稳定版本
[**OSpider_v3.0.0**](https://skytruine.github.io/OSpider/) (Last Release)
该版本的核心功能为**按行政区划名称、矩形框、圆形区和自定义面文件**四种方式**抓取POI**(暂仅支持百度POI,高德POI将再下一次更新中加入)，支持通过csv批处理文件批量执行POI抓取任务,且提供了分城市获取POI总量的实用工具。OSpider v3.0.0集成了**WGS84/BD09/GCJ02坐标互转**工具与**地址解析**工具。

## 版本说明与下载链接
|  发行时间    |  版本(下载/源码)  | 说明  |
| :-: | :-: | :-: |
|20190831|[OSpider_v3.0.0](https://skytruine.github.io/OSpider/)<br>([源码](https://skytruine.github.io/OSpider/))|修正内测阶段Bug:①修正key池耗尽后持续执行的重大Bug;②针对内置Key被快速消耗的问题，不再提供内置Key;③通过增加界面形状记忆，解决部分用户界面显示不全问题；④修正了部分异常处理增强稳定性；⑤修改批处理功能中的“中止”效果为立即中止；⑥为POI结果添加了额外属性；⑦为文件选择添加了类型限制|
|20190822|[OSpider_v3.0.0_Beta](https://skytruine.github.io/OSpider/)<br>([源码](https://skytruine.github.io/OSpider/))|①提供6种模式抓取POI,预留高德接口;②针对百度高德的抽稀机制更改抓取算法为初始网格阈值四分递归；③引入Key池和多线程;④集成包括地址解析、坐标转换在内的多种功能；⑤重构GUI和所有代码，为发行python库做准备|
|20190615|[OSpider_v2.0.1](https://skytruine.github.io/OSpider/)<br>([源码](https://skytruine.github.io/OSpider/))|①修复部分内陆城市及沿海城市抓取失败Bug(数据模板不一致造成)②为抓取的POI添加了分类等属性；③修正了部分POI行政区划为空的Bug;④针对部分用户界面显示不全问题内置了单独修正版|
|20190319|[ExtraTools_v1.0.0](https://skytruine.github.io/OSpider/)<br>([源码](https://skytruine.github.io/OSpider/))|独立桌面端辅助工具，内含坐标转换、地址解析功能|
|20190311|[CityNum_v.sp](https://skytruine.github.io/OSpider/)<br>([源码](https://skytruine.github.io/OSpider/))|单独.py，实现了分城市获取POI总量功能|
|20191229|[OSpider_v2.0.0](https://github.com/skytruine/OSpider/releases/download/v2.0.0/OSpider_v2.0.0.zip)<br>([源码](https://skytruine.github.io/OSpider/))|①增添了UI界面,程序运行状态提示更加人性化 ②重构核心代码 ③自动记忆上一次输入的参数 ④新增用户群，开辟交流新渠道|
|20180731|[OSpider_v1.0.1](https://skytruine.github.io/OSpider/)<br>([源码](https://skytruine.github.io/OSpider/))|①修复了中文路径闪退bug;②修复了部分POI由于属性结构问题而无法爬取造成闪退的bug|
|20180725|[OSpider_v1.0.0](https://skytruine.github.io/OSpider/)<br>([源码](https://skytruine.github.io/OSpider/))|①通过初始网格自动四分递归算法实现百度POI抓取;②基于百度地图实现了行政区四至获取③将源码封装控制台版exe应用程序|

## 关于
### 开发团队
OSpider项目由小O发起和负责，当前开发团队包括：
- 华盛顿大学HGIS Lab | 小O
- 西南交通大学 | 苟强
### 加入我们
我们需要对POI、AOI、Land use、路网及其他GIS/规划相关数据获取及预处理有一定了解和实践经验，并希望为开源社区做贡献的开发者小伙伴-Talk is cheap. Show me the code. 如果你认为OSpider的文档编写、Web主页存在不足，且有能力进行改进，我也非常欢迎你的加入。有加入意向的小伙伴请发送邮件至sunyifan@uw.edu
### Bug报告与意见反馈
如果您在使用OSpider的过程中发现Bug或对OSpider的使用有什么意见或建议，请向ospider_org@163.com发送邮件我们收到邮件后会尽快回复。另外，非常欢迎加入OSpider用户群（QQ）: 939504570。
### 支持我们
[GitHub Star](https://github.com/skytruine/OSpider)是对我们的最大肯定，而您的赞助支持将为项目的平稳发展保驾护航
![赞助](https://cdn.jsdelivr.net/gh/skytruine/clouding//img/OSpider赞助.jpg)
