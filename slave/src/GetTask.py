#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import json
import time
import socket
import urllib2

from lib import utils
from config import settings
from cache import RedisClass

class GetTask(object):
    def __init__(self):
        self._task_filter = TaskFilter()
        self.initialize()
        
    def initialize(self):
        utils.save_pid_to_cache()
        
    def run(self):
        self._task_filter.run()
        time.sleep(60)
    
    def __call__(self):
        self.run()


class TaskFilter(object):
    """
    过滤master任务和时期粒度任务，以及删除任务
    重要的任务属性：
        real_time
        is_del
        end_time
    如果是real_time则直接放入todo_list
    如果是is_del则从task_pool中删除该任务
    如果是end_time，则从task_pool中删除该任务
    """
    def __init__(self):
        self._index = 1
        self._slave_key = utils.get_slave_key()
        self._task_pool = RedisClass.RedisHash(namespace='TaskPool')     # 任务池 {task_id, task_dict}
        self._todo_list = RedisClass.RedisQueue(namespace='TodoList')    # 任务队列，[task, task , ...]
        
    
    def _request(self):
        """向master发送请求获取任务"""
        try:
            obj = urllib2.urlopen(settings.DIST_TASK_URL + '?key=' + self._slave_key , timeout=10)
            return obj.read() if obj.getcode() == 200 else None
        except urllib2.URLError:
            pass
        except urllib2.HTTPError:
            pass
        except socket.timeout:
            pass
        
    def _master_filter(self):
        """
        master返回数据: [task, task, task]
        处理real_time和is_del任务，合并修改任务
        """
        json_data = self._request()
        master_task = None
        if json_data:
            try:
                res = json.loads(json_data)
                if res['code'] == 0: master_task = res['data']
            except ValueError:
                pass
        if master_task:
            for task in master_task:
                if 'real_time' in task and task['real_time']:
                    self._todo_list.put(json.dumps(task))
                elif 'is_del' in task and task['is_del']:
                    self._task_pool.hdel(task['task_id'])
                else:
                    self._task_pool.hset(task['task_id'], json.dumps(task))

    def _task_pool_filter(self):
        """任务池过滤：删除过期任务，"""
        time_point = self._get_valid_counter()
        now = int(time.time())
        all_task = self._task_pool.get_all()
        for task_id, task_json in all_task.iteritems():
            task_entity = json.loads(task_json)
            if task_entity['end_time'] < now:
                self._task_pool.hdel(task_id)
            elif task_entity['interval'] in time_point:
                print task_entity['interval']
                self._todo_list.put(task_json)
            else:
                pass 
        
        self._reset_time_counter()
        
    
    def _get_valid_counter(self):
        """时间计数器，每次返回可用的时间粒度"""
        return filter(lambda x: self._index % x == 0, settings.TASK_INTERVAL)    
    
    def _reset_time_counter(self):
        """重置计数器"""
        self._index = 1 if self._index == max(settings.TASK_INTERVAL) else self._index + 1
        
    def run(self):
        self._master_filter()
        self._task_pool_filter()
    
    def __call__(self):
        self.run()