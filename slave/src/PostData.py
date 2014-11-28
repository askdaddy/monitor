#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import json
import time
import urllib
import httplib
import urlparse
import urllib2

from lib import utils
from cache import RedisClass
from config import settings

"""回收数据，发送给Master"""
class PostData(object):
    def __init__(self):
        self._post = RedisClass.RedisQueue('PostData')
        self.initialize()
        
    def initialize(self):
        utils.save_pid_to_cache()
        self._slave_key = utils.get_slave_key()
        
        
    def post_result(self):
        data = []
        if not self._post.empty():
            num = self._post.qsize()
            print num
            for i in xrange(num):
                tmp = json.loads(self._post.get())
                data.append(tmp)
                
            self.new_request(data)
                
    def new_request(self, data):
        if data:
            params = urllib.urlencode({'key': self._slave_key, 'data': json.dumps(data)})
            try:
                urllib2.urlopen(url= settings.POST_DATA_URL, data=params, timeout=5)
            except:
                pass
    
    def request(self, data):
        if data:
            params = urllib.urlencode({'key': self._slave_key, 'data': json.dumps(data)})
            headers = headers = { "Content-Type": "application/x-www-form-urlencoded", "Connection": "Keep-Alive" } 
            urlres = urlparse.urlparse(settings.POST_DATA_URL)
            try:
                conn = httplib.HTTPConnection(urlres.netloc, timeout=5)
                conn.request(method='POST', url=settings.POST_DATA_URL, body=params, headers=headers)
                response = conn.getresponse()
                if response.status != 200:
                    raise Exception('http code != 200')
            except:
                utils.log_except_traceback(__file__)
            finally:
                conn.close()
                
    def run(self):
        self.post_result()
        time.sleep(20)
    
    def __call__(self):
        self.run()
