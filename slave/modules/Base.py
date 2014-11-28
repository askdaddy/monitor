#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import json

from cache import RedisClass
from lib import utils

#所有Model必须继承BaseTask

class BaseTask(object):
    def __init__(self):
        self._result = {}
        self._post = RedisClass.RedisQueue('PostData')
        self.initialize()
    
    def initialize(self):        
        self._detect_point = utils.get_slave_key()
        utils.save_pid_to_cache()

    #将探测结果写入本地缓存
    def save_to_cache(self):      
        if self._result:
            self._post.put(json.dumps(self._result))      
        
    def is_active(self):
        return True    
    
    def run(self):
        pass

    def __call__(self):
        self.run()