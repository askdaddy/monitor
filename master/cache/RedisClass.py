#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import redis
from conf import config

"""
Redis操作类
实现各种数据结构
队列，哈希表，集合等等
"""

ConnPool = redis.ConnectionPool(host = config.rhost, port = config.rport, db = config.rdb)


class RedisConn(object):
    """Redis 连接对象，管理 """
    def __init__(self, namespace = '标识一个指定的应用', data_type = 'Queue_or_Hash_or_other'):
        self._db = redis.StrictRedis(connection_pool = ConnPool)
        self._key = '%s:%s' % (data_type, namespace)
    
    def operator_about_redis_info(self):
        """数据库信息"""
        pass


# Redis操作类示例
class OtherRedis(RedisConn):
    """继承RedisConn基本结构"""
    def __init__(self, namespace = '', ):
        RedisConn.__init__(self, namespace, data_type = 'should be fixed')

    def do(self):
        self._db(self._key, 'other')



class RedisQueue(RedisConn):
    """队列基本操作"""
    def __init__(self, namespace = 'Redis'):
        RedisConn.__init__(self, namespace, data_type = 'Queue')

    def qsize(self):
        return self._db.llen(self._Key)
    
    def empty(self):
        return self.qsize() == 0
    
    def put(self, item):
        self._db.rpush(self._key, item)

    def get(self, block = True, timeout = None):
        if block :
            return self._db.blpop(self._key, timeout = timeout)[1]
        else:
            return self._db.lpop(self._key)
        
    def get_nowait(self):
        return self.get(False)
    

class RedisHash(RedisConn):
    """哈希表基本操作"""
    def __init__(self, namespace = 'Redis'):
        RedisConn.__init__(self, namespace, data_type = 'Hash')
    
    def hexists(self, field):
        return self._db.hexists(self._key, field)
        
    def hget(self, field):
        return self._db.hget(self._key, field)
    
    def hset(self, field, value):
        self._db.hset(self._key, field, value)
        
    def hdel(self, *fields):
        self._db.hdel(self._key, *fields)
    
    def get_all(self):
        return self._db.hgetall(self._key)
    
    def get_all_keys(self):
        return self._db.hkeys(self._key)
        
    
class RedisSet(RedisConn):
    """集合基本操作"""
    def __init__(self, namespace = 'Redis'):
        RedisConn.__init__(self, namespace, data_type = 'Set')
                
    def is_exists(self, member):
        return self._db.sismember(self._key, member)
    
    def size(self):
        return self._db.scard(self._key)
    
    def sdel(self, *member):
        self._db.srem(self._key, *member)
        
    def sadd(self, *member):
        self._db.sadd(self._key, *member)
        
