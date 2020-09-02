# -*- coding:utf-8 -*-
import numpy as np
import pandas as pd
x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 偏心率平方

def gcj02_to_bd09(lng, lat):
    """
    火星坐标系(GCJ-02)转百度坐标系(BD-09)
    高德——>百度
    :param lng:火星坐标经度
    :param lat:火星坐标纬度
    :return:
    """
    lng=np.array(lng)
    lat=np.array(lat)
    z = np.sqrt(lng * lng + lat * lat) + 0.00002 * np.sin(lat * x_pi)
    #numpy.arctan
    theta = np.arctan2(lat, lng) + 0.000003 * np.cos(lng * x_pi)
    bd09_lng = z * np.cos(theta) + 0.0065
    bd09_lat = z * np.sin(theta) + 0.006
    return [bd09_lng, bd09_lat]


def bd09_to_gcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02)
    百度——>高德
    :param bd_lat:百度坐标纬度
    :param bd_lon:百度坐标经度
    :return:转换后的坐标列表形式
    """
    bd_lon = np.array(bd_lon)
    bd_lat = np.array(bd_lat)
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = np.sqrt(x * x + y * y) - 0.00002 * np.sin(y * x_pi)
    theta = np.arctan2(y, x) - 0.000003 *np.cos(x * x_pi)
    gcj02_lng = z * np.cos(theta)
    gcj02_lat = z * np.sin(theta)
    return [gcj02_lng, gcj02_lat]


def wgs84_to_gcj02(lng, lat):
    """
    WGS84转GCJ02(火星坐标系)
    :param lng:WGS84坐标系的经度
    :param lat:WGS84坐标系的纬度
    :return:
    """
    lng = np.array(lng)
    lat = np.array(lat)
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = np.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = np.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * np.cos(radlat) * pi)
    gcj02_lat = lat + dlat
    gcj02_lng = lng + dlng
    return [gcj02_lng, gcj02_lat]


def gcj02_to_wgs84(lng, lat):
    """
    GCJ02(火星坐标系)转WGS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    lng = np.array(lng)
    lat = np.array(lat)
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = np.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = np.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * np.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    wgs84_lng=lng * 2 - mglng
    wgs84_lat=lat * 2 - mglat
    return [wgs84_lng,wgs84_lat]


def bd09_to_wgs84(bd_lon, bd_lat):
    bd_lon = np.array(bd_lon)
    bd_lat = np.array(bd_lat)
    lon, lat = bd09_to_gcj02(bd_lon, bd_lat)
    return gcj02_to_wgs84(lon, lat)


def wgs84_to_bd09(lon, lat):
    lon = np.array(lon)
    lat = np.array(lat)
    lon, lat = wgs84_to_gcj02(lon, lat)
    return gcj02_to_bd09(lon, lat)


def _transformlat(lng, lat):
    lng = np.array(lng)
    lat = np.array(lat)
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat +\
          0.1 * lng * lat + 0.2 * np.sqrt(np.fabs(lng))
    ret += (20.0 * np.sin(6.0 * lng * pi) + 20.0 *
            np.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * np.sin(lat * pi) + 40.0 *
            np.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * np.sin(lat / 12.0 * pi) + 320 *
            np.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    lng = np.array(lng)
    lat = np.array(lat)
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * np.sqrt(np.fabs(lng))
    ret += (20.0 * np.sin(6.0 * lng * pi) + 20.0 *
            np.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * np.sin(lng * pi) + 40.0 *
            np.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * np.sin(lng / 12.0 * pi) + 300.0 *
            np.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret

def coordtrans(lng,lat,origin_crs,target_crs):
    lng=np.array(lng)
    lat=np.array(lat)
    if origin_crs==target_crs:
        return [lng,lat]
    elif origin_crs=='BD09':
        if target_crs=='GCJ02':
            return bd09_to_gcj02(lng,lat)
        elif target_crs=='WGS84':
            return bd09_to_wgs84(lng,lat)
    elif origin_crs=='GCJ02':
        if target_crs=='BD09':
            return gcj02_to_bd09(lng,lat)
        elif target_crs=='WGS84':
            return gcj02_to_wgs84(lng,lat)
    elif origin_crs=='WGS84':
        if target_crs=='BD09':
            return wgs84_to_bd09(lng,lat)
        elif target_crs=='GCJ02':
            return wgs84_to_gcj02(lng,lat)
    return [lng,lat]

def coordtrans_byFile(inputFilePath,outFilePath,origin_crs,target_crs):
    df=pd.read_csv(inputFilePath,encoding= 'gb18030')
    print('读取批量转换文件：'+inputFilePath)
    print('正执行从' + origin_crs + '到' + target_crs + '的转换...')
    print('转换中...')
    lng=df.lng.values
    lat=df.lat.values
    outlng,outlat=coordtrans(lng,lat,origin_crs,target_crs)
    inlngstr=origin_crs.lower()+'_lng'
    inlatstr=origin_crs.lower()+'_lat'
    outlngstr=target_crs.lower()+'_lng'
    outlatstr=target_crs.lower()+'_lat'
    df.loc[:,inlngstr]=lng
    df.loc[:,inlatstr]=lat
    df.loc[:,outlngstr]=outlng
    df.loc[:,outlatstr]=outlat
    df.drop('lng',axis=1,inplace=True)
    df.drop('lat',axis=1,inplace=True)
    df.to_csv(outFilePath,index=False,encoding='utf-8-sig')
    print('从'+origin_crs+'到'+target_crs+'的转换已完成')
    print('已将结果写入：'+outFilePath)





if __name__ == '__main__':
    lng = np.array([122.23523, 120.2359])
    lat = np.array([31.2312432, 29.123142])
    print(coordtrans(lng,lat,'WGS84','BD09'))
    print(coordtrans(lng,lat,'BD09','GCJ02'))
    coordtrans_byFile('D:/坐标转换输入Demo.csv', 'D:/坐标转换Results.csv', 'WGS84', 'BD09')
    # lngt,latt = gcj02_to_bd09(lng, lat)
    # result2 = bd09_to_gcj02(lng, lat)
    # result3 = wgs84_to_gcj02(lng, lat)
    # result4 = gcj02_to_wgs84(lng, lat)
    # result5 = bd09_to_wgs84(lng, lat)
    # result6 = wgs84_to_bd09(lng, lat)
    # print('gcj02_to_bd09:',bd09_to_gcj02(lng, lat))
    # print('gcj02_to_wgs84:', gcj02_to_wgs84(lng, lat))
    # print('wgs84_to_gcj02:',wgs84_to_gcj02(lng, lat))
    # print('wgs84_to_bd09:', wgs84_to_bd09(lng, lat))
    # print('bd09_to_wgs84:',bd09_to_wgs84(lng, lat))
    # print('bd09_to_gcj02:', bd09_to_gcj02(lng, lat))
    # print(lngt,lat)




