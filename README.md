# OSpider
[OSpider](https://skytruine.github.io/OSpider/)是GPL v3.0协议下的开源免费桌面软件及python库，致力于提供便捷的矢量地理数据获取和预处理体验，用户手册及开发者文档完善。目前已不对v3以前版本进一步维护，需要老版的小伙伴或Github/百度网盘下不下来的小伙伴请在用户群中自行下载。
**用户群（QQ）: 939504570**
## 尝鲜版本
**暂无**
## 稳定版本
[**OSpider_v3.0.0**](https://github.com/skytruine/OSpider/releases/download/OSpider_v3.0.0/OSpider.v3.0.0.zip) (Last Release)
(**OSpider v3.0.0桌面版**)[https://github.com/skytruine/OSpider/releases/download/OSpider_v3.0.0/OSpider.v3.0.0.zip] 的核心功能为**按行政区划名称、矩形框、圆形区和自定义面文件**四种方式**抓取POI**(暂仅支持百度POI,高德POI将再下一次更新中加入)，支持通过csv批处理文件批量执行POI抓取任务,且提供了分城市获取POI总量的实用工具。OSpider v3.0.0也集成了**WGS84/BD09/GCJ02坐标互转**工具与**地址解析**工具。

(**OSpider v3.0.0源码**)[https://github.com/skytruine/OSpider/releases/download/OSpider_v3.0.0/OSpider_v3.0.0_code.zip]的功能模块包括POI抓取模块、坐标转换模块、行政区划获取模块、地址解析模块。

## 版本说明与下载链接
- **20200901 | OSpider_v3.0.0** ([应用](https://github.com/skytruine/OSpider/releases/download/OSpider_v3.0.0/OSpider.v3.0.0.zip)|[源码](https://github.com/skytruine/OSpider/releases/download/OSpider_v3.0.0/OSpider_v3.0.0_code.zip))<br>
修正内测阶段Bug:①修正key池耗尽后持续执行的重大Bug;②针对内置Key被快速消耗的问题，不再提供内置Key;③通过增加界面形状记忆，解决部分用户界面显示不全问题；④修正了部分异常处理增强稳定性；⑤修改批处理功能中的“中止”效果为立即中止；⑥为POI结果添加了额外属性；⑦为文件选择添加了类型限制
*备用下载链接：*
应用 | 链接：https://pan.baidu.com/s/1geZK0yWR5Wuc60fcCc5zKg 提取码：lyf5 
源码 | 链接：https://pan.baidu.com/s/1O4OFjl1KXMMku1TYd9J5Bg 提取码：7mqz
- **20200822 | OSpider_v3.0.0_Beta** ([应用](https://github.com/skytruine/OSpider/releases/download/OSpider_v3.0.0-Beta/OSpider_v3.0.0_Beta.zip)|[源码](https://github.com/skytruine/OSpider/releases/download/OSpider_v3.0.0-Beta/OSpider_v3.0.0_Beta_Code.zip))<br>
①提供6种模式抓取POI,预留高德接口;②针对百度高德的抽稀机制更改抓取算法为初始网格阈值四分递归；③引入Key池和多线程;④集成包括地址解析、坐标转换在内的多种功能；⑤重构GUI和所有代码，为发行python库做准备
*备用下载链接：*
应用 | 链接：https://pan.baidu.com/s/1Og-Q7B696mlviwyJNLRQsw 提取码：i2nf
源码 | 链接：https://pan.baidu.com/s/1ztHUMAgCbMRKo1bD_qE-3Q 提取码：1c6b
- **20200615 | OSpider_v2.1.0** ([应用](https://github.com/skytruine/OSpider/releases/download/OSpider_v2.1.0/OSpider_v2.1.0.zip))<br>
①修复部分内陆城市及沿海城市抓取失败Bug(数据模板不一致造成)②为抓取的POI添加了分类等属性；③修正了部分POI行政区划为空的Bug;④针对部分用户界面显示不全问题内置了单独修正版
*备用下载链接：*
应用 | 链接：https://pan.baidu.com/s/1m4czR4NF6vClMGmzhyME4Q 提取码：ja3n
- **20200319 | ExtraTools_v1.0.0** ([应用](https://skytruine.github.io/OSpider/))<br>
独立桌面端辅助工具，内含坐标转换、地址解析功能
- **20200311 | CityNum_v.sp** ([源码](https://skytruine.github.io/OSpider/))<br>
单独.py，实现了分城市获取POI总量功能
- **20191229 | OSpider_v2.0.0** ([应用](https://github.com/skytruine/OSpider/releases/download/OSpider_v2.0.0/OSpider_v2.0.0.zip))<br>
①增添了UI界面,程序运行状态提示更加人性化 ②重构核心代码 ③自动记忆上一次输入的参数 ④新增用户群，开辟交流新渠道
- **20180731 | OSpider_v1.0.1** ([应用](https://github.com/skytruine/OSpider/releases/download/OSpider_v1.0.1/OSpider_v1.0.1.zip))<br>
①修复了中文路径闪退bug;②修复了部分POI由于属性结构问题而无法爬取造成闪退的bug
- **20180725 | OSpider_v1.0.0** ([应用](https://skytruine.github.io/OSpider/))<br>
①通过初始网格自动四分递归算法实现百度POI抓取;②基于百度地图实现了行政区四至获取③将源码封装控制台版exe应用程序

## 关于
### 开发团队
OSpider项目由小O发起和负责，当前开发团队包括：<br>
**华盛顿大学HGIS Lab | 小O**<br>
**西南交通大学 | 苟强**

### 加入我们
我们需要对POI、AOI、Land use、路网及其他GIS/规划相关数据获取及预处理有一定了解和实践经验，并希望为开源社区做贡献的开发者小伙伴-Talk is cheap. Show me the code. 如果你认为OSpider的文档编写、Web主页存在不足，且有能力进行改进，我们也非常欢迎你的加入。有加入意向的小伙伴请发送邮件至sunyifan@uw.edu

### Bug报告与意见反馈
如果你在使用OSpider的过程中发现Bug或对OSpider的有什么建议，请通过[GitHub](https://github.com/skytruine/OSpider)直接发起issue，或向ospider_org@163.com发送邮件。对于微小Bug的修正可以直接在GitHub中发pr，希望主导Feature的进一步开发，请提issue后向ospider_org@163.com发送邮件。
另外，非常欢迎加入OSpider用户群（QQ）: 939504570。

### 支持我们
[GitHub Star](https://github.com/skytruine/OSpider)是对我们的最大肯定，而您的赞助支持将为项目的平稳发展保驾护航
![赞助](https://cdn.jsdelivr.net/gh/skytruine/clouding//img/OSpider赞助.jpg)
