#!/usr/bin/env python

import collections
import functools
import sys
import threading
import time
import traceback


def timer(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        time_one = time.time()
        result = f(*args, **kwargs)
        time_two = time.time()
        print("%.03f seconds: %s" % (time_two - time_one, f.__name__))
        return result
    return wrapper


@timer
def work():
    work_spin_loop(64)
    work_spin_fast(64)
    work_time_wait(1.00)

@timer
def work_spin_loop(size: int):
    s = 0
    for i in range(size * 1024 ** 2):
        s += i
    return s

@timer
def work_spin_fast(size: int):
    return sum(range(size * 1024 ** 2))

@timer
def work_time_wait(wait: float):
    return time.sleep(wait)


profiler_finish = threading.Event()
profiler_thread = None


def profiler_enable(sampling_interval: float):
    global profiler_thread
    assert profiler_thread is None
    profiler_thread = threading.Thread(target = profiler, args = [sampling_interval], daemon = True)
    profiler_finish.clear()
    profiler_thread.start()

def profiler_disable():
    global profiler_thread
    assert profiler_thread is not None
    profiler_finish.set()
    profiler_thread.join()


def profiler(sampling_interval: float):
    profiler_thread_id = threading.get_ident()
    samples_counter = collections.Counter()
    seconds_counter = collections.Counter()
    last_sampled_at_time = time.time()
    while True:
        this_sampled_at_time = time.time()
        this_sample_duration = this_sampled_at_time - last_sampled_at_time
        last_sampled_at_time = this_sampled_at_time
        for thread_id, thread_frame in sys._current_frames().items():
            if thread_id == profiler_thread_id:
                continue
            traceback_frames = traceback.extract_stack(thread_frame)
            formatted_sample = " ".join("%s:%s:%i" % (f.filename, f.name, f.lineno) for f in traceback_frames)
            samples_counter[formatted_sample] += 1
            seconds_counter[formatted_sample] += this_sample_duration
        if profiler_finish.wait(sampling_interval):
            break
    for formatted_sample in samples_counter:
        total_samples = samples_counter[formatted_sample]
        total_seconds = seconds_counter[formatted_sample]
        print("%.03f seconds; %4d samples: %s" % (total_seconds, total_samples, formatted_sample))


if __name__ == '__main__':
    profiler_enable(0.01)
    work()
    profiler_disable()
