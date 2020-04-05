import os
import redis
from datetime import timedelta
from tests.mock import RedisMock


class RedisUtil:
    REDIS = RedisMock
    if os.getenv('FLASK_ENV') != 'testing':
        REDIS = redis.from_url(os.getenv('REDIS_SERVER_URL'))

    @classmethod
    def set(cls, key, value, **exp_time_delta_kwargs):
        cls.REDIS.set(key, value)
        if exp_time_delta_kwargs:
            delta = timedelta(**exp_time_delta_kwargs)
            cls.REDIS.expire(key, int(delta.total_seconds()))

    @classmethod
    def get(cls, key: str):
        return cls.REDIS.get(key)

    @classmethod
    def hset(cls, hash_name, key, value, **exp_time_delta_kwargs):
        custom_key = f'{hash_name}_{key}'
        cls.set(custom_key, value, **exp_time_delta_kwargs)

    @classmethod
    def _get_psedu_hash_key(cls, hash_name, key):
        return f'{hash_name}_{key}'

    @classmethod
    def hget(cls, hash_name, key):
        value = cls.REDIS.get(cls._get_psedu_hash_key(hash_name, key))
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    @classmethod
    def hdel(cls, hash_name, key):
        return cls.REDIS.delete(cls._get_psedu_hash_key(hash_name, key))

    @classmethod
    def find_keys(cls, regex):
        final_list = []
        for key in cls.REDIS.keys(regex):
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            final_list.append(key)
        return final_list

    @classmethod
    def delete_hash(cls, hash_name):
        hash_keys = cls.find_keys(f'{hash_name}_*')
        for key in hash_keys:
            cls.REDIS.delete(key)
