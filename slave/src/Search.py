#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import json
from lib import utils
from cache import RedisClass

import traceback

class Search(object):
    def __init__(self):
        self._todo_list = RedisClass.RedisQueue('TodoList')
        self.initialize()
    
    def initialize(self):
        utils.save_pid_to_cache()

    def do_search(self):
        try:
            task = self._todo_list.get()
            if task:
                obj = self.__auto_mapping(json.loads(task))
                if obj.is_active():
                    obj.run()
        except:
            ex = traceback.format_exc()
            print ex
        
    
    def __auto_mapping(self, task):
        module = __import__(task['task_type'])
        md = getattr(module, task['task_type'])
        return md(task)

    def run(self):
        self.do_search()
        
    def __call__(self):
        self.run()
