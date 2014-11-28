#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

class TaskFieldError(Exception):
    pass

# Http任务类，初始化传入一个任务字典
class DnsTask(object):
    def __init__(self, task):
        pass
        
    def validate(self):
        raise TaskFieldError('任务字段属性有错')
