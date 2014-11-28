#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

"""
slave进程控制器
解析命令行参数
维护子进程状态字典
"""
import os
import os.path
import sys
import json
import time
import signal
import urllib
import argparse
import multiprocessing

from lib import utils
from src import MainLoop
from config import settings

class Monitor(object):
    def __init__(self):
        self._process_status = {}
        self._process_name = ['GetTask', 'Search', 'PostData']
        self._main_loop = MainLoop.Loop()
    
    def initialize(self):
        pass
    
    def _init_env(self):
        if not os.path.exists(settings.ERROR_LOG_PATH):
            os.makedirs(settings.ERROR_LOG_PATH)
        if not os.path.exists(settings.PID_PATH):
            os.makedirs(settings.PID_PATH)
        path = os.path.dirname(os.path.realpath(__file__))
        file_list = os.listdir(path)
        pp = []
        for fl in file_list:
            tmp = os.path.join(path, fl)
            if os.path.isdir(tmp):
                pp.append(tmp)
        sys.path.extend(pp)
 
    def _register(self):
        if os.path.exists(settings.SLAVE_KEY_PATH):
            with open(settings.SLAVE_KEY_PATH) as f:
                res = f.read().strip()
            if res: return
        try:
            json_data = urllib.urlopen(settings.REGISTER_URL).read()
            res = json.loads(json_data)
            if res['code'] == 0:
                with open(settings.SLAVE_KEY_PATH, 'w') as f:
                    f.write(res['data'])
            else:
                sys.exit('Register failed : error => %s' % res['data'])
        except:
            sys.exit('Register failed : network connect error')
    
    def _save_main_pid(self):
        if os.path.exists(settings.MAIN_PID):
            sys.exit('Main Pid exists !!!')
        else:
            with open(settings.MAIN_PID, 'w') as f:
                f.write(str(os.getpid()))
            self._register()

    def _init_all_process(self):
        for proc_name in self._process_name:
            if proc_name == 'Search':
                for num in range(multiprocessing.cpu_count()):
                    self._start_process_by_name(proc_name)
            else:
                self._start_process_by_name(proc_name)
            time.sleep(3)

    def _start_process_by_name(self, proc_name):
        self._main_loop.auto_load(proc_name)
        process = multiprocessing.Process(target=self._main_loop.run)
        process.daemon = True
        process.start()
        self._process_status.setdefault(process.pid, [proc_name, process])

    def _check_loop(self):
        while True:
            self._check_process_is_alive()
            time.sleep(10)

    def _check_process_is_alive(self):
        for pid, status in self._process_status.items():
            if not status[1].is_alive():
                utils.clean_pid(pid)
                self._process_status.pop(pid)
                try:
                    os.kill(pid, signal.SIGKILL)
                except:
                    pass
                self._start_process_by_name(status[0])
                
    def clean_env(self):
        root_path = settings.BASE_PATH
        self._recurse_delete(root_path)
    
    def _recurse_delete(self, root_path):
        if os.path.exists(root_path):
            if os.path.isdir(root_path):
                file_list = os.listdir(root_path)
                for fl in file_list:
                    path = os.path.join(root_path, fl)       
                    self._recurse_delete(path)    
            elif os.path.isfile(root_path):
                if root_path.find('slave.key') == -1:
                    print 'delete ', root_path
                    os.remove(root_path)
    
    def run(self):
        self._init_env()
        self._save_main_pid()
        print 'monitor initiallizing...'
        time.sleep(2)
        utils.daemonize(stdin='/dev/null', stdout='/tmp/monitor.log', stderr='/tmp/monitor.log')
        self._init_all_process()
        self._check_loop()

    def _get_all_pid(self):
        pid_list = []
        if os.path.exists(settings.MAIN_PID):
            with open(settings.MAIN_PID) as f:
                pid_list.append(f.read().strip())
        pid_list.extend(os.listdir(settings.PID_PATH))
        return pid_list

    def kill_all(self):
        for pid in self._get_all_pid():
            try:
                os.kill(int(pid), signal.SIGKILL)
            except:
                pass
        self.clean_env()
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='slave 主控')
    parser.add_argument('--start', action='store_true', dest='start', default=False, help='启动monitor主程序')
    parser.add_argument('--stop',  action='store_true', dest='stop',  default=False, help='停止monitor主程序')
    parser.add_argument('--clean', action='store_true', dest='clean', default=False, help='清除monitor执行环境')
    args = parser.parse_args()   
    
    monitor = Monitor()
    if len(sys.argv) != 2:
        parser.print_help()
        sys.exit()   
    elif args.clean:
        monitor.clean_env()
        sys.exit('ok')
    elif args.stop:
        monitor.kill_all()
        sys.exit('ok')
    elif args.start:
        monitor.run()
        sys.exit('ok')