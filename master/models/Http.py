#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import re
import time
from conf import config


class HttpTaskError(Exception):
    pass
"""
http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+
"""

class HttpTask(object):    
    def __init__(self):
        self._raw_task = {}
        self._ret_task = config.HTTP_TASK
        self._valid_pattern = {
            'require' : re.compile(r'.+'),                     
            'number'  : re.compile(r'^\d+$'),
            'integer' : re.compile(r'^[-\+]?\d+$'),
            'double'  : re.compile(r'^[-\+]?\d+(\.\d+)?$'),
            'email'   : re.compile(r'^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$'),
            'url'     : re.compile(r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*\/?$',),
            'ip'      : re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'),
        }

        self._field_valid_mapper = {
            'task_name'    : self._valid_task_name,
            'task_target'  : self._valid_task_target,
            'locates'      : self._valid_locate,
            'isps'         : self._valid_isp,
            'http_proxy'   : self._valid_proxy,
            'http_host'    : self._valid_host,
            'http_referer' : self._valid_referer,
            'http_cookie'  : self._valid_cookie,
            'http_gzip'    : self._valid_gzip,
            'http_redirect': self._valid_redirect,
            'http_content' : self._valid_content,
            'real_time'    : self._valid_real_time,
            'is_del'       : self._valid_is_del,
            'interval'     : self._valid_interval,
            'conn_timeout' : self._valid_timeout,
            'end_time'     : self._valid_end_timeout,
            'transf_timeout' : self._valid_timeout,
            'http_user_agent': self._valid_user_agent,
            'http_limit_rate': self._valid_limit_rate,
        }     
          
        
    def auto_validate(self, task):
        """
        @param   dict:  self.request.arguments
        @return  task or exception
        """
        if task and isinstance(task, dict):
            self._raw_task = task
        else:
            raise HttpTaskError('参数错误')
            
        for key, value in self._raw_task.iteritems():
            if key in self._ret_task:
                self._field_valid_mapper[key](key, value)
            else:
                raise HttpTaskError('未知参数：%s' % key)
        return self._ret_task                    
            
    def _valid_set(self, is_valid, key, value):
        if is_valid:
            self._ret_task.update({key: value})
        else:
            raise HttpTaskError('字段：%s => 值: %s 设置错误' % (key, repr(value)))
        
    def _valid_task_name(self, key, value):
        is_valid = True if value[0] != '' else False
        self._valid_set(is_valid, key, value[0])
        
    def _valid_task_target(self, key, value):
        """验证是否是一个合法的url"""
        is_valid = True if self._valid_pattern['url'].match(value[0]) else False
        self._valid_set(is_valid, key, value[0])

    def _valid_locate(self, key, value):
        self._valid_set('is_valid', key, value)

    def _valid_isp(self, key, value):
        self._valid_set('is_valid', key, value)
    
    def _valid_proxy(self, key, value):
        parsed_value = value[0].split(':')
        is_valid = True if (len(parsed_value) == 2 and 
                            self._valid_pattern['ip'].match(parsed_value[0]) and 
                            self._valid_pattern['integer'].match(parsed_value[1])) else False
        self._valid_set(is_valid, key, value[0])
    
    def _valid_host(self, key, value):
        self._valid_set('is_valid', key, value)
    
    def _valid_referer(self, key, value):
        self._valid_set('is_valid', key, value)
    
    def _valid_cookie(self, key, value):
        self._valid_set('is_valid', key, value)
    
    def _valid_gzip(self, key, value):
        self._valid_set('is_valid', key, value)
    
    def _valid_redirect(self, key, value):
        is_valid = True if value[0] != '' else False
        self._valid_set(is_valid, key, is_valid)
    
    def _valid_content(self, key, value):
        is_valid = True if value[0] else False
        self._valid_set(is_valid, key, is_valid)
    
    def _valid_real_time(self, key, value):
        self._valid_set('is_valid', key, value)
    
    def _valid_is_del(self, key, value):
        self._valid_set('is_valid', key, value)
    
    def _valid_interval(self, key, value):
        try:
            value = int(value[0])
            is_valid = True if value in config.task_interval else False
        except ValueError:
            is_valid = False
        self._valid_set(is_valid, key, value)
    
    def _valid_timeout(self, key, value):
        try:
            value = int(value[0])
            is_valid = True
        except ValueError:
            is_valid = False
        self._valid_set(is_valid, key, value)
    
    def _valid_end_timeout(self, key, value):
        try:
            value = int(value[0])
            now = int(time.time())
            is_valid = True if value > now else False
        except ValueError:
            is_valid = False
        self._valid_set(is_valid, key, value)
    
    def _valid_user_agent(self, key, value):
        self._valid_set('is_valid', key, value[0])
    
    def _valid_limit_rate(self, key, value):
        self._valid_set('is_valid', key, value[0])        
                

if __name__ == '__main__':
    task = {'task_target': 'http://www.baidu.com/', 
            'http_proxy': '123.4.5.6:80', 
            'interval': 1, 
            'http_host': 'www.baidu.com',
            'http_cookie': 'setup cookie',
            'http_redirect': True,
            'isps': [1,2,3,4],
            'locates': [14,563,6246],
            'transf_timeout': 20,
            'http_referer': 'setup referer',
            'end_time': 1234560000000,
    }
    ht = HttpTask()
    try:
        res = ht.auto_validate(task)
    except HttpTaskError as e:
        print e
    if 'res'  in globals():
        for k, v in res.iteritems():
            print k , '==>' , v
