#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import base
import copy
import time
import tornado.web
import tornado.gen
import tornado.httpclient

from conf import config
from web import AddTaskHandler
from tornado.escape import json_encode, json_decode


class AddCacheTaskHandler(AddTaskHandler):
    """
    请求ops获取全部的Cache IP
    检测任务是否添加，若没有则添加
    """
    @base.user_auth
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()
        response = yield http_client.fetch(config.ops_all_cache_ip)
        res = json_decode(response.body)
        cache_list = res['data'] if res['code'] == 0 else None
        task = copy.deepcopy(config.HTTP_TASK)
        retval = {}
        self.valid_locates = self.loct_mgr.get_valid_locate()
        if self.valid_locates and cache_list:
            for item in cache_list:
                for port in ('80', '8081', '8082'):
                    http_proxy = item['proxy_ip'] + ':' + port
                    if http_proxy not in retval: retval[http_proxy] = ''
                    if not self.ops_ip_mgr.is_exists(http_proxy) and \
                    not self.mdb['TaskList'].find_one({'http_proxy': http_proxy}):
                        task_id = self.gen_task_id()
                        task.update({'task_id': task_id,
                                     'task_name': item['name'], 
                                     'http_proxy': http_proxy, 
                                     'task_target': 'http://cdnfox.com/0/1.jpg', 
                                     'end_time': int(time.time()) + 365 * 24 * 60 * 60 })
                        retval.update({http_proxy: task_id})
                        self.ops_ip_mgr.add(http_proxy, task_id)
                        self.dist_task(task)
                        self.task_mgr.add(task)
                        self.save_to_db(task)
            self.write(json_encode({'code': 0, 'data': retval}))
        else:
            self.write(json_encode({'code': 1, 'data': '当前没有可以的地区，或没有可用的Cache'}))
        self.finish()


class ModifyAlertParamHandler(base.BaseHandler):
    def prepare(self):
        """读取配置文件"""
        pass
    
    def get(self):
        """验证参数合法性，并修改"""
        pass