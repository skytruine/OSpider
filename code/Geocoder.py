# -*- coding:utf-8 -*-
#-*-coding:utf-8-*-
import tkinter as tk
import tkinter.filedialog
# from tkinter import filedialog
import json
import requests
import CoordTrans as coord
import os,sys
import importlib
import itertools
import time
import platform

class Adress:
    id = -1
    city=''
    address = ''
    status=-1
    bd09_lng = -1
    bd09_lat = -1
    wgs84_lng = -1
    wgs84_lat = -1
    precise=-1
    confidence=-1
    comprehension=-1
    level=''

#有点写不动了，地址解析就用了原来的旧代码，暂时先用着吧，也没啥问题
def Geocoder(key,inputFilePath,outputDirPath):
    print('地址解析：开发者偷懒所以本功能依然是单Key单线程...鲁棒性一般')
    print('目前基本够用，之后有空再优化')
    t1=time.time()
    lAdress = list()
    urls = list()
    file = open(inputFilePath, 'r')
    for line in itertools.islice(file,1,None):
        text=line.strip('\n').split(',')
        address=Adress()
        address.id=text[0]
        address.city=text[1]
        address.address=text[2]
        url='http://api.map.baidu.com/geocoding/v3/?address='+address.address+'&city='+address.city+'&output=json&ak='+key
        urls.append(url)
        lAdress.append(address)
    file.close()
    print('文件读取完毕，开始抓取...')
    n=len(urls)
    print('进度:1/' + str(n))
    for i in range(len(urls)):
        if not (i+1)%5:
            print('进度:'+str(i+1)+'/'+str(n))
        url=urls[i]
        response = requests.get(url)
        data = json.loads(response.text)
        if not data['status']:
            lAdress[i].status=data['status']
            lAdress[i].bd09_lng=data['result']['location']['lng']
            lAdress[i].bd09_lat=data['result']['location']['lat']
            lng,lat=coord.bd09_to_wgs84([lAdress[i].bd09_lng],[lAdress[i].bd09_lat])
            lAdress[i].wgs84_lng=lng[0]
            lAdress[i].wgs84_lat = lat[0]
            lAdress[i].precise=data['result']['precise']
            lAdress[i].confidence = data['result']['confidence']
            lAdress[i].comprehension = data['result']['comprehension']
            lAdress[i].level=data['result']['level']
        else:
            lAdress[i].status = data['status']
    t2=time.time()
    print('解析完毕，结果写入中...')
    inputFileName = inputFilePath.split('/')[-1].split('.')[0]
    outputPath=outputDirPath+'/地址解析结果_'+inputFileName+'.csv'
    os.makedirs(os.path.dirname(outputPath), exist_ok=True)
    file = open(outputPath, 'w')
    print('-------OSpider-Geocoder ------------------')
    print('于 ' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '执行地址解析：')
    print('输入文件：' + inputFilePath )
    print('输出路径：' + outputDirPath)
    print('使用的KEY：' +key)
    print('---------------')
    print('抓取耗时：' + str(t2-t1) + 's')
    print('KEY用量：' + str(len(urls)) )
    print('结果文件：' + outputPath )
    print('--------OSpider-Geocoder------------------')
    file.write('id,city,address,status,wgs84_lng,wgs84_lat,bd09_lng,bd09_lat,precise,confidence,comprehension,level\n')
    for each in lAdress:
        tstr =str(each.id)+','+each.city+','+each.address+','+str(each.status)+','+str(each.wgs84_lng)+','+str(
            each.wgs84_lat)+','+str(each.bd09_lng)+','+str(each.wgs84_lat)+','+str(each.precise)+','+str(
            each.confidence)+','+str(each.comprehension)+','+each.level+'\n'
        file.write(tstr)
    file.close()
    print('写入完毕，输出路径为：'+outputPath)

if __name__ == '__main__':
    #不太想写的原因是我follow了一个开源项目专门做Geocoder的，项目代码质量很高但我还没研究清楚，我希望能够为该项目贡献代码或使用该项目，因此不愿从底层自己写了
    inputFilePath='D:/地址解析输入Demo.csv'
    outputDirPath='D:/'
    key='4Ye9j82Hwdm79nQB5Y7lCZqPLo1O8SeX'
    Geocoder(key,inputFilePath,outputDirPath)