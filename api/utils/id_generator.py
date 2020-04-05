import numpy as np
import time


# Logic of this was copied from https://gist.github.com/risent/4cab3878d995bec7d1c2
class IDGenerator:

    PUSH_CHARS = ('-0123456789'
                  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                  '_abcdefghijklmnopqrstuvwxyz')
    last_push_time = 0
    last_rand_chars = np.empty(12, dtype=int)

    @classmethod
    def generate_id(cls):
        now = int(time.time() * 1000)
        duplicate_time = (now == cls.last_push_time)
        cls.last_push_time = now
        time_stamp_chars = np.empty(8, dtype=str)

        for i in range(7, -1, -1):
            time_stamp_chars[i] = cls.PUSH_CHARS[now % 64]
            now = int(now / 64)

        uid = ''.join(time_stamp_chars)
        if not duplicate_time:
            cls.last_rand_chars = np.random.randint(low=0, high=63, size=12)
        else:
            cls.last_rand_chars = np.where(cls.last_rand_chars == 63, 0,
                                           cls.last_rand_chars + 1)

        string_mapper = np.vectorize(
            cls._get_vectorize_func(cls.PUSH_CHARS, cls.last_rand_chars))

        sample = string_mapper(np.arange(12))

        return uid + ''.join(sample)

    @classmethod
    def _get_vectorize_func(cls, chars, last_chars):
        def vectorize_func(index):
            return chars[last_chars[index]]

        return vectorize_func
