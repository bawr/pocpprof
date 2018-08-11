#!/usr/bin/env python

import collections
import sys
import threading
import time
import traceback
import vmprof


prof_finish = threading.Event()
profiler_thread = None


def work():
    return time.sleep(4.0)


def wait():
    return time.sleep(1.0)


def main_prof(sampling_interval: float):
    vmprof.insert_real_time_thread()
    prof_thread_id = threading.get_ident()
    stack_frames_sampled = collections.Counter()
    while True:
        current_frames = sys._current_frames()
        for thread_id, thread_frame in current_frames.items():
            if thread_id == prof_thread_id:
                continue
            thread_stack = traceback.extract_stack(thread_frame)
            for single_frame in thread_stack:
                stack_frames_sampled[(thread_id, single_frame.filename, single_frame.lineno)] += 1
        if prof_finish.wait(sampling_interval):
            for (thread_id, filename, lineno), count in stack_frames_sampled.most_common(100):
                print("%.02f %d %s:%d" % (count * sampling_interval, thread_id, filename, lineno))
            wait()
            return


def prof_enable(sampling_interval = 0.001):
    global profiler_thread
    assert prof_thread is None
    prof_thread = threading.Thread(target=main_prof, args=[sampling_interval], daemon=True)
    prof_finish.clear()
    prof_thread.start()


def prof_disable():
    global profiler_thread
    assert prof_thread is not None
    prof_finish.set()
    prof_thread.join()


def main(sampling_interval: float, use_vmprof: bool, use_pocpprof: bool):
    if use_vmprof:
        file = open('prof.log', 'w+b')
        vmprof.enable(file.fileno(), period = sampling_interval, lines = True, native = True, real_time = True)
    if use_pocpprof:
        prof_enable(sampling_interval)

    work()

    if use_pocpprof:
        prof_disable()
    if use_vmprof:
        vmprof.disable()


if __name__ == '__main__':
    main(0.01, True, True)
