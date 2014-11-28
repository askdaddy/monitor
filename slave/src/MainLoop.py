#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import sys

from lib import utils

"""进程主循环控制类"""
class Loop(object):
    def __init__(self):
        self._instance = None
    
    def initialize(self):
        utils.save_pid_to_cache()
        
    def auto_load(self, process_name):
        p = __import__(process_name)
        obj = getattr(p, process_name)
        self._instance = obj()
        
    def run(self):
        self.initialize()
        while True:
            self._instance.run()
            
    def sig_handler(self, signum, frame):
        self.shut_down
        
    def shut_down(self):
        utils.clean_pid()
        sys.exit()