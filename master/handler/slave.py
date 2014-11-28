#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import time
import urllib

from conf import config
from tornado.escape import json_encode, json_decode
from base import BaseHandler, TaskOperator
from pymongo.errors import OperationFailure



class RegisterHandler(BaseHandler):
    """
    slave 注册接口
    调用http://ip.taobao.com/service/getIpInfo.php?ip=[ip地址字串] 获取slave地理信息
    判断是否有该地区id记录，若没有则记录，否则创建新的记录，并初始化该地区任务列表到缓存中
    @param string ip
    @return slave key
    """
    def get(self):
        """ 如果在反向代理后运行，则设置X-Real-Ip """
        """ 218.66.170.126 """
        #slave_ip = self.request.remote_ip   112.90.60.203
        slave_ip = self.get_argument('ip', '112.90.60.203')
        ip_info = self._call_taobao_api(slave_ip)
        if ip_info['code'] == 1:
            return self.write(json_encode({'code': 1, 'data': 'ip信息获取失败'}))
        else:
            locate_key = self._gen_locate_key_by_ip(ip_info)
            slave_key = locate_key + '-' + str(int(time.time()))
            if not self._save_slave_into_db(slave_ip, ip_info, locate_key, slave_key):
                return self.write(json_encode({'code': 1, 'data': '数据库操作失败'}))
            self._save_slave_into_cache(locate_key)
            self.write(json_encode({'code': 0, 'data': slave_key}))
            
    def _call_taobao_api(self, slave_ip):
        url = config.tb_api + slave_ip
        return json_decode(urllib.urlopen(url).read())
    
    def _gen_locate_key_by_ip(self, ip_info):
        "locate_key 格式: CN-area-region-city-isp"
        return '-'.join(('CN',
                         ip_info['data']['area_id'],    
                         ip_info['data']['region_id'],  
                         ip_info['data']['city_id'],    
                         ip_info['data']['isp_id']))
    
    def _save_slave_into_db(self, slave_ip, ip_info, locate_key, slave_key):
        data = {
            'ip_info'   :   ip_info,
            'slave_ip'  :   slave_ip,
            'locate_key':   locate_key,
            'slave_key' :   slave_key,
            'weigth'    :   0,
            'last_post' :   None,
        }
        try:
            return self.mdb['RegisteredSlave'].insert(data)
        except OperationFailure:
            pass
    
    def _save_slave_into_cache(self, locate_key):
        if not self.loct_mgr.is_exists(locate_key):
            self.loct_mgr.add(locate_key)
            self._init_task_table(locate_key)
        
    def _init_task_table(self, locate_key):
        """初始化locate_key对应的任务表"""
        all_task = self.task_mgr.get_all_task_id()
        to = TaskOperator(locate_key)
        if all_task:
            for task_id in all_task:
                to.add(task_id)


class DistributeTaskHandler(BaseHandler):
    """
    任务分发
    根据slave_key获取locate_key
    实例化locate_key对应的任务管理器，获取当前可以用的任务
    """
    def get(self):
        slave_key = self.get_argument('key', None)
        retval = []
        if slave_key:
            locate_key = self.parse_key(slave_key, 'locate_key')
            if locate_key:
                to = TaskOperator(locate_key)
                task_list = to.distribute(slave_key)
                if task_list:
                    for task in task_list:
                        if isinstance(task, str):
                            ts = self.get_task_from_task_mgr(task)
                            retval.append(ts)
                        elif isinstance(task, dict):
                            retval.append(task)
                        else:
                            pass
                    self.write(json_encode({'code': 0, 'data': retval }))
                else:
                    self.write(json_encode({'code': 1, 'data': '没有需要分发的任务'}))
            
    def get_task_from_task_mgr(self, task_id):
        return self.task_mgr.get(task_id)
    

class PostDataHandler(BaseHandler):
    """
    数据回收
    更新对应地区时间戳
    @params dict {'key':xxx, 'data':xxx}, data: result
    """
    def get(self):
        slave_key = self.get_argument('key', None)
        data_json = self.get_argument('data', None)
        if slave_key:
            self.write(slave_key)
            locate_key = self.parse_key(slave_key, 'locate_key')
            if locate_key:
                self.loct_mgr.update(locate_key)
            else:
                return
            if data_json:
                data = json_decode(data_json)
                try:
                    self.mdb['Result'].insert(data)
                except OperationFailure:
                    pass