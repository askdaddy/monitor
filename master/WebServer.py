#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import tornado.httpserver
import tornado.ioloop
import tornado.options

from handler import web
from handler import slave
from handler import tan14
from handler import ops
from handler.base import TaskManage, LocateManage, OpsCacheIPManage
from conf import config
from pymongo import MongoClient
from tornado.options import define, options
 
 
define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        # 定义uri和handler映射
        handlers = [
            (r'/', web.MainHandler),
            # Web端接口
            (r'/api/v1/task/AddTask/',          web.AddTaskHandler),
            (r'/api/v1/task/DeleteTask/',       web.DeleteTaskHandler),
            (r'/api/v1/task/UpdateTask/',       web.UpdateTaskHandler),
            (r'/api/v1/task/QueryTask/',        web.QueryTaskHandler),
            (r'/api/v1/task/QueryResult/',      web.QueryResultHandler),
            # 可用地区，时间等信息
            (r'/api/v1/check/GetAreaList/',     web.GetAreaListHandler),
            (r'/api/v1/check/GetISPList/',      web.GetISPListHandler),
            (r'/api/v1/check/GetTaskInterval/', web.GetTaskIntervalHandler),
            # Slave端接口
            (r'/api/v1/slave/Register/',        slave.RegisterHandler),
            (r'/api/v1/slave/DistributeTask/',  slave.DistributeTaskHandler),
            (r'/api/v1/slave/PostData/',        slave.PostDataHandler),
            #ops cache监控
            (r'/api/v1/ops/cache/AddTask/',     ops.AddCacheTaskHandler),
            (r'/api/v1/ops/cache/modify/params',ops.ModifyAlertParamHandler),
            # Tan14接口
            (r'/api/v1/tan14/performance',      tan14.SourcePerformanceHandler),
        ]
 
        settings = {
            'autoescape': None,
            'debug'     : config.DEBUG,
            'xheaders': True,
        }
                    
        tornado.web.Application.__init__(self, handlers, **settings)
        
        # 初始化传入一个MongoDB数据库连接句柄
        self.con = MongoClient(config.mhost, config.mport)
        self.database = self.con[config.mdb]
        
        # 初始化管理器
        self.loct_mgr = LocateManage()
        self.task_mgr = TaskManage()
        self.ops_ip_mgr = OpsCacheIPManage()
        
        
# master主入口  
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
 

if __name__ == '__main__':
    #import os,sys
    #sys.path.append(os.path.realpath(os.path.dirname(__file__)))
    main()