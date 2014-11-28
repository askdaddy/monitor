#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import time

# debug 模式
DEBUG = True

# MongoDB 
mhost = 'localhost'
mport = 27017
mdb   = 'TestMaster'

# Redis
rhost = 'localhost'
rport = 6379
rdb   = 0

# taobao API
tb_api = 'http://ip.taobao.com/service/getIpInfo.php?ip='

ops_all_cache_ip = 'http://ops.maichuang.net/Servers/getAllCacheIp/'


# 任务时间粒度 单位分钟
task_interval = (1, 2, 3, 5, 10, 15, 30)

HTTP_TASK = {
            'task_type'    : 'Http',
            'task_name'    : 'Http探测',
            'locates'      : [],
            'isps'         : [],
            'task_target'  : '',
            'http_proxy'   : '',
            'http_host'    : '',
            'http_referer' : '',
            'http_cookie'  : '',
            'http_gzip'    : False,
            'http_redirect': False,
            'http_content' : False,
            'real_time'    : False,
            'is_del'       : False,
            'interval'     : 2,
            'conn_timeout' : 3,
            'end_time'     : int(time.time()) + 30 * 24 * 60 * 60,
            'transf_timeout' : 5,
            'http_user_agent': '',
            'http_limit_rate': '',
    }


"""
任务格式定义
task_type       : Http
task_name       : 任务名称                http 探测
task_target     : 探测地址                url
end_time        : 任务结束时间             
interval        : 任务频率,分钟
real_time       : 实时任务标记，默认 False，为True标识只执行一次

locates         : 任务下发地区ID,数组   默认 []
isps            : 任务下发 ISP,数组    默认 []
http_proxy      : 代理  格式 127.0.0.1:8080  可选
http_host       : http 主机名,可选
http_referer    : referer,可选
http_cookie     : cookie, 可选
http_user_agent : user agent,   默认False
http_gzip       : 是否启用 gzip  默认False
http_redirect   : 是否跟随重定向  默认False
http_limit_rate : 限速,Kb/s,可选

http_content    : 是否收集网页数据，慎用！  默认False
is_del          : 是否删除  默认 False
transf_timeout  : 传输超时  默认 5s
conn_timeout    : 连接超时  默认 3s
"""