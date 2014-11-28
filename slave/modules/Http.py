#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import time
import pycurl
import cStringIO

from modules.Base import BaseTask
from urlparse import urlparse

class Http(BaseTask):
    def __init__(self, task):
        BaseTask.__init__(self)
        self._task = task
        self._head_info = cStringIO.StringIO()
        self._body_content = cStringIO.StringIO()

    def do_task(self):
        try:
            c = pycurl.Curl()
            c.setopt(pycurl.URL, str(self._task['task_target']))
            c.setopt(pycurl.HEADERFUNCTION, self._head_info.write)
            
            if 'http_content' in self._task and self._task['http_content']:
                c.setopt(pycurl.WRITEFUNCTION, self._body_content.write)
            else:
                c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
            
            if 'http_referer' in self._task and self._task['http_referer']:
                c.setopt(pycurl.REFERER, self._task['http_referer'])
            
            if 'http_user_agent' in self._task and self._task['http_user_agent']:
                c.setopt(pycurl.USERAGENT, self._task['http_user_agent'])
            
            if 'http_cookie' in self._task and self._task['http_cookie']:
                c.setopt(pycurl.COOKIE, self._task['http_cookie'])
                
            if 'conn_timeout' in self._task and self._task['conn_timeout']:
                c.setopt(pycurl.CONNECTTIMEOUT, self._task['conn_timeout'])
            
            if 'transf_timeout' in self._task and self._task['transf_timeout']:
                c.setopt(pycurl.TIMEOUT, self._task['transf_timeout'])
            
            if 'http_redirect' in self._task and self._task['http_redirect']:
                c.setopt(pycurl.FOLLOWLOCATION, 1)
            
            if 'http_limit_rate' in self._task and self._task['http_limit_rate']:
                c.setopt(pycurl.MAX_SEND_SPEED_LARGE, self._task['MAX_SEND_SPEED_LARGE'])
                
            if 'http_proxy' in self._task and self._task['http_proxy']:
                self._proxy_ip, self._proxy_port = self._task['http_proxy'].split(':')
                c.setopt(pycurl.PROXY, str(self._task['http_proxy']))
            else:
                self._proxy_ip, self._proxy_port = '', ''

            if 'http_gzip' in self._task and self._task['http_gzip']:
                c.setopt(pycurl.ENCODING, 'gzip')

            c.perform()
            self.get_result(c)
        except:
            pass
        
    def get_result(self, c):
        self._result = {
            'task_type':                self._task['task_type'],
            'task_id':                  self._task['task_id'],
            'detect_point':             self._detect_point,
            'proxy_ip':                 self._proxy_ip,
            'proxy_port':               self._proxy_port,
            'parsed_host':              urlparse(self._task['task_target']).netloc,
            'server_ip':                c.getinfo(pycurl.PRIMARY_IP),
            'url':                      c.getinfo(pycurl.EFFECTIVE_URL),
            'content_type':             c.getinfo(pycurl.CONTENT_TYPE),
            'http_code':                c.getinfo(pycurl.HTTP_CODE),
            'header_size':              c.getinfo(pycurl.HEADER_SIZE),
            'request_size':             c.getinfo(pycurl.REQUEST_SIZE),
            'filetime':                 c.getinfo(pycurl.INFO_FILETIME),
            'ssl_verify_result':        c.getinfo(pycurl.SSL_VERIFYRESULT),
            'total_time':               c.getinfo(pycurl.TOTAL_TIME),
            'namelookup_time':          c.getinfo(pycurl.NAMELOOKUP_TIME),
            'connect_time':             c.getinfo(pycurl.CONNECT_TIME),
            'pretransfer_time':         c.getinfo(pycurl.PRETRANSFER_TIME),
            'starttransfer_time' :      c.getinfo(pycurl.STARTTRANSFER_TIME),
            'size_upload':              c.getinfo(pycurl.SIZE_UPLOAD),
            'size_download' :           c.getinfo(pycurl.SIZE_DOWNLOAD),
            'speed_download':           c.getinfo(pycurl.SPEED_DOWNLOAD),
            'speed_upload' :            c.getinfo(pycurl.SPEED_UPLOAD),
            'download_content_length':  c.getinfo(pycurl.CONTENT_LENGTH_DOWNLOAD),
            'upload_content_length':    c.getinfo(pycurl.CONTENT_LENGTH_UPLOAD),
            'redirect_count':           c.getinfo(pycurl.REDIRECT_COUNT),
            'redirect_time':            c.getinfo(pycurl.REDIRECT_TIME),
            'redirect_url':             c.getinfo(pycurl.REDIRECT_URL),
            'response_header':          self._head_info.getvalue().decode('utf-8', 'ignore'),
            'http_content':             self._body_content.getvalue().decode('utf-8', 'ignore'),
            'record_time':              int(time.time())
        }
        
    def run(self):
        self.do_task()
        self.save_to_cache()
        
if __name__ == '__main__':
    task = {"task_id": "81bc5596608111e3a67210604b7e490e", 
            "http_content": True, 
            "http_user_agent": "", 
            "isps": [], 
            "locates": [], 
            "http_gzip": False, 
            "real_time": False, 
            "is_del": False, 
            "transf_timeout": 5, 
            "http_proxy": "", 
            "task_name": "Http\u63a2\u6d4b", 
            "task_target": "http://www.baidu.com", 
            "task_type": "Http", 
            "http_host": "", 
            "interval": 1, 
            "conn_timeout": 3, 
            "http_referer": "", 
            "http_cookie": "", 
            "http_redirect": False, 
            "http_limit_rate": "", 
            "end_time": 1389151492}

    ht = Http(task)
    ht.run()