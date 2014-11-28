#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import time
import copy
import uuid
import tornado.web

from . import base
from datetime import datetime
from models.Http import HttpTaskError, HttpTask
from pymongo.errors import OperationFailure
from tornado.escape import json_encode

class MainHandler(tornado.web.RequestHandler):
    """
    测试Tornado是否正常工作！
    """
    @property
    def db(self):
        return self.application.database
  
 
    def get(self):
        new_comment = {
            "comment": "what a nice page",
            "author" : "test",
            "time"   : datetime.utcnow(),
        }
 
        self.db.comments.insert(new_comment)
 
        comments = self.db["comments"].find()
 
        self.write("Hello, world. with mongo")
        for c in comments:
            self.write("<br/>")
            self.write(c["comment"])
            self.write(c["author"])
            self.write(str(c["time"]))

# Web端接口
class AddTaskHandler(base.BaseHandler):
    """
    验证数据合法性，存入Mongo和Redis，返回任务id
    @param dict: self.requeset.arguments 
    @return task_id
    """
    @base.user_auth
    def get(self):
        task = copy.deepcopy(self.request.arguments)
        task.pop('username')
        task.pop('password')
        try:
            http_check = HttpTask()
            valid_task = http_check.auto_validate(task)
        except HttpTaskError as e:
            return self.finish(json_encode({'code': 1, 'data': repr(e)}))
            
        task_id = self.gen_task_id()    
        valid_task.update({'task_id': task_id})
        
        """ 添加到任务管理器，分发，存数据库 """         
        self.valid_locates = self.loct_mgr.get_valid_locate()
        if self.valid_locates:
            self.dist_task(valid_task)
            self.task_mgr.add(valid_task)
            self.save_to_db(valid_task)
            self.write(json_encode({'code': 0, 'data': task_id}))
        else:
            self.write(json_encode({'code': 1, 'data': '当前没有可用的地区，任务添加失败'}))
    
    def dist_task(self, valid_task):
        isps = valid_task['isps']
        regions = valid_task['locates']
        for locate_key in self.valid_locates:
            task_ops = base.TaskOperator(locate_key)
            pk = self.parse_key(locate_key)
            """根据region和isp分发任务"""
            if (not isps and not regions or
                not isps and pk['region'] in regions or
                not regions and pk['isp'] in isps or
                pk['isp'] in isps and not pk['region'] in regions):
                task_ops.add(valid_task['task_id'])    
                     
    def gen_task_id(self):
        """唯一任务id生成，暂用uuid"""
        return uuid.uuid1().hex
    
    def save_to_db(self, valid_task):
        valid_task = copy.deepcopy(valid_task)
        try:
            self.mdb['TaskList'].insert(valid_task)
        except OperationFailure:
            return self.write(json_encode({'code': 1, 'data': '任务分发成功，但是存入数据失败，任务id: %s \
            你可以在有效期内调用/api/v1/task/QueryResult/获取探测结果' % valid_task['task_id'] }))
        try:
            self.mdb['UserInfo'].update({'username': self.get_argument('username'), 
                                         'password': self.get_argument('password') 
                                         },{
                                         '$push': {'task_id_list': valid_task['task_id']}
                                        })
        except (TypeError, OperationFailure):
            self.write(json_encode({'code': 1, 'data': '任务分发成功，但是任务id任存入用户表失败，任务id: %s \
            你可以在有效期内调用/api/v1/task/QueryResult/获取探测结果' % valid_task['task_id']}))
         
    
        
class DeleteTaskHandler(base.BaseHandler):
    """
    查询任务分发信息，逐个下发删除命令
    @param string: task_id
    @return: ok
    """
    @base.user_auth
    def get(self):
        task_id = self.get_argument('task_id', None)
        if task_id:
            self.task_mgr.delete(task_id)
            task_detail = self.mdb['TaskList'].find_one({'task_id': task_id}, {'_id': 0})
            if task_detail:
                self.mdb['TaskList'].remove({'task_id': task_id})
                isps = task_detail['isps']
                regions = task_detail['locates']
                """分发下发消息"""
                valid_locates = self.loct_mgr.get_valid_locate()
                if valid_locates:        
                    for locate_key in valid_locates:
                        task_ops = base.TaskOperator(locate_key)
                        pk = self.parse_key(locate_key)
                        if (not isps and not regions or
                            not isps and pk['region'] in regions or
                            not regions and pk['isp'] in isps or
                            pk['isp'] in isps and not pk['region'] in regions):
                            task_ops.delete(task_id)    
            self.write({'code':0, 'data': 'ok'})
        else:
            self.write({'code': 1, 'data': '无效的任务id'})
    
class UpdateTaskHandler(base.BaseHandler):
    """
    @param string: task_id
    @param other: 其他参数同创建任务参数
    @return: ok
    """
    @base.user_auth
    def get(self):
        pass
    
    
class QueryTaskHandler(base.BaseHandler):
    """
    任务查询
    @param string: task_id
    @param dict: task_detail 
    """
    @base.user_auth
    def get(self):
        task_id = self.get_argument('task_id', None)
        if task_id:
            task_detail = self.mdb['TaskList'].find_one({'task_id': task_id}, {'_id': 0})
            if task_detail:
                self.write(json_encode({'code': 0, 'data': task_detail}))
            else:
                self.write(json_encode({'code': 1, 'data': '没有该任务，请检查task_id参数是否正确'}))
    
    
class QueryResultHandler(base.BaseHandler):
    """
    探测结果查询
    @param string: task_id
    @param int   : start_time  unix时间戳  默认距离当前30分钟
    @param int   : end_time    unix时间戳  默认当前
    @return:  { 'code': 0, 'data': [ {result},  {result},  {result}] } 
    """
    @base.user_auth
    def get(self):
        cur_time = int(time.time())
        start_time = int(self.get_argument('start_time', cur_time - 30 * 60))
        end_time   = int(self.get_argument('end_time', cur_time))
        task_id    = self.get_argument('task_id', None)
        if task_id:
            if start_time > end_time:
                self.write(json_encode({'code': 1, 'data': '起始时间不能大于结束时间'}))
            else:
                try:
                    cursor = self.mdb['Result'].find({'task_id': task_id, 'record_time': {'$lt': end_time, '$gt': start_time}}, {'_id': 0})
                except TypeError:
                    return self.write(json_encode({'code': 1, 'data': '数据库查询参数错误'}))
                if cursor.count() != 0:
                    retval = list(cursor)
                    self.write(json_encode({'code': 0, 'data': retval }))
                else:
                    self.write(json_encode({'code': 1, 'data': '没有该任务结果'}))
        else:
            self.write(json_encode({'code': 1, 'data': '没有task_id'}))
        
    

# 可用地区，时间等信息 
class GetAreaListHandler(base.BaseHandler):
    @base.user_auth
    def get(self):
        self.get_valid_locate_or_isp(kind = 'region')
        
        
class GetISPListHandler(base.BaseHandler):
    @base.user_auth
    def get(self):
        self.get_valid_locate_or_isp(kind = 'isp')
        
    
class GetTaskIntervalHandler(base.BaseHandler):
    """返回当前可用的时间粒度"""
    @base.user_auth
    def get(self):
        self.write(json_encode(
                {'code' : 0, 
                 'data' : [{'name': '1分钟', 'value': 1}, 
                           {'name': '2分钟', 'value': 2}, 
                           {'name': '3分钟', 'value': 3},
                           {'name': '5分钟', 'value': 5},
                           {'name': '10分钟','value': 10},
                           {'name': '15分钟','value': 15},
                           {'name': '30分钟','value': 30},]
                 }))