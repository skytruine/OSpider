# -*- coding:utf-8 -*-
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
from tkinter import ttk
import sys
import os
import configparser
import webbrowser
import geopandas as gpd
import pandas as pd
from threading import Timer
from threading import Thread
from POISpider import BaiduPOISpider
import CoordTrans as coord
import Geocoder as coder
#尝试解决pyinstaller打包失败
from pyproj import _datadir, datadir
from osgeo import ogr
from osgeo import gdal
from fiona import _shim, schema
#用于将输出进行重定向
#用于将输出进行重定向
class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.see('end')
        self.widget.configure(state="disabled")

#OSpider主窗口
class OSpider_Main(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title('OSpider v3.0.0_Beta')
        self.geometry('305x400')
        self.resizable(1, 1)
        self.iconbitmap('icon.ico')

        # 创建菜单-----start--------------------------------------------------
        self.menubar = tk.Menu(self)
        helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='帮助', menu=helpmenu)
        helpmenu.add_command(label='快速引导', command=self.help_quickstart)
        helpmenu.add_command(label='用户手册', command=self.help_help)
        helpmenu.add_command(label='技术支持', command=self.help_support)
        helpmenu.add_command(label='定制服务', command=self.help_service)
        toolmenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='工具', menu=toolmenu)
        toolmenu.add_command(label='坐标正反查询', command=self.tool_CoordPick)
        toolmenu.add_command(label='区划四至查询', command=self.tool_ADbounds)
        ADsubmenu =tk.Menu(self.menubar, tearoff=0)
        ADsubmenu.add_command(label='百度POI分类', command=self.tool_BaiduTag)
        ADsubmenu.add_command(label='高德POI分类', command=self.tool_GaodeTag)
        toolmenu.add_cascade(label='POI类型参考', menu=ADsubmenu)
        # toolmenu.add_command(label='POI类型参考', command=self.t)
        toolmenu.add_command(label='行政区划下载', command=self.tool_ADdownload)

        toolmenu.add_separator()
        toolmenu.add_command(label='分城POI总量', command=self.tool_getPOI_CityNum)
        toolmenu.add_command(label='批量爬取POI', command=self.tool_getPOI_byBatch)
        toolmenu.add_command(label='地址解析工具', command=self.tool_Geouncoding)
        toolmenu.add_command(label='坐标转换工具', command=self.tool_CoordTrans)
        aboutmenu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='关于', menu=aboutmenu)
        aboutmenu.add_command(label='作者', command=self.about_author)
        aboutmenu.add_command(label='软件', command=self.about_software)
        aboutmenu.add_separator()
        aboutmenu.add_command(label='赞助支持', command=self.about_support)
        aboutmenu.add_command(label='GitHub', command=self.about_GitHub)
        aboutmenu.add_command(label='加入我们', command=self.about_joinus)
        self.menubar.add_command(label='Key池',comman=self.set_key)
        self.config(menu=self.menubar)
        # 创建菜单-----end--------------------------------------------------

        # 生成主界面其余widget-----start--------------------------------------
        #第一行，查询关键词和POI类型
        tk.Label(self, text='POI名称', width=9, height=1, pady=5).grid(row=0, column=0)
        self.e_query = tk.Entry(self, width=10)
        self.e_query.grid(row=0, column=1, sticky='W')

        tk.Label(self, text='POI类型', width=9, height=1, pady=8).grid(row=0, column=2)
        self.e_tag = tk.Entry(self, width=10)
        self.e_tag.grid(row=0, column=3, sticky='W')

        # 第二行，用来输入Region
        self.tabControl = ttk.Notebook(self)
        self.tabControl.grid(row=1,column=0,columnspan=4,sticky='W',padx=10)
        tab_byAD=ttk.Frame(self.tabControl)
        tab_byBounds=ttk.Frame(self.tabControl)
        tab_byCircle=ttk.Frame(self.tabControl)
        tab_byFile=ttk.Frame(self.tabControl)
        self.tabControl.add(tab_byAD,text='行政区')
        self.tabControl.add(tab_byBounds,text='矩形框')
        self.tabControl.add(tab_byCircle,text='圆形区')
        self.tabControl.add(tab_byFile,text='自定义')

        tk.Label(tab_byAD, text='区划名称', width='9', height=1).grid(row=0, column=0)
        self.e_byAD=tk.Entry(tab_byAD, width='18')
        self.e_byAD.grid(row=0, column=1)
        tk.Button(tab_byAD, width='8', text='区划清单', height='1',command=self.b_ADlist).grid(row=0, column=2,padx=7,pady=5)

        tk.Label(tab_byBounds, text='矩形定义', width='9', height=1).grid(row=0, column=0)
        self.e_byBounds = tk.Entry(tab_byBounds, width='18')
        self.e_byBounds.grid(row=0, column=1)
        tk.Button(tab_byBounds, width='8', text='辅助查询', height='1', command=self.tool_ADbounds).grid(row=0, column=2, padx=7, pady=5)


        tk.Label(tab_byCircle, text='圆形定义', width='9', height=1).grid(row=0, column=0)
        self.e_byCircle = tk.Entry(tab_byCircle, width='18')
        self.e_byCircle.grid(row=0, column=1)
        tk.Button(tab_byCircle, width='8', text='辅助查询', height='1', command=self.tool_CoordPick).grid(row=0, column=2, padx=7,pady=5)

        tk.Label(tab_byFile, text='文件路径', width='9', height=1).grid(row=0, column=0)
        self.e_byFile = tk.Entry(tab_byFile, width='22')
        self.e_byFile.grid(row=0, column=1)
        tk.Button(tab_byFile, width='4', text='浏览', height='1', command=lambda: self.openfile(self.e_byFile)).grid(row=0, column=2, padx=7,pady=5)

        # 第三行，用来获取格网四分递归的参数
        tk.Label(self, text='初始网格', width=9, height=1, pady=5).grid(row=2, column=0)
        self.e_grid_num = tk.Entry(self, width=10)
        self.e_grid_num.grid(row=2, column=1, sticky='W')

        tk.Label(self, text='四分阈值', width=9, height=1, pady=5).grid(row=2, column=2)
        self.e_threshold = tk.Entry(self, width=10)
        self.e_threshold.grid(row=2, column=3, sticky='W')

        # 第四行，用来确定并发与数据源
        tk.Label(self, text='线程数', width=9, height=1, pady=0).grid(row=3, column=0)
        self.e_thread_num = tk.Entry(self, width=10)
        self.e_thread_num.grid(row=3, column=1, sticky='W')

        tk.Label(self, text='数据源', width=9, height=1, pady=0).grid(row=3, column=2)
        self.cmb_data_source = ttk.Combobox(self,width=7)
        self.cmb_data_source['value'] = (['百度地图','高德地图'])
        self.cmb_data_source.current(0)
        self.cmb_data_source.grid(row=3, column=3, sticky='W')

        #第五行，文件保存路径设置
        tk.Label(self, text='输出文件', width='9', height=1).grid(row=4, column=0)
        self.e_outFilePath = tk.Entry(self, width='20')
        self.e_outFilePath.grid(row=4, column=1,columnspan=2)
        tk.Button(self, width='9', text='浏览', height='1', command=lambda: self.savefile(self.e_outFilePath)).grid(row=4, column=3, padx=3, pady=5)

        # 第六行，帮助及执行按钮
        tk.Button(self, width='6', text='帮助', height='1', command=self.help).grid(row=5, column=0, columnspan=1,pady=3)
        tk.Button(self, width='30', text='执行', height='1', command = lambda: self.thread_it(self.tool_getPOI_byRegion)).grid(row=5, column=1,columnspan=3, pady=3)

        # 第七行，通用输出console
        tk.Label(self, text='运行状态', width=9, height=1, pady=3).grid(row=6, column=0,sticky='NW')
        self.console = tk.Text(self, width='31', height='10', state='disabled')
        self.console.config(bg='#eee', fg='#888')
        self.console.tag_configure("stderr", foreground="#b22222")
        self.console.grid(row=6,column=1, columnspan=3,pady=3)
        sys.stdout = TextRedirector(self.console, "stdout")
        sys.stderr = TextRedirector(self.console, "stderr")
        print('欢迎使用OSpider...\n请尽量使用自己的key池....\n用户群(QQ):939504570')


        #读取所需文件并写入
        try:
            cf = configparser.ConfigParser()
            cf.read('property.ini')
            self.e_query.insert("end",cf.get('POISpider', 'query'))
            self.e_tag.insert("end",cf.get('POISpider', 'tag'))
            self.e_byAD.insert("end", cf.get('POISpider', 'AD'))
            self.e_byBounds.insert("end", cf.get('POISpider', 'bounds'))
            self.e_byCircle.insert("end", cf.get('POISpider', 'circle'))
            self.e_byFile.insert("end", cf.get('POISpider', 'file'))
            self.e_grid_num.insert("end", cf.get('POISpider', 'grid_num'))
            self.e_threshold.insert("end", cf.get('POISpider', 'threshold'))
            self.e_thread_num.insert("end", cf.get('POISpider', 'thread_num'))
            self.e_outFilePath.insert("end", cf.get('POISpider', 'outFilePath'))
            keystr=cf.get('Key', 'keyBaidu').split('\n')[0]
            keylist=list()
            for key in keystr.split(','):
                keylist.append(key)
            if 'mgRIjArNHuol074XjsyDPQMu7g22hEjZ' in keylist or 'Zdi4l0k8V41sQqoXdIyZMRDxh3GUzDte' in keylist:
                thread_protect=1
            else:
                thread_protect=int(cf.get('Key', 'thread_protect'))
        except Exception as e:
            keylist=['mgRIjArNHuol074XjsyDPQMu7g22hEjZ','Zdi4l0k8V41sQqoXdIyZMRDxh3GUzDte']
            thread_protect=1
            sys.stderr.write('property.ini文件缺失或错误，虽不影响使用，但会失去参数保存功能\n')
            sys.stderr.write(e)

        #创建所需爬虫类，并设置key池
        self.spider = BaiduPOISpider()  # 实例化BaiduPOISpider类
        self.spider.set_key(keylist, thread_protect=thread_protect)  # key池设置一次就够了


    def about_author(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('关于开发者...')
        tk.messagebox.showinfo(title='关于开发者',message='发起人：小O | 武大城市化研究室 & 华盛顿大学HGIS Lab\n开发团队：小O(其他小伙伴快到碗里来)')
    def about_software(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('关于OSpider...')
        tk.messagebox.showinfo(title='关于OSpider', message='版本：v3.0.0(<-v2.1.0)\n核心功能：获取POI数据\n升级说明：1.配置了key池和多线程\n2.改进了抓取算法\n3.支持多模式抓取和批处理\n4.集成了包括地址解析在内的多个独立工具\n5.重构GUI')
    def about_joinus(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('加入我们...')
        tk.messagebox.showinfo(title='加入我们',message='Talk is cheap. Show me the code.')
    def about_support(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('赞助支持，多少随意....')
        webbrowser.open('https://img-blog.csdnimg.cn/20200819163015411.jpg')
    def about_GitHub(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('GitHub来个Star或者直接贡献代码很赞哟...')
        webbrowser.open('https://github.com/skytruine/OSpider')
    def help_quickstart(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('快速引导...')
        tk.messagebox.showinfo(title='快速引导',message='1.菜单栏设置Key池后即可正常运行;\n2.主界面支持四种方式抓POI,其余工具请在工具菜单中选择;\n3.点击各界面中的帮助按钮会在运行状态栏输出工具使用指南')
    def help_help(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开帮助文件...')
        try:
            os.startfile('help.pdf')
        except Exception as e:
            sys.stderr.write('help.pdf文件缺失...')
            sys.stderr.write(e)
    def help_support(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('发送邮件或加入用户群获取技术支持...')
        tk.messagebox.showinfo(title='技术支持', message='加入用户群(QQ)939504570，或发送邮件至ospider_org@163.com')
    def help_service(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('定制服务...')
        tk.messagebox.showinfo(title='定制服务', message='最近没空...')

    def tool_ADbounds(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开行政区外接矩形获取工具...')
        webbrowser.open('http://guihuayun.com/poi/region.php')
    def tool_CoordPick(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开坐标拾取器...')
        webbrowser.open('http://www.guihuayun.com/tools.php?id=10')
    def tool_ADdownload(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开行政区划下载工具...')
        webbrowser.open('http://datav.aliyun.com/tools/atlas')
    def tool_BaiduTag(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开百度POI分类表...')
        webbrowser.open('http://lbsyun.baidu.com/index.php?title=lbscloud/poitags')
    def tool_GaodeTag(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开高德POI分类表...')
        webbrowser.open('https://lbs.amap.com/api/webservice/download')
    def b_ADlist(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开行政区划清单...')
        webbrowser.open('http://www.mca.gov.cn/article/sj/xzqh/2020/2020/202003301019.html')
    def tool_getPOI_byRegion(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('启动按区域抓取POI工具...')
        cf = configparser.ConfigParser()
        cf.read('property.ini')
        cf.set('POISpider', 'query', self.e_query.get())
        cf.set('POISpider', 'tag', self.e_tag.get())
        cf.set('POISpider', 'AD', self.e_byAD.get())
        cf.set('POISpider', 'bounds', self.e_byBounds.get())
        cf.set('POISpider', 'circle', self.e_byCircle.get())
        cf.set('POISpider', 'file', self.e_byFile.get())
        cf.set('POISpider', 'grid_num', self.e_grid_num.get())
        cf.set('POISpider', 'threshold', self.e_threshold.get())
        cf.set('POISpider', 'thread_num', self.e_thread_num.get())
        cf.set('POISpider', 'outFilePath', self.e_outFilePath.get())
        cf.write(open('property.ini', 'w'))
        query=self.e_query.get()
        tag=self.e_tag.get()
        AD=self.e_byAD.get()
        bounds=self.e_byBounds.get()
        circle=self.e_byCircle.get()
        file=self.e_byFile.get()
        grid_num=int(self.e_grid_num.get())
        if grid_num>20:
            grid_num=20
        threshold=int(self.e_threshold.get())
        if threshold<50:
            threshold=50
        thread_num=int(self.e_thread_num.get())
        outFilePath=self.e_outFilePath.get()
        model=self.tabControl.tab(self.tabControl.select(), 'text')
        if model=='行政区': #执行按行政区抓取POI
            gdf=self.spider.getPOI_byAD(query,tag,AD,grid_num,threshold,thread_num)
        elif model=='矩形框': #执行按矩形框抓取POI
            left=float(bounds.split(',')[0])
            down= float(bounds.split(',')[1])
            right = float(bounds.split(',')[2])
            up = float(bounds.split(',')[3])
            gdf=self.spider.getPOI_byBounds(query,tag,left,down,right,up,grid_num,threshold,thread_num)
        elif model=='圆形区': #执行按圆形区抓取POI
            lng=float(circle.split(',')[0])
            lat=float(circle.split(',')[1])
            r=int(circle.split(',')[2])
            if r>30000:  #防止圆形区域太大了，这里我设置的半径上限是30km
                r=30000
            gdf=self.spider.getPOI_byCircle(query,tag,lng,lat,r,grid_num,threshold,thread_num)
        else: #执行按照自定义文件抓取POI
            gdf=self.spider.getPOI_byFile(query,tag,file,grid_num,threshold,thread_num)
            # 根据用户定义的输出类型执行输出操作
        if type(gdf) == type(gpd.GeoDataFrame()):
            outType = outFilePath.split('.')[len(outFilePath.split('.')) - 1]
            if outType == 'csv' or outType == 'txt':
                gdf.to_csv(outFilePath, encoding='utf-8-sig')
            elif outFilePath.split('.')[len(outFilePath.split('.')) - 1] == 'json':
                gdf.to_file(outFilePath, driver='GeoJSON', encoding='utf-8')
            else:
                gdf.to_file(outFilePath, encoding='utf-8')
            print('写入完成，结果存储于：' + outFilePath)
        else:
            sys.stderr.write('emmmmmm,返回的数据为空，不可能完成写入的啊\n')


    def tool_getPOI_CityNum(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开分城市获取POI总量工具...')
        OSpider_CityNum(self)

    def tool_getPOI_byBatch(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开POI抓取批处理...')
        OSpider_POIBatch(self)
    def tool_Geouncoding(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开地址解析工具')
        OSpider_Geocoder(self)

    def tool_CoordTrans(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开坐标转换工具....')
        OSpider_CoordTrans(self)

    def help(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('---------帮助文档----------')
        print('工具名称：按区域抓取POI')
        print('核心功能：按行政区划名称/矩形框/圆形区/自定义面文件抓取某数据源（百度/高德/谷歌)特定关键词和类型的POI数据并保存为指定类型文件(shp/json/csv/txt')
        print('--------输入参数说明--------')
        print('POI名称：查询关键词，如“酒吧”，“联想售后”；')
        print('POI类型：POI分类标识，如”美食”、“中餐厅”，可以通过工具->POI类型表查询支持的POI类型。当为空时，不进行类型限制。')
        print('区划名称：省（不建议)、市、区名称（支持模糊匹配，如输入武汉，代码将自动解析为武汉市）。当要抓区县级行政区时，建议采用城市名+区县名的方式（因为区县级行政区存在重名），样例如“武汉市”，“武汉市洪山区”，行政区名称可通过右侧清单按钮进行查看')
        print('矩形定义：左下经度,左下纬度,右上经度,右上纬度。注意两点定义矩形的坐标需与数据源匹配，可通过右侧辅助按钮进行辅助获取。')
        print('圆形定义：圆心经度,圆心纬度,半径。注意坐标需与数据源匹配，半径的单位为米，可通过右侧辅助按钮进行辅助获取。')
        print('文件路径：自定义抓取区域面文件的路径，支持shp,json,kml等常用格式,坐标系是什么都行，程序内部会自动根据需要进行转换。')
        print('初始网格：抓取时首先将抓取区域的外接矩形划分为n*n个切片，初始网格数n越大一般数据越全（但速度越慢），一般抓城市级的POI，设置为6-12已经够用了，如果设置为大于20的数，在实际执行时将强制重置为20。')
        print('四分阈值：当切片返回的POI量大于四分阈值m的时候，将对当前切片进一步四分。四分阈值小数据越精确，一般设置为100就够用了，如果设置为小于50的数，在实际执行时将强制重置为50.')
        print('线程数：多线程抓取中启用的线程数，如果线程数>key池大小*并发保护数(在key池中设置)，实际执行时的线程数将被消减至“key池大小*并发保护数”')
        print('数据源：抓取POI所使用的数据源，当前仅支持百度地图。')
        print('输出文件：结果文件的保存路径，支持输出为shp,txt,csv,json')
        print('--------结果文件说明--------')
        print('输出文件中将存储POI名称，类别，地址，所属行政区及BD09和WGS84坐标')
        print('----------注意事项---------')
        print('好像没啥要特别注意的')
        self.console.see(1.0)
    def set_key(self):
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('打开Key池配置页面...')
        OSpider_KeyPool(self)
    def openfile(self,widget):
        str_inputFilePath=tk.filedialog.askopenfilename()
        widget.delete(0,'end')
        widget.insert('end',str_inputFilePath)
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('设置输入文件为：'+str_inputFilePath)
    def savefile(self,widget):
        str_outFilePath=tk.filedialog.asksaveasfilename()
        if str_outFilePath=='':
            str_outFilePath='按区域抓取POI_result.csv'
        widget.delete(0, 'end')
        widget.insert('end', str_outFilePath)
        self.console.config(state='normal')
        self.console.delete(1.0, 'end')
        self.console.config(state='disable')
        print('设置输出文件为：' + str_outFilePath)

    def t(self):
        print(type(self.tabControl.tab(self.tabControl.select(),'text')))
        print(self.tabControl.tab(self.tabControl.select(),'text'))

    # 打包进线程（耗时的操作）
    # 感恩https://zhuanlan.zhihu.com/p/103334828
    @staticmethod
    def thread_it(func, *args):
        t = Thread(target=func, args=args)
        t.setDaemon(True)  # 守护--就算主界面关闭，线程也会留守后台运行（不对!）
        t.start()  # 启动

#key池窗口
class OSpider_KeyPool(tk.Toplevel):
    def __init__(self,root):
        tk.Toplevel.__init__(self,root)
        self.root=root
        self.title('Key池设置')
        self.geometry('255x165')
        self.resizable(1, 1)
        self.iconbitmap('icon.ico')

        # 选项卡设置key池输入
        self.tabControl = ttk.Notebook(self)
        self.tabControl.grid(row=0, column=0, columnspan=4, sticky='W', padx=10,pady=5)
        tab_Baidu = ttk.Frame(self.tabControl)
        tab_Gaode = ttk.Frame(self.tabControl)
        self.tabControl.add(tab_Baidu, text='百度地图')
        self.tabControl.add(tab_Gaode, text='高德地图')

        tk.Label(tab_Baidu, text='百度地图', width='9', height=1).grid(row=0, column=0)
        self.e_Baidu = tk.Text(tab_Baidu, width=33,height=6)
        self.e_Baidu.grid(row=0, column=0)
        # self.e_protect_Baidu= tk.Entry(self.e_Baidu, width='5')
        tk.Label(tab_Gaode, text='高德地图', width='9', height=1).grid(row=0, column=0)
        self.e_Gaode = tk.Text(tab_Gaode, width=33, height=6)
        self.e_Gaode.grid(row=0, column=0)

        #并发保护设置及应用key池设置按钮
        tk.Label(self,text='并发保护',width='8',height=1).grid(row=1,column=0)
        self.e_protect = tk.Entry(self, width='5')
        self.e_protect.grid(row=1, column=1,sticky='W')
        tk.Button(self,width='4',text='帮助',height=1,command=self.help).grid(row=1, column=2,padx=0,pady=5,sticky='W')
        tk.Button(self, width='9', text='应用设置', height='1', command=self.applyKey).grid(row=1, column=3,padx=0,pady=5,sticky='W')

        #读取所需文件并写入
        try:
            cf = configparser.ConfigParser()
            cf.read('property.ini')
            self.e_Baidu.insert("end", cf.get('Key', 'keyBaidu'))
            self.e_Gaode.insert("end", cf.get('Key', 'keyGaode'))
            self.e_protect.insert("end",cf.get('Key','thread_protect'))
        except Exception as e:
            sys.stderr.write('property.ini文件缺失或错误，虽不影响使用，但会失去参数保存功能\n')
            sys.stderr.write(e)

    def applyKey(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('应用Key池设置..')
        cf = configparser.ConfigParser()
        cf.read('property.ini')
        cf.set('Key', 'keyBaidu', self.e_Baidu.get(1.0,'end'))
        cf.set('Key', 'thread_protect', self.e_protect.get())
        keystr = cf.get('Key', 'keyBaidu').split('\n')[0]
        keylist = list()
        for key in keystr.split(','):
            keylist.append(key)
        print(keylist)
        if 'mgRIjArNHuol074XjsyDPQMu7g22hEjZ' in keylist or 'Zdi4l0k8V41sQqoXdIyZMRDxh3GUzDte' in keylist:
            thread_protect = 1
        else:
            thread_protect = int(cf.get('Key', 'thread_protect'))
        cf.write(open('property.ini', 'w'))
        self.root.spider.set_key(keylist,thread_protect)

    def help(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('---------帮助文档----------')
        print('工具名称：Key池配置')
        print('核心功能：设置Key池和并发保护数，为软件的正常运行提供保障')
        print('--------输入参数说明--------')
        print('百度地图Key:输入百度地图key,key间以英文逗号分隔')
        print('高德地图Key:当前版本尚不支持高德地图Key设置')
        print('并发保护：由于API存在调用频率（并发QPS）的限制，为了不触发key的并发禁用，需要进行并发保护。OSpider通过设置“单个Key最多能被多少个线程同时占有”进行并发保护。并发保护数具体设置为多少应当根据网络状况不同而调整，当网速非常快的时候，并发保护超过3就极有可能超并发，对于未经过认证的key而言，并发保护数大于1就存在并发风险。在未触发Key的并发禁用的前提下，并发保护数越大，程序运行越快。')
        print('----------注意事项---------')
        print('1.OSpider本身提供了2个key:"mgRIjArNHuol074XjsyDPQMu7g22hEjZ"和“Zdi4l0k8V41sQqoXdIyZMRDxh3GUzDte”，如果key池中存在这两个key，并发保护将被一直限制为1')
        print('2.提高程序运行速度的不二良方是大key池，超多线程，并在不触发并用禁用的前提下增大并发保护数')
        print('3.如果并发保护数为1，依然会超并发，则请扩大key池并将线程数设置为一个不大于key池总量的整数')
        self.root.console.see(1.0)

#分城POI总量窗口
class OSpider_CityNum(tk.Toplevel):
    def __init__(self,root):
        tk.Toplevel.__init__(self,root)
        self.root=root
        self.title('分城POI总量')
        self.geometry('300x120')
        self.resizable(1, 1)
        self.iconbitmap('icon.ico')

        # 第一行，查询关键词和POI类型
        tk.Label(self, text='POI名称', width=9, height=1, pady=5).grid(row=0, column=0)
        self.e_query = tk.Entry(self, width=10)
        self.e_query.grid(row=0, column=1, sticky='W')

        tk.Label(self, text='POI类型', width=9, height=1, pady=8).grid(row=0, column=2)
        self.e_tag = tk.Entry(self, width=10)
        self.e_tag.grid(row=0, column=3, sticky='W')


        # 第二行，文件保存路径设置
        tk.Label(self, text='输出文件', width=9, height=1).grid(row=1, column=0)
        self.e_outFilePath = tk.Entry(self, width='20')
        self.e_outFilePath.grid(row=1, column=1, columnspan=2)
        tk.Button(self, width='7', text='浏览', height='1', command=lambda: self.savefile(self.e_outFilePath)).grid(row=1,column=3,padx=3,pady=5)

        # 第三行，帮助和执行
        tk.Button(self,width='5',text='帮助',height=1,command=self.help).grid(row=2, column=0,padx=0,pady=5)
        tk.Button(self, width='29', text='执行', height='1', command=lambda: self.thread_it(self.run)).grid(row=2, column=1,columnspan=3,padx=0,pady=5,sticky='W')
        #读取所需文件并写入
        try:
            cf = configparser.ConfigParser()
            cf.read('property.ini')
            self.e_query.insert("end", cf.get('CityNum', 'query'))
            self.e_tag.insert("end", cf.get('CityNum', 'tag'))
            self.e_outFilePath.insert("end",cf.get('CityNum','outfilepath'))
        except Exception as e:
            sys.stderr.write('property.ini文件缺失或错误，虽不影响使用，但会失去参数保存功能\n')
            sys.stderr.write(e)

    def run(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('执行分城POI总量')
        cf = configparser.ConfigParser()
        cf.read('property.ini')
        cf.set('CityNum', 'query', self.e_query.get())
        cf.set('CityNum', 'tag', self.e_tag.get())
        cf.set('CityNum', 'outfilepath', self.e_outFilePath.get())
        cf.write(open('property.ini', 'w'))
        query = self.e_query.get()
        tag = self.e_tag.get()
        outFilePath = self.e_outFilePath.get()
        df=self.root.spider.getPOI_CityNum(query,tag)
        if type(df)==type(pd.DataFrame()):
            df.to_csv(outFilePath,encoding='utf-8-sig')
            print('成功，结果已保存至：'+outFilePath)
        else:
            print('看起来像失败了的样子！')

    def savefile(self,widget):
        str_outFilePath=tk.filedialog.asksaveasfilename()
        if str_outFilePath=='':
            str_outFilePath='分城POI总量_result.csv'
        widget.delete(0, 'end')
        widget.insert('end', str_outFilePath)
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('设置输出文件为：' + str_outFilePath)

    def help(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('---------帮助文档----------')
        print('工具名称：分城POI总量')
        print('核心功能：用于抓取除港澳台外国内所有地级及地级以上城市的指定POI数量并输出csv格式文件。适用于宏观研究(把各城市的POI量作为指标)。')
        print('--------输入参数说明--------')
        print('POI名称：查询关键词，如“酒吧”，“联想售后”；')
        print('POI类型：POI分类标识，如”美食”、“中餐厅”，可以通过工具->POI类型表查询支持的POI类型。当为空时，不进行类型限制。')
        print('输出文件：结果文件的保存路径，仅支持输出为csv，txt')
        print('--------结果文件说明--------')
        print('输出文件中将存储省市区名及指定POI的总量')
        print('----------注意事项---------')
        print('当前版本该功能基于百度Place API，暂不支持其他数据源')
        self.root.console.see(1.0)

    @staticmethod
    def thread_it(func, *args):
        t = Thread(target=func, args=args)
        t.setDaemon(True)  # 守护--就算主界面关闭，线程也会留守后台运行（不对!）
        t.start()  # 启动

#批量抓取POI窗口
class OSpider_POIBatch(tk.Toplevel):
    def __init__(self,root):
        tk.Toplevel.__init__(self,root)
        self.root=root
        self.title('批量抓取POI')
        self.geometry('285x85')
        self.resizable(1, 1)
        self.iconbitmap('icon.ico')

        # 第一行，批处理文件设置
        tk.Label(self, text='批处理文件', width=9, height=1).grid(row=1, column=0)
        self.e_batchPath = tk.Entry(self, width='20')
        self.e_batchPath.grid(row=1, column=1, columnspan=2)
        tk.Button(self, width='7', text='浏览', height='1', command=lambda: self.openfile(self.e_batchPath)).grid(row=1,column=3,padx=3,pady=5)

        # 第二行，帮助和执行
        tk.Button(self,width='7',text='帮助',height=1,command=self.help).grid(row=2, column=0,padx=0,pady=5)
        tk.Button(self, width='7', text='执行', height='1', command=lambda: self.thread_it(self.run)).grid(row=2, column=1,padx=0,pady=5)
        tk.Button(self, width='7', text='状态', height=1, command=self.disp).grid(row=2, column=2, padx=0, pady=5)
        tk.Button(self, width='7', text='中止', height=1, command=self.kill).grid(row=2, column=3, padx=0, pady=5)
        #读取所需文件并写入
        try:
            cf = configparser.ConfigParser()
            cf.read('property.ini')
            self.e_batchPath.insert("end",cf.get('POIbatch','inputfilepath'))
        except Exception as e:
            sys.stderr.write('property.ini文件缺失或错误，虽不影响使用，但会失去参数保存功能\n')
            sys.stderr.write(e)
    def show_batch(self):
        if (not self.root.spider.qKey.empty()) and (not self.root.spider.qTask.empty()):
            print('###批量抓取POI中,批处理剩余任务数：'+str(self.root.qTask.qsize())+'...')
            global timer
            timer=Timer(3,self.show_batch)
            timer.start()
    def kill(self):
        self.root.spider.qTask.queue.clear()
        sys.stderr.write('批处理任务强行中止\n')
    def disp(self):
        num=self.root.spider.qTask.qsize()
        print('批处理任务剩余量：'+str(num))
    def run(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('执行批量抓取POI')
        cf = configparser.ConfigParser()
        cf.read('property.ini')
        cf.set('POIbatch', 'inputfilepath', self.e_batchPath.get())
        cf.write(open('property.ini', 'w'))
        batchPath = self.e_batchPath.get()
        self.root.spider.getPOI_byBatch(batchPath)

    def openfile(self,widget):
        str_inputFilePath=tk.filedialog.askopenfilename()
        widget.delete(0,'end')
        widget.insert('end',str_inputFilePath)
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('设置批处理文件为：'+str_inputFilePath)

    def help(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('---------帮助文档----------')
        print('工具名称：批量抓取POI')
        print('核心功能：利用批处理文件批量抓取POI。')
        print('--------输入参数说明--------')
        print('POI名称：查询关键词，如“酒吧”，“联想售后”；')
        print('POI类型：POI分类标识，如”美食”、“中餐厅”，可以通过工具->POI类型表查询支持的POI类型。当为空时，不进行类型限制。')
        print('批出处理文件：用来设定批处理任务队列的批处理文件，csv格式，以下为样例')
        print('id,query,tag,region,grid_num,threshold,thread_num,outFilePath')
        print('1,KTV,,https://geo.datav.aliyun.com/areas_v2/bound/350100.json,6,100,3,C:\福州市_KTV.csv')
        print('2,高中,中学,118.351915;29.192178;120.724682;30.569969,6,100,3,C:\西安外接矩形_高中.shp')
        print('3,咖啡厅,,121.480248;31.236276;3000,6,100,3,C:\上海市政府周边3km_咖啡厅.json')
        print('4,酒吧,酒吧,广州,6,100,3,C:\广州市_酒吧.txt')
        print('----------注意事项---------')
        print('1.批处理文件region列内部的分隔符为英文分号而不是逗号！！！')
        print('2.批处理文件各列的定义参考主界面帮助选项，其中region可为行政区划名称，矩形框，圆形或自定义面文件')
        print('3.如果批处理任务中途失败或终止，会将未完成抓取的任务保存为批处理文件目录下的”批处理文件名_cover.csv“，从而实现断点续传')
        print('4.由于Timer在GUI中无效，手动设置了“状态”按钮，点击状态按钮可以查看当前批处理队列还有多少任务')
        print('5.如果想中止批处理，点击“中止”按钮即可，程序会在完成正在处理的抓取任务后终止')

        self.root.console.see(1.0)

    @staticmethod
    def thread_it(func, *args):
        t = Thread(target=func, args=args)
        t.setDaemon(True)  # 守护--就算主界面关闭，线程也会留守后台运行（不对!）
        t.start()  # 启动

#坐标转换窗口
class OSpider_CoordTrans(tk.Toplevel):
    def __init__(self,root):
        tk.Toplevel.__init__(self,root)
        self.root=root
        self.title('坐标转换工具')
        self.geometry('370x255')
        self.resizable(1, 1)
        self.iconbitmap('icon.ico')

        # 第一行，标题栏
        tk.Label(self, text='输入栏/坐标系', width=24, height=1).grid(row=0, column=0,columnspan=2)
        tk.Label(self, text='输入栏/坐标系', width=24, height=1).grid(row=0, column=2, columnspan=2)
        # 第二行，输入框
        self.input=tk.Text(self,width='24',height=6)
        self.input.grid(row=1,column=0,columnspan=2)
        self.output = tk.Text(self, width='24', height=6)
        self.output.grid(row=1, column=2, columnspan=2)
        # 第三行，坐标系与少量转换按钮
        self.cmb_origin_crs = ttk.Combobox(self, width=6)
        self.cmb_origin_crs['value'] = (['BD09', 'GCJ02','WGS84'])
        self.cmb_origin_crs.current(0)
        self.cmb_origin_crs.grid(row=2,column=0)
        tk.Button(self, width='30', text='少量转换', height='1', command=lambda: self.thread_it(self.trans)).grid(row=2, column=1,columnspan=2,padx=2,pady=3)
        self.cmb_target_crs = ttk.Combobox(self, width=6)
        self.cmb_target_crs['value'] = (['BD09', 'GCJ02', 'WGS84'])
        self.cmb_target_crs.current(2)
        self.cmb_target_crs.grid(row=2, column=3)
        #第四行 输入文件
        tk.Label(self, text='输入文件', width='8', height=1).grid(row=3, column=0)
        self.e_inputFile = tk.Entry(self, width='30')
        self.e_inputFile.grid(row=3, column=1,columnspan=2)
        tk.Button(self, width='8', text='浏览', height='1', command=lambda: self.openfile(self.e_inputFile)).grid(row=3, column=3, padx=0, pady=3)
        #第五行，输出文件
        tk.Label(self, text='输出文件', width='8', height=1).grid(row=4, column=0)
        self.e_outputFile = tk.Entry(self, width='30')
        self.e_outputFile.grid(row=4, column=1, columnspan=2)
        tk.Button(self, width='8', text='浏览', height='1', command=lambda: self.savefile(self.e_outputFile)).grid(row=4,column=3,padx=0,pady=3)
        #第六行，帮助与执行
        tk.Button(self, width='8', text='帮助', height='1', command=self.help).grid(row=5, column=0, pady=3,padx=4)
        tk.Button(self, width='40', text='执行', height='1',command=lambda: self.thread_it(self.run)).grid(row=5, column=1, columnspan=3, pady=3)

        #读取所需文件并写入
        try:
            cf = configparser.ConfigParser()
            cf.read('property.ini')
            self.input.insert("end",cf.get('CoordTrans','inputlist'))
            self.e_inputFile.insert("end", cf.get('CoordTrans', 'inputfilepath'))
            self.e_outputFile.insert("end", cf.get('CoordTrans', 'outfilepath'))
        except Exception as e:
            sys.stderr.write('property.ini文件缺失或错误，虽不影响使用，但会失去参数保存功能\n')
            sys.stderr.write(e)


    def trans(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        self.output.delete(1.0,'end')
        print('执行少量坐标转换...')
        cf = configparser.ConfigParser()
        cf.read('property.ini')
        cf.set('CoordTrans', 'inputlist', self.input.get(1.0,'end'))
        cf.write(open('property.ini', 'w'))
        inputstr=self.input.get(1.0,'end')
        inputlist=inputstr.split()
        lng=list()
        lat=list()
        for coor in inputlist:
            lng.append(float(coor.split(',')[0]))
            lat.append(float(coor.split(',')[1]))
        origin_crs=self.cmb_origin_crs.get()
        target_crs=self.cmb_target_crs.get()
        print(origin_crs+'->'+target_crs)
        outlng,outlat=coord.coordtrans(lng,lat,origin_crs,target_crs)
        n=len(outlng)
        outstr=''
        for i in range(n-1):
            outstr+=str(outlng[i])+','+str(outlat[i])+'\n'
        outstr+=str(outlng[n-1])+','+str(outlat[i])
        self.output.insert(1.0,outstr)
        print('少量坐标转换完成！')

    def run(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('执行批量坐标转换...')
        cf = configparser.ConfigParser()
        cf.read('property.ini')
        cf.set('CoordTrans', 'inputfilepath', self.e_inputFile.get())
        cf.set('CoordTrans', 'outfilepath', self.e_outputFile.get())
        cf.write(open('property.ini', 'w'))
        origin_crs = self.cmb_origin_crs.get()
        target_crs = self.cmb_target_crs.get()
        inputFilePath=self.e_inputFile.get()
        outFilePath=self.e_outputFile.get()
        coord.coordtrans_byFile(inputFilePath,outFilePath,origin_crs,target_crs)


    def savefile(self,widget):
        str_outFilePath=tk.filedialog.asksaveasfilename()
        if str_outFilePath=='':
            str_outFilePath='坐标转换_result.csv'
        widget.delete(0, 'end')
        widget.insert('end', str_outFilePath)
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('设置输出文件为：' + str_outFilePath)

    def openfile(self,widget):
        str_inputFilePath=tk.filedialog.askopenfilename()
        widget.delete(0,'end')
        widget.insert('end',str_inputFilePath)
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('设置批处理文件为：'+str_inputFilePath)

    def help(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('---------帮助文档----------')
        print('工具名称：坐标转换工具')
        print('核心功能：少量或基于文件批量进行BD09/GCJ02/WGS84坐标互转。')
        print('--------参数说明--------')
        print('少量坐标输入栏：经度,纬度 每行表示一个点')
        print('左侧下拉框：输入栏/或输入文件的坐标系')
        print('右侧下拉框：输出栏/及输出文件希望包含的坐标系')
        print('WGS84:wgs84坐标系，GPS及谷歌地图所使用的坐标系，无加密，常用')
        print('GCJ02:gcj02坐标系，又称火星坐标系，由国测局对WGS84坐标进行加密得到，高德地图使用该坐标系')
        print('BD09:bd09坐标系，百度地图使用的坐标系，对GCJ02二次加密获得')
        print('输入文件：批量转换的输入csv文件，包括id,lng,lat三个必须列。输入文件中允许包含其他用户自定义列，这些列将在输出文件中得到保留')
        print('输出文件：批量转换结果保存文件（仅支持txt,csv)，必定包含id，及原始和转换后的经纬度5列，如果输入文件中存在用户自定义列，这些列将在结果中得到保留')
        print('----------注意事项---------')
        print('没啥需要特别注意的，有bug联系我哟')
        self.root.console.see(1.0)

    @staticmethod
    def thread_it(func, *args):
        t = Thread(target=func, args=args)
        t.setDaemon(True)  # 守护--就算主界面关闭，线程也会留守后台运行（不对!）
        t.start()  # 启动

#地址解析窗口
class OSpider_Geocoder(tk.Toplevel):
    def __init__(self,root):
        tk.Toplevel.__init__(self,root)
        self.root=root
        self.title('地址解析工具')
        self.geometry('370x140')
        self.resizable(1, 1)
        self.iconbitmap('icon.ico')

        tk.Label(self, text='百度Key', width='8', height=1).grid(row=2, column=0)
        self.e_key = tk.Entry(self, width='40')
        self.e_key.grid(row=2,column=1,columnspan=3,pady=5)
        #第四行 输入文件
        tk.Label(self, text='输入文件', width='8', height=1).grid(row=3, column=0)
        self.e_inputFile = tk.Entry(self, width='30')
        self.e_inputFile.grid(row=3, column=1,columnspan=2)
        tk.Button(self, width='8', text='浏览', height='1', command=lambda: self.openfile(self.e_inputFile)).grid(row=3, column=3, padx=0, pady=3)
        #第五行，输出文件
        tk.Label(self, text='输出目录', width='8', height=1).grid(row=4, column=0)
        self.e_outputDir = tk.Entry(self, width='30')
        self.e_outputDir.grid(row=4, column=1, columnspan=2)
        tk.Button(self, width='8', text='浏览', height='1', command=lambda: self.savedir(self.e_outputDir)).grid(row=4,column=3,padx=0,pady=3)
        #第六行，帮助与执行
        tk.Button(self, width='8', text='帮助', height='1', command=self.help).grid(row=5, column=0, pady=3,padx=4)
        tk.Button(self, width='40', text='执行', height='1',command=lambda: self.thread_it(self.run)).grid(row=5, column=1, columnspan=3, pady=3)

        #读取所需文件并写入
        try:
            cf = configparser.ConfigParser()
            cf.read('property.ini')
            self.e_key.insert("end", cf.get('Geocoder', 'key'))
            self.e_inputFile.insert("end", cf.get('Geocoder', 'inputfilepath'))
            self.e_outputDir.insert("end", cf.get('Geocoder', 'outdirpath'))
        except Exception as e:
            sys.stderr.write('property.ini文件缺失或错误，虽不影响使用，但会失去参数保存功能\n')
            sys.stderr.write(e)

    def run(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('执行地址解析工具...')
        cf = configparser.ConfigParser()
        cf.read('property.ini')
        cf.set('Geocoder','key',self.e_key.get())
        cf.set('Geocoder', 'inputfilepath', self.e_inputFile.get())
        cf.set('Geocoder', 'outdirpath', self.e_outputDir.get())
        cf.write(open('property.ini', 'w'))
        key=self.e_key.get()
        inputFilePath=self.e_inputFile.get()
        outDirPath=self.e_outputDir.get()
        coder.Geocoder(key,inputFilePath,outDirPath)

    def savedir(self,widget):
        str_outputDirPath = tk.filedialog.askdirectory()
        if str_outputDirPath=='':
            str_outputDirPath='D:/'
        widget.delete(0, 'end')
        widget.insert('end', str_outputDirPath)
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('设置输出目录为：' + str_outputDirPath)

    def openfile(self,widget):
        str_inputFilePath=tk.filedialog.askopenfilename()
        widget.delete(0,'end')
        widget.insert('end',str_inputFilePath)
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('设置批处理文件为：'+str_inputFilePath)

    def help(self):
        self.root.console.config(state='normal')
        self.root.console.delete(1.0, 'end')
        self.root.console.config(state='disable')
        print('---------帮助文档----------')
        print('工具名称：地址解析工具')
        print('核心功能：根据文件输入，将地址解析为坐标')
        print('--------输入参数说明--------')
        print('输入文件：必须严格遵循Demo文件格式')
        print('输出目录：这里选目录就好，输出文件自动保存为该目录下的“输入文件名+地址解析结果.csv“')
        print('--------输入文件解释--------')
        print('id:地址索引，必要项')
        print('city:地址所在城市，如指定，则优先在指定城市内部解析，该值也可为空')
        print('address：地址，可为结构化的也可为非结构化的，POI具体名称也可以')
        print('--------输出文件解释--------')
        print('结果包含wgs84和bd09两套坐标系')
        print('status:0成功，非0失败')
        print('precise:位置的附加信息，是否精确查找。1为精确查找，即准确打点；0为不精确，即模糊打点。')
        print('confidence：描述打点绝对精度（即坐标点的误差范围),>80-误差小于100m,>60-吴超小于500m。')
        print('comprehension：描述地址理解程度。分值范围0-100，分值越大，服务对地址理解程度越高（建议以该字段作为解析结果判断标准）。')
        print('comprehension=100，解析误差100m内概率为91%，误差500m内概率为96%；')
        print('comprehension≥90，解析误差100m内概率为89%，误差500m内概率为96%；')
        print('comprehension≥80，解析误差100m内概率为88%，误差500m内概率为95%；')
        print('comprehension≥70，解析误差100m内概率为84%，误差500m内概率为93%；')
        print('comprehension≥60，解析误差100m内概率为81%，误差500m内概率为91%；')
        print('comprehension≥50，解析误差100m内概率为79%，误差500m内概率为90%；')
        print('----------注意事项---------')
        print('作者写这个功能偷懒了,依然是单线程单Key，用户有强烈需求才会改')
        self.root.console.see(1.0)

    @staticmethod
    def thread_it(func, *args):
        t = Thread(target=func, args=args)
        t.setDaemon(True)  # 守护--就算主界面关闭，线程也会留守后台运行（不对!）
        t.start()  # 启动

app = OSpider_Main()
app.mainloop()