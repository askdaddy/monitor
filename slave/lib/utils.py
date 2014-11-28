#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import os
import sys
import traceback
import time
from config import settings
        
#进程pid缓存
def save_pid_to_cache():
    pid = str(os.getpid())
    with open(os.path.join(settings.PID_PATH, pid), 'w') as f:
        f.write(pid)
     
#清除pid文件  
def clean_pid(pid = None):
    if pid is None:
        pid = str(os.getpid())
    pid_path = os.path.join(settings.PID_PATH, str(pid))
    if os.path.exists(pid_path):
        os.remove(pid_path)
        
#记录异常信息
def log_except_traceback(file_name):
    ex = traceback.format_exc()
    log_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    log = os.path.realpath(file_name).split('/')[-1].split('.')[0] + '.log'
    with open(os.path.join(settings.ERROR_LOG_PATH, log), 'a+') as f:
        f.writelines([log_time + '\n', ex + '\n'])
        
def print_traceback():
    traceback.print_exc()        

#获取agent key
def get_slave_key():
    with open(settings.SLAVE_KEY_PATH) as f:
        return f.read().strip()

#守护进程方法
def daemonize(stdin='/dev/null',stdout='/dev/null',stderr='/dev/null'):
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError,e:
        sys.stderr.write("fork #1 failed:(%d) %s \n" % (e.errno, e.strerror))
        sys.exit(1)
    os.chdir("/")
    os.umask(0)
    os.setsid()
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError,e:
        sys.stderr.write("fork #2 failed: (%d) %s \n" % (e.errno, e.strerror))
        sys.exit(1)
        
    for f in sys.stdout,sys.stderr:f.flush()
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())