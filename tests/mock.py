import re


class RedisMock:
    cache = {}
    expired_cache = {}

    @classmethod
    def set(cls, key, value):
        cls.cache[key] = value

    @classmethod
    def delete(cls, key):
        if key in cls.cache:
            del cls.cache[key]
            return 1
        return 0

    @classmethod
    def keys(cls, regex):
        matching_keys = []

        for key in cls.cache.keys():
            if re.match(regex, key):
                matching_keys.append(key)
        return matching_keys

    @classmethod
    def get(cls, key):
        return cls.cache.get(key)

    @classmethod
    def expire(cls, key, exp_time):
        cls.expired_cache[key] = exp_time

    @classmethod
    def flush_all(cls):
        cls.cache = {}
        cls.expired_cache = {}
