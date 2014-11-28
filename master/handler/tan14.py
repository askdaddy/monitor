#!/usr/bin/python
#-*- coding:utf-8 -*-


import time
import copy
import redis
import hashlib

from conf import config
from web import AddTaskHandler
from tornado.escape import json_encode, json_decode


"""查询源站url列表数据，计算可用性并返回，若没有则添加任务"""
class SourcePerformanceHandler(AddTaskHandler):
    def prepare(self):
        self.redis_client = redis.StrictRedis(host = config.rhost, port = config.rport, db = config.rdb)
    
    def gen_retval(self, m, a, b):
        """生成结果返回格式"""
        return {'status': m, 'data': {'chart': {'a': a, 'b': b}}}

    def merge_data(self, cursor):
        """合并来自Mongo的数据"""
        download = []
        avaliab = []
        total = len(cursor)
        delta = total if total <= 30 else total / 30
        n = 0
        m = delta
        while total - m > delta:
            a, b = self.analysis(cursor[n: m])
            download.append(a)
            avaliab.append(b)
            n = n + delta
            m = m + delta
        return download, avaliab
        
    def analysis(self, data):
        """接受一个数据分片"""
        down = 0
        ava = 0
        t = 0
        al = len(data)
        for item in data:
            down = down + item['connect_time']
            if not str(item['http_code']).startswith('5'):
                ava = ava + 1
            t = item['record_time']
        return [t , round(down / al, 2)], [t , int((float(ava) / float(al)) * 100)] 
    
    def get(self):
        uri_hash_code= hashlib.md5(self.request.uri).hexdigest()
        res = self.redis_client.get('String:' + uri_hash_code)
        if res: return self.finish(res)
        
        urls = self.get_argument('urls', '')
        start = self.get_argument('start', '')
        end = self.get_argument('end', '')        
        need_query = []
        task_list = json_decode(urls)
        
        for task in task_list:
            mark = task['url'] + '@' + task['host']
            task_id = self.redis_client.hget('Hash:Tan14TaskId', mark)
            if not task_id: task_id = self.mdb['TaskList'].find_one({'task_target': task['url'], 'http_proxy': task['host'] + ':80'}, {'task_id':1, '_id': 0})
            if task_id:
                need_query.append(task_id)
            else:
                task_id = self.add_task(task)
                if task_id: self.redis_client.hset('Hash:Tan14TaskId', mark, task_id)
        if need_query:
            cursor = self.mdb['Result'].find({'task_id': {'$in': need_query}, 
                                              'record_time': {'$gt': int(start), '$lt': int(end)}}, 
                                             {'_id': 0, 'task_id': 1, 'http_code': 1, 'connect_time': 1, 'record_time': 1}).sort([('record_time', 1)])
            if cursor.count() != 0:
                a, b = self.merge_data(list(cursor))
                retval = self.gen_retval(0, a, b)
                self.redis_client.set('String:'+ uri_hash_code, json_encode(retval))
                self.redis_client.expire('String:'+uri_hash_code, 24 * 3600)
            else:
                retval = self.gen_retval(1, a=[], b=[])
        else:
            retval = self.gen_retval(1, a=[], b=[])
        
        self.write(json_encode(retval))
            
    def add_task(self, task):
        """添加一个任务，返回任务id"""
        task_id = self.gen_task_id()
        valid_task = copy.deepcopy(config.HTTP_TASK)
        valid_task.update({'task_id': task_id, 
                           'task_target': task['url'], 
                           'http_proxy': task['host'] + ':80', 
                           'interval': 5,
                           'end_time': int(time.time()) + 365 * 24 * 3600})
        self.valid_locates = self.loct_mgr.get_valid_locate()
        if self.valid_locates:
            self.dist_task(valid_task)
            self.task_mgr.add(valid_task)
            self.save_to_db(valid_task)
            return task_id
        else:
            return self.write(json_encode({'code': 1, 'data': '当前没有可用地区，任务添加失败'}))