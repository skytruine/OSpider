# -*- coding:utf-8 -*-
import geopandas as gpd
import pandas as pd
import numpy as np
import requests
from threading import Thread
from threading import Timer
from queue import Queue
import json
import sys
import time
import os
import CoordTrans as coord
import ADSpider as ad
from shapely.geometry import Point,Polygon


#把显示弄成定时的也许效果会更好，又或者
class BaiduPOISpider():
    def __init__(self):
        #qA用辅助抓取区域的解析，qUrls用来存用于抓数据的url,qResults用于存临时结果tuple，完成运行后它们都将清空
        self.qAnalysis=Queue()
        self.qUrls=Queue()
        self.qResults=Queue()
        #抓取必要参数，直接在核心抓取函数中设置，query是POI关键词,tag是POI类型，region是抓取区域（geopandas中的GeoDataFrame类型）
        self.query = ''
        self.tag=''
        self.region=gpd.GeoDataFrame()
        #抓取参数，包括初始网格数grid_num（影响抓取精度）和线程数thread_num（影响抓取速度）
        self.grid_num=6
        self.thread_num=2
        self.thread_protect=2
        #key池，采用队列的形式，通过get,put形成使用上的循环和弹出无效key
        self.qKey=Queue()
        #Task队列，用于辅助POI抓取批处理功能
        self.qTask=Queue()
        #是否要显示过程信息
        self.dispStatus=True
        #为了增加交互友好性，设置一下key的使用量
        # self.keyuse=0
        #用全局的keyuse做基础存在隐患，要用也应该是用队列，懒得计数了
        #目前百度地图Place API虽然返回上限是400个POI但实际上即便有400，也会进行抽稀，因此进行四分的时候应该设置一个小于该值的量，GUI的版本我默认设置为100
        self.threshold=100
    def set_threshold(self,threshold):
        self.threshold=threshold
    def disp(self,str):
        if self.dispStatus:
            print(str)
    def set_dispStatus(self,status):
        self.dispStatus=status
    def set_env(self, grid_num: int, threshold=100,thread_num=2) -> None:
        self.grid_num=grid_num
        self.thread_num=thread_num
        self.threshold=threshold

    def set_key(self, keylist: list,thread_protect=2) -> None:
        #通过thread_protect倍增key池，从而控制单个key最多能被多少个线程同时使用，进而达到并发保护的目的
        self.qKey.queue.clear()
        self.thread_protect = thread_protect
        for _ in range(self.thread_protect):
            for key in keylist:
                self.qKey.put(key)
    #内部用于显示的函数
    def show_analysis(self):
        while not self.qAnalysis.empty():
            self.disp('分析切片中，队列剩余：'+str(self.qAnalysis.qsize()))
            time.sleep(0.5)
    def show_grab(self):
        while not self.qUrls.empty():
            self.disp('抓取POI中，剩余URL：'+str(self.qUrls.qsize()))
            time.sleep(0.5)
    def show_batch(self):
        if (not self.qKey.empty()) and (not self.qTask.empty()):
            print('###批量抓取POI中,批处理剩余任务数：'+str(self.qTask.qsize())+'...')
            global timer
            timer=Timer(3,self.show_batch)
            timer.start()
    #丢弃指定的key，要删的key不在里面，实际上就相当于循环了一遍而已，无影响
    def drop_key(self,key):
        for _ in range(self.qKey.qsize()):
            t = self.qKey.get()
            if t != key:
                self.qKey.put(t)
    def set_grab(self,query,tag,region):
        self.query=query
        self.tag=tag
        #这里全部转为了WGS84的坐标，所以输入的geodataframe是什么坐标系并不重要
        self.region=region.to_crs(epsg=4326)
    def get_paras(self):
        return {'query':self.query,'tag':self.tag,'region':self.region,'grid_num':self.grid_num,'thread_num':self.thread_num,'key':self.qKey}
    #由produce_urls调用的url中POI计数函数
    #如果返回为-1的话，意味着存在边界效应，需要进一步分割;如果为-99则说明key失效
    def countPOI(self,query: str, tag: str, down: float, left: float, up: float, right: float, key: str) -> int:
        url = 'http://api.map.baidu.com/place/v2/search?query=' + query + '&tag=' + tag + '&bounds=' \
              + str(down) + ',' + str(left) + ',' + str(up) + ',' + str(right) \
              + '&page_size=20&page_num=0&output=json&ak=' + key
        try:
            response = requests.get(url)
            data = json.loads(response.text)
        except Exception:
            try: #这个地方的双重try-except结构是为了当访问不稳定时，给失败的访问多一次机会，
                if not self.qKey.empty(): #这种写法隐藏了一个bug，当一个key失效的时候，可能drop掉另一个key，但是这种情况发生概率很小，在不确定访问稳定性是否由key造成时不失为一种不错方式
                    tkey=self.qKey.get()
                    url=url.split('ak=')[0]+'ak='+tkey
                    response = requests.get(url)
                    data = json.loads(response.text)
                    self.qKey.put(tkey)
                else:
                    response = requests.get(url)
                    data = json.loads(response.text)
            except Exception:
                sys.stderr.write('线程解析异常，请手动处理异常url：' + url+'\n')
                return 0
        # response = requests.get(url)
        # data = json.loads(response.text)
        if data['status']!=0:
            return -99
        elif data['total']!=0 and ('location' not in data['results'][0]):
            return -1
        else:
            return data['total']
    #基本解析线程函数，进一步调用countPOI
    def produce_urls(self):
        while (not self.qAnalysis.empty()) and (not self.qKey.empty()):
            bounds=self.qAnalysis.get()
            left = bounds[0]
            down = bounds[1]
            right = bounds[2]
            up = bounds[3]
            # 单区域抓取限制为400
            #这里用while循环是为了防止key失效，主要失效的情况就是超限
            poi_cnt = -99 #-99是因为解析的时候key失效，出现抓取bug应该直接返回0
            while (not self.qKey.empty()) and poi_cnt == -99:
                key = self.qKey.get()
                poi_cnt = self.countPOI(self.query, self.tag, down, left, up, right, key)
                if poi_cnt == -99:
                    self.drop_key(key)
                    sys.stderr.write('Key:' + key + '失效\n')
                else:
                    self.qKey.put(key)

            if poi_cnt>0 and poi_cnt<self.threshold: #如果介于1-399，则可以直接抓取，添加即可
                num = int(poi_cnt / 20)
                for page_num in range(num + 1):
                    turl = 'http://api.map.baidu.com/place/v2/search?query=' + self.query + '&tag=' + self.tag + '&bounds=' \
                          + str(down) + ',' + str(left) + ',' + str(up) + ',' + str(right) \
                          + '&page_size=20&page_num=' + str(page_num) + '&scope=2&output=json&ak='
                    self.qUrls.put(turl)
            #如果为-1或者400的话需要进一步四分，-1四分是为了处理边界效应，400则是为了获得更精确的数据
            elif poi_cnt==-1 or poi_cnt>=self.threshold:
                height = (up - down) / 2
                width = (right - left) / 2
                for i in range(2):
                    for j in range(2):
                        left2 = left + i * width
                        down2 = down + j * height
                        right2 = left2 + width
                        up2 = down2 + height
                        self.qAnalysis.put((left2,down2,right2,up2))
            # print('POI分析线程' + name + '-当前完成解析url数量：' + str(self.qUrls.qsize()))
    #单url实际抓取函数,由grab_urls调用
    def getPOI(self,url):
        try:
            response = requests.get(url)
            data = json.loads(response.text)
        except Exception:
            try: #这个地方的双重try-except结构是为了当访问不稳定时，给失败的访问多一次机会，
                if not self.qKey.empty(): #这种写法隐藏了一个bug，当一个key失效的时候，可能drop掉另一个key，但是这种情况发生概率很小，在不确定访问稳定性是否由key造成时不失为一种不错方式
                    tkey=self.qKey.get()
                    url=url.split('ak=')[0]+'ak='+tkey
                    response = requests.get(url)
                    data = json.loads(response.text)
                    self.qKey.put(tkey)
                else:
                    response = requests.get(url)
                    data = json.loads(response.text)
            except Exception:
                sys.stderr.write('线程抓取异常，请手动处理异常url：' + url+'\n')
                return 0
        response = requests.get(url)
        data = json.loads(response.text)
        poi_list = list()
        if data['status'] == 0:
            for item in data['results']:
                name=''
                if 'name' in item:
                    name = item['name']
                if 'location' in item:
                    bd09_lng = item['location']['lng']
                    bd09_lat = item['location']['lat']
                else:
                    bd09_lng=121.2141248
                    bd09_lat=30.45124567
                wgs84_lng = coord.bd09_to_wgs84(np.array([bd09_lng]), np.array([bd09_lat]))[0][0]
                wgs84_lat = coord.bd09_to_wgs84(np.array([bd09_lng]), np.array([bd09_lat]))[1][0]
                address=''
                if 'address' in item:
                    address = item['address']
                key1 = 'province'
                key2 = 'city'
                key3 = 'area'
                if key1 in item:
                    province = item['province']
                else:
                    province = ''
                if key2 in item:
                    city = item['city']
                else:
                    city = ''
                if key3 in item:
                    area = item['area']
                else:
                    area = ''
                tag = ''
                if 'detail_info' in item:
                    if 'tag' in item['detail_info']:
                        tag = item['detail_info']['tag']
                poi_list.append((name,address,province,city,area,tag,wgs84_lng,wgs84_lat,bd09_lng,bd09_lat))
            return poi_list
        else:
            return None
    #基本抓取线程函数，进一步调用getPOI
    def grab_urls(self):
        while (not self.qUrls.empty()) and (not self.qKey.empty()):
            url = self.qUrls.get()
            tpoi_list=None
            while tpoi_list==None and (not self.qKey.empty()):
                key=self.qKey.get()
                tpoi_list=self.getPOI(url+key)
                if tpoi_list==None:
                    # 当前的key无效，删掉它
                    self.drop_key(key)
                    sys.stderr.write('Key:' + key + '失效\n')
                else:
                    for poi in tpoi_list:
                        self.qResults.put(poi)
                    self.qKey.put(key)
            # print('POI抓取线程' + name + '-当前POI数量：' + str(self.qResults.qsize()))
    def run(self):
        self.qAnalysis.queue.clear()
        self.qUrls.queue.clear()
        self.qResults.queue.clear()
        envolope=self.region.total_bounds
        tlng,tlat=coord.wgs84_to_bd09(np.array([envolope[0],envolope[2]]),np.array([envolope[1],envolope[3]]))
        left=tlng[0]
        down=tlat[0]
        right=tlng[1]
        up=tlat[1]
        height = (up - down) / self.grid_num
        width = (right - left) / self.grid_num
        for i in range(self.grid_num):
            for j in range(self.grid_num):
                left2 = left + i * width
                down2 = down + j * height
                right2 = left2 + width
                up2 = down2 + height
                self.qAnalysis.put((left2,down2,right2,up2))
        self.disp('开启多线程POI抓取任务...')
        self.disp('正在执行切片分析...')
        #多线程进行url解析
        t1=time.time()
        ths = []
        for _ in range(self.thread_num):
            th = Thread(target=self.produce_urls)
            th.start()
            ths.append(th)
        th=Thread(target=self.show_analysis)
        th.start()
        ths.append(th)
        for _ in ths:
            _.join()
        if self.qKey.empty():
            sys.stderr.write('Key耗尽，请重置Key池后重新尝试...\n')
            return None
        self.disp('切片分析执行完毕...')
        #阶段性输出
        #多线程进行url抓取
        self.disp('正在执行POI抓取...')
        ths = []
        for _ in range(self.thread_num):
            th = Thread(target=self.grab_urls)
            th.start()
            ths.append(th)
        th=Thread(target=self.show_grab)
        th.start()
        ths.append(th)
        for _ in ths:
            _.join()
        if self.qKey.empty():
            sys.stderr.write('Key耗尽，请重置Key池后再尝试...\n')
            return None
        self.disp('外接矩形内POI抓取完毕,共有' + str(self.qResults.qsize()) + '个')
        t2=time.time()
        self.disp('抓取POI共消耗'+str(t2-t1)+'s')
        self.disp('正在提取区域内的POI...')
        df = pd.DataFrame(columns=['name', 'address', 'province', 'city', 'area', 'tag', 'wgs84_lng', 'wgs84_lat', 'bd09_lng','bd09_lat'])
        i=0
        while not self.qResults.empty():
            df.loc[i]=self.qResults.get()
            i=i+1
        #构造WGS84坐标系的GeoDataFrame选取region中的点结果
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.wgs84_lng, df.wgs84_lat),crs=4326)
        #这样做空间选择效率很低，暂时没有特别好的方法
        self.region['dummy']='dummy'
        geom = self.region.dissolve(by='dummy').geometry[0]
        gdf=gdf[gdf.intersects(geom)]
        self.disp('提取完成,区域内共有指定POI：' + str(gdf.shape[0])+'个')
        self.disp('多线程POI抓取任务执行完毕')
        return gdf
    #按行政区名称获取POI
    def getPOI_byAD(self,query,tag,ADname,grid_num=6,threshold=100,thread_num=2):
        self.disp('----------OSpider-----------------------------------------')
        if type(tag)!=type(''):
            tag=''
        self.disp('按行政区抓取任务：(' + query + ',' + tag + ',' + ADname + ')启动：')
        self.disp('正在查询行政区边界...')
        ads=ad.ChinaADSpider()
        region=ads.getAD_byName(ADname)
        self.disp('已获取行政区边界...')
        self.set_grab(query,tag,region)
        self.set_env(grid_num,threshold,thread_num)
        gdf=self.run()
        if type(gdf)!=type(gpd.GeoDataFrame()):
            sys.stderr.write('按行政区抓取任务：('+query+','+tag+','+ADname+')失败！\n')
            return None
        else:
            return gdf
    #按照矩形框获取POI,注意当前输入坐标使用的是BD09
    def getPOI_byBounds(self, query, tag, left, down, right,up, grid_num=6, threshold=100,thread_num=2):
        self.disp('----------OSpider-----------------------------------------')
        if type(tag)!=type(''):
            tag=''
        self.disp(
            '按矩形框抓取任务：(' + query + ',' + tag + ',' + str(left) + ',' + str(down) + ',' + str(right) + ',' + str(up)  + ')启动：')
        lng,lat=coord.bd09_to_wgs84([left,right],[down,up])
        bounds=Polygon([(lng[0],lat[0]),(lng[0],lat[1]),(lng[1],lat[1]),(lng[1],lat[0])])
        region = gpd.GeoDataFrame(geometry=gpd.GeoSeries([bounds]),crs=4326)
        self.set_grab(query, tag, region)
        self.set_env(grid_num,threshold,thread_num)
        gdf = self.run()
        if type(gdf)!=type(gpd.GeoDataFrame()):
            sys.stderr.write('按矩形框抓取任务：(' + query + ',' + tag + ','  + str(left) + ',' + str(down) + ',' + str(right) + ',' + str(up)  + ')失败！\n')
            return None
        else:
            return gdf

    def getPOI_byCircle(self,query,tag,lng,lat,r,grid_num=6,threshold=100,thread_num=2):
        self.disp('----------OSpider-----------------------------------------')
        if type(tag)!=type(''):
            tag=''
        self.disp('按圆形抓取任务：(' + query + ',' + tag + ',' + str(lng) + ',' + str(lat) + ',' + str(r) + ')启动：')
        lng,lat=coord.bd09_to_wgs84([lng],[lat])
        region = gpd.GeoDataFrame(geometry=gpd.GeoSeries([Point(lng[0], lat[0])]), crs=4326)
        region=region.to_crs(epsg=3857)#转化为横轴墨卡托投影，方便根据半径创建缓冲区
        region=gpd.GeoDataFrame(geometry=region.buffer(r))
        self.set_grab(query, tag, region)
        self.set_env(grid_num,threshold,thread_num)
        gdf = self.run()
        if type(gdf)!=type(gpd.GeoDataFrame()):
            sys.stderr.write('按圆形抓取任务：(' + query + ',' + tag + ',' + str(lng) + ',' + str(lat) + ',' + str(r)  + ')失败！\n')
            return None
        else:
            return gdf

    def getPOI_byFile(self,query,tag,filePath,grid_num=6,threshold=100,thread_num=2):
        self.disp('----------OSpider-----------------------------------------')
        if type(tag)!=type(''):
            tag=''
        self.disp('自定义文件抓取任务：(' + query + ',' + tag + ',' + filePath + ')启动：')
        self.disp('读取抓取区域中...')
        region=gpd.read_file(filePath)
        self.disp('抓取区域读取完毕...')
        self.set_grab(query, tag, region)
        self.set_env(grid_num,threshold,thread_num)
        gdf = self.run()
        if type(gdf)!=type(gpd.GeoDataFrame()):
            sys.stderr.write('按距离抓取任务：(' + query + ',' + tag + ',' + str(filePath) + ')失败！\n')
            return None
        else:
            self.disp('自定义文件抓取任务：(' + query + ',' + tag + ',' + str(filePath) + ')完成！')
            return gdf
    #获取国内除港澳台外所有城市指定POI的总量
    def getPOI_CityNum(self,query,tag=''):
        #用循环key还是单key?我倾向于使用循环key，
        #总共才三十几个url,找一个key就足够了。
        t1=time.time()
        self.qResults.queue.clear()
        provValues = ['河北省', '山西省', '辽宁省', '吉林省', '黑龙江省', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省', '湖南省',
                      '广东省', '海南省', '四川省', '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '内蒙古自治区', '广西壮族自治区', '西藏自治区', '宁夏回族自治区',
                      '新疆维吾尔自治区']
        spcityValues = ['北京市', '上海市', '天津市', '重庆市']
        status=1
        self.disp('分析直辖市中....')
        while (not self.qKey.empty()) and status!=0:
            key=self.qKey.get()
            url = 'http://api.map.baidu.com/place/v2/search?query=' + query + '&tag=' + tag + '&region=全国&output=json&ak=' + key
            response = requests.get(url)
            data = json.loads(response.text)
            status=data['status']
            if status==0:
                for item in data['results']:
                    if item['name'] in spcityValues:
                        self.qResults.put((item['name'],item['name'],item['num']))
                        self.qKey.put(key)
            else:
                sys.stderr.write('Key：'+key+'失效!\n')
                self.drop_key(key)
        self.disp('直辖市分析完毕!')
        self.disp('分析其他省份中...')
        for region in provValues:
            self.disp('分析'+region+'中...')
            status=1
            while (not self.qKey.empty()) and status != 0:
                key = self.qKey.get()
                url = 'http://api.map.baidu.com/place/v2/search?query=' + query + '&tag=' + tag + '&region='+region+'&output=json&ak=' + key
                response = requests.get(url)
                data = json.loads(response.text)
                status = data['status']
                if status == 0:
                    for item in data['results']:
                        self.qResults.put((region, item['name'], item['num']))
                        self.qKey.put(key)
                else:
                    sys.stderr.write('Key：' + key + '失效!\n')
                    self.drop_key(key)
        self.disp('其他省份分析完毕...')
        i=0
        if not self.qKey.empty():
            df=pd.DataFrame(columns=['province','city','num'])
            while not self.qResults.empty():
                df.loc[i, :] = self.qResults.get()
                i+=1
            t2=time.time()
            self.disp('分城市抓取POI('+query+','+tag+')成功完成,总耗时：'+str(t2-t1)+'s')
            self.disp('除港澳台外，全国'+str(len(df))+'个城市共有指定POI:'+str(df.num.sum())+'个！')
            return df
        else:
            sys.stderr.write('Key耗尽，任务失败，请重置key池后尝试...\n')
            return None
    #通过批处理文件（csv)，批量抓取POI
    def getPOI_byBatch(self,batchPath):
        self.qTask.queue.clear()
        print('启动POI抓取批处理...')
        df = pd.read_csv(batchPath)
        df.fillna('')
        try:
            for i in df.index:
                self.qTask.put(i)
            timer=Timer(3,self.show_batch)
            timer.start()
            # th = Thread(target=self.show_batch())
            # th.start()
            while (not self.qTask.empty()) and (not self.qKey.empty()):
                i=self.qTask.get()
                #按自定义文件或行政区名抓取
                if len(df.region[i].split(';'))==1:
                    # 按自定义文件的方式进行抓取
                    if len(df.region[i].split('.'))>1:
                        gdf=self.getPOI_byFile(df.loc[i,'query'],df.tag[i],df.region[i],df.grid_num[i],df.threshold[i],df.thread_num[i])
                    # 按行政区名称的方式进行抓取
                    else:
                        gdf = self.getPOI_byAD(df.loc[i,'query'], df.tag[i], df.region[i], df.grid_num[i], df.threshold[i],df.thread_num[i])
                #按圆形区域抓取
                elif len(df.region[i].split(';'))==3:
                    rlist=df.region[i].split(';')
                    gdf = self.getPOI_byCircle(df.loc[i,'query'], df.tag[i], float(rlist[0]), float(rlist[1]),float(rlist[2]),df.grid_num[i], df.threshold[i],df.thread_num[i])
                #按矩形区域抓取
                else:
                    rlist = df.region[i].split(';')
                    gdf = self.getPOI_byBounds(df.loc[i,'query'], df.tag[i], float(rlist[0]), float(rlist[1]), float(rlist[2]),float(rlist[3]), df.grid_num[i],df.threshold[i], df.thread_num[i])
                #根据用户定义的输出类型执行输出操作
                if type(gdf) == type(gpd.GeoDataFrame()):
                    outType=df.outFilePath[i].split('.')[len(df.outFilePath[i].split('.')) - 1]
                    if outType == 'csv' or outType=='txt':
                        gdf.to_csv(df.outFilePath[i], encoding='utf-8-sig')
                    elif df.outFilePath[i].split('.')[len(df.outFilePath[i].split('.')) - 1] == 'json':
                        gdf.to_file(df.outFilePath[i], driver='GeoJSON', encoding='utf-8')
                    else:
                        gdf.to_file(df.outFilePath[i], encoding='utf-8')
                    self.disp('写入完成，结果存储于：' + df.outFilePath[i])
                    df.drop(i,inplace=True)
            if len(df)>0:
                self.qTask.queue.clear()
                tempPath=batchPath.split('.csv')[0]+'_cover.csv'
                df.to_csv(tempPath,index=False,encoding='utf-8-sig')
                sys.stderr.write('部分任务失败，未完成部分存储于:'+tempPath+'\n')
            else:
                print('抓取POI批处理成功完成，结果已保存于指定路径')
        except Exception as e:
            self.qTask.queue.clear()
            tempPath=batchPath.split('.csv')[0]+'_cover.csv'
            df.to_csv(tempPath,index=False,encoding='utf-8-sig')
            sys.stderr.write('批处理中止，未完成部分存储于:'+tempPath+'\n')
            sys.stderr.write('e')
if __name__ == '__main__':
    keylist=["mgRIjArNHuol074XjsyDPQMu7g22hEjZ","Zdi4l0k8V41sQqoXdIyZMRDxh3GUzDte"]
    print('初始化类...')
    spider = BaiduPOISpider()  # 实例化BaiduPOISpider类
    print('设置key池...')
    # key池设置一次就够了,thread_protect是用来限制并发的，表示一个Key最多可以被多少个线程同时占有,只要key不超并发，这个值就可以设置的比较大
    # 想速度快，就大key池，多线程，同时在不触发并发限制的情况下调大并发保护数thread_protect
    spider.set_key(keylist,thread_protect=1)
    #测试根据自定义面文件抓取POI-抓取福州市内的KTV(check)
    # gdf = spider.getPOI_byFile('KTV', '', 'https://geo.datav.aliyun.com/areas_v2/bound/350100.json', grid_num=6,threshold=100,thread_num=3)
    #测试根据矩形区域抓取POI-抓取西安市外接矩形内的高中(check)
    # gdf = spider.getPOI_byBounds('高中','中学',118.351915,29.192178,120.724682,30.569969, grid_num=6,threshold=100,thread_num=3)
    #测试根据圆形区域抓取POI-抓取上海市政府周边3km范围内的咖啡厅(check)
    # gdf= spider.getPOI_byCircle('咖啡厅','',121.480248,31.236276,3000, grid_num=6,threshold=100,thread_num=3)
    #测试根据行政区划名称抓取POI-抓取广州市内的酒吧(check)
    # gdf=spider.getPOI_byAD('酒吧','酒吧','广州',grid_num=6,threshold=100,thread_num=3)
    # print(gdf.head())
    #测试抓取POI批处理功能(check)
        #E:/test.csv
            #id,query,tag,region,grid_num,threshold,thread_num,outFilePath
            # 1,KTV,,https://geo.datav.aliyun.com/areas_v2/bound/350100.json,6,100,3,C:\福州市_KTV.csv
            # 2,高中,中学,118.351915;29.192178;120.724682;30.569969,6,100,3,C:\西安外接矩形_高中.shp
            # 3,咖啡厅,,121.480248;31.236276;3000,6,100,3,C:\上海市政府周边3km_咖啡厅.json
            # 4,酒吧,酒吧,广州,6,100,3,C:\广州市_酒吧.txt
    # spider.getPOI_byBatch('E:/Demo.csv')
    #测试分城市获取POI总量(check)
    df=spider.getPOI_CityNum('咖啡厅','咖啡厅')
    print(df.head())
