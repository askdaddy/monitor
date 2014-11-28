#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import time
import functools
import tornado.web

from cache import RedisClass
from tornado.escape import json_encode, json_decode


def user_auth(method):
    """用户验证装饰器"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        if username == 'cyrus' and password == 'cyrus':
        #if username and password and self.mdb['UserInfo'].count({'username': username, 'password': password}) == 1:
            return method(self, *args, **kwargs)
        else:
            self.finish(json_encode({'code': 1, 'data': '用户验证失败'}))
    return wrapper


class BaseHandler(tornado.web.RequestHandler):
    """Handler基类，所有Handler必须继承该类"""
    @property
    def mdb(self):
        return self.application.database
    
    @property
    def loct_mgr(self):
        return self.application.loct_mgr
    
    @property
    def task_mgr(self):
        return self.application.task_mgr

    @property
    def ops_ip_mgr(self):
        return self.application.ops_ip_mgr

    def post(self):
        self.get()
    
    def parse_key(self, key, field = None):
        """key格式： CN-area-region-city-isp-(timestamp)"""
        res = key.split('-')
        res.append('timestamp') if len(res) == 5 else res
        if len(res) == 6:
            parsed_key = dict(
                locate_key = '-'.join(res[0:5]),
                area       = res[1],
                region     = res[2],
                city       = res[3],
                isp        = res[4],
                reg_time   = res[5],
            )
            return parsed_key[field] if field in parsed_key else parsed_key
        
    def get_valid_locate_or_isp(self, kind = None):
        """
        获取当前可用地区列表
        从locate_mgr获取可用地区列表
        查询RegisteredLocate，获取详细信息
        { "info" : { "data" : { "region_id" : "310000", "region" : "上海市", "isp" : "电信", "isp_id" : "100017" } } }
        """
        if kind in ('region', 'isp'):
            valid_locate = self.loct_mgr.get_valid_locate()
            if valid_locate:
                try:
                    cursor = self.mdb['RegisteredSlave'].find({'locate_key': {'$in': valid_locate}}, 
                                           {'_id'                     : 0, 
                                            'ip_info.data.' + kind       : 1, 
                                            'ip_info.data.' + kind +'_id': 1 })
                except TypeError:
                    return self.write(json_encode({'code': 1, 'data': '数据库查询参数错误'}))
                retval = []
                tmp = {}
                for res in cursor:
                    tmp.setdefault(res['ip_info']['data'][kind], res['ip_info']['data'][kind + '_id'])
                for locate_name, locate_key in tmp.iteritems():
                    retval.append({locate_name: locate_key})
                self.write(json_encode({'code': 0, 'data': retval}))
            else:
                self.write(json_encode({'code': 1, 'data': '当前没有信息'}))
        else:
            raise AssertionError('kind参数只能取值region或isp')
    
"""
  type: RedisHash  
  locate_key #  task_id => {is_del : False, which_slave : [slave_1_key, salve_2_key] or None }
"""
class TaskOperator(object):
    """
    任务操作类       
    提供任务在缓存中的CURD操作
    """
    def __init__(self, locate_key):
        self._task_opt = RedisClass.RedisHash(namespace = locate_key)
        self._basic_schema = {
            'is_del'      : False,
            'which_slave' : [],
        }
    
    def add(self, task_id, schema = None):
        if schema:
            self._task_opt.hset(task_id, json_encode(schema))
        else:
            self._task_opt.hset(task_id, json_encode(self._basic_schema))
                    
    def reset(self, task_id):    
        self.add(task_id)        
            
    def update(self, task_id, schema):
        self.add(task_id, schema)

    def delete(self, task_id):
        """Web端调用，删除操作，修改is_del标志为True"""
        tmp = self.get(task_id)
        if tmp:
            tmp['is_del'] = True
            self._task_opt.hset(task_id, json_encode(tmp))

    def remove(self, task_id):
        """Slave端调用，删除操作，从任务表中删除该任务"""
        self._task_opt.hdel(task_id)
        
    def get(self, task_id):
        tmp = self._task_opt.hget(task_id)
        return json_decode(tmp) if tmp else None
    
    def distribute(self, slave_key):
        """ 
        根据basic_schema信息分发任务 
        @params string slave_key
        @return list task_id    {id, id {task},id}
        """
        all_task = self._task_opt.get_all()
        retval = []
        need_del = []
        for task_id, schema_json in all_task.iteritems():
            basic_schema = json_decode(schema_json)
            if basic_schema['is_del']:             
                if basic_schema['which_slave'] :
                    if slave_key in basic_schema['which_slave']:
                        basic_schema['which_slave'].remove(slave_key)
                        self.update(task_id, basic_schema)
                        retval.append({'task_id': task_id, 'is_del': True})
                else:
                    need_del.append(task_id)
            else:
                if slave_key not in basic_schema['which_slave']:
                    retval.append(task_id)
                    basic_schema['which_slave'].append(slave_key)
                    self.update(task_id, basic_schema)
        if need_del:
            for task_id in need_del:
                self.remove(task_id)            
        return retval


class TaskManage(object):
    """
    任务管理器
    {task_id:xxx, task_json:json_obj}
    """
    def __init__(self, namespace = 'TaskManage'):
        self._task_cache = RedisClass.RedisHash(namespace)
    
    def add(self, task):
        self._task_cache.hset(task['task_id'], json_encode(task))
    
    def delete(self, task_id):
        self._task_cache.hdel(task_id)
    
    def update(self, task):
        self.add(task)
    
    def get(self, task_id):
        return json_decode(self._task_cache.hget(task_id))
    
    def get_all(self):
        result = self._task_cache.get_all()
        tmp = {}
        if result:
            for key, value in result.iteritems():
                tmp.setdefault(key, json_decode(value))
        return tmp
    
    def get_all_task_id(self):
        return self._task_cache.get_all_keys()
    
    
class LocateManage(object):
    """
    地区管理器    管理以注册的地区
    {locate_key: last_update }
    """
    def __init__(self, namespace = 'LocateManage'):
        self._locate_cache = RedisClass.RedisHash(namespace)
        
    def add(self, locate_key):
        self._locate_cache.hset(locate_key, int(time.time()))
        
    def delete(self, locate_key):
        self._locate_cache.hdel(locate_key)
    
    def update(self, locate_key):
        self.add(locate_key)
    
    def is_exists(self, locate_key):
        return self._locate_cache.hexists(locate_key)
    
    def get_valid_locate(self):
        """获取前10分钟的地区，作为可用地区点"""
        dead_line = int(time.time()) - 10 * 60
        all_locate = self._locate_cache.get_all()
        retval = []
        for locate_key, last_time in all_locate.iteritems():
            if last_time >= dead_line:
                retval.append(locate_key)
        return retval
    
class OpsCacheIPManage(object):
    """
    管理Ops中Cache任务下发
    """
    def __init__(self, namespace='OpsCacheIP'):
        self._ip_mgr = RedisClass.RedisHash(namespace)
        
    def add(self, ip, task_id):
        self._ip_mgr.hset(ip, task_id)
        
    def is_exists(self, ip):
        return self._ip_mgr.hexists(ip)
    
    def get(self, ip):
        return self._ip_mgr.hget(ip)