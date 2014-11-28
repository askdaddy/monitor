#!/usr/bin/python2.7
#-*- coding:utf-8 -*-


#master 
MASTER_HOST = 'http://127.0.0.1:8888'

REGISTER_URL  = MASTER_HOST + '/api/v1/slave/Register/'
DIST_TASK_URL = MASTER_HOST + '/api/v1/slave/DistributeTask/'
POST_DATA_URL = MASTER_HOST + '/api/v1/slave/PostData/' 

# Redis
rhost = 'localhost'
rport = 6379
rdb   = 0

# 任务时间粒度
TASK_INTERVAL = (1, 2, 3, 5, 10, 15, 30)

#base path
BASE_PATH = '/tmp/slave/'
# Pid缓存文件
PID_PATH = BASE_PATH + 'pid/'
# 错误日志
ERROR_LOG_PATH = BASE_PATH + 'error/'
# key path
SLAVE_KEY_PATH = BASE_PATH + 'slave.key'
# main pid
MAIN_PID = BASE_PATH + 'main.pid'


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
#            'end_time'     : int(time.time()) + 30 * 24 * 60 * 60,
            'transf_timeout' : 5,
            'http_user_agent': '',
            'http_limit_rate': '',
    }