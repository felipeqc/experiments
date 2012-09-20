from os import path, getenv, listdir, makedirs
import subprocess
import sys
import xml.dom.minidom as minidom

from proc import spawn
from litmus import release_taskset
from feathertrace import ftcat, SCHED_EVENTS

import litmus
import topology

COMPUTE_TASK    = 'compute-task'
COMPUTE_TASK_EDFWM    = 'compute-task-edfwm'
COMPUTE_TASK_HIME    = 'compute-task-hime'
BACKGROUND_TASK = 'background-task'
LOCK_TASK       = 'lockstress'
SPIN_TASK       = 'spinlock-task'

RUNLENGTH = 60

EXPERIMENTS_DIR = getenv('EXPERIMENTS', '/home/felipe/experiments')
ALLOCATION_DIR = path.join(EXPERIMENTS_DIR, 'allocation')
RESULTS_DIR = path.join(EXPERIMENTS_DIR, 'results')

def task_args(task, wait=True):
    args = ['-P', int(task.period),
            '-E', int(task.cost),
            '-T', RUNLENGTH
            ]
    if wait:
        args.append('-w')
    if not task.cpu is None:
        args += ['-p', task.cpu]
    if not task.priority is None:
        args += ['-Q', task.priority]

    binary = COMPUTE_TASK

    return (binary, args)

def run_task(task, *args, **kargs):
    (binary, args) = task_args(task, *args, **kargs)
    return spawn(binary, args,
                 path=EXPERIMENTS_DIR)

def run_tasks(tasks, sched):
    procs = []

    if sched == 'HIME':
        task_id = 0
        for task in tasks.getElementsByTagName("task"): # For each task
            task_id += 1
            task_path = ".task_input_hime_" + str(task_id)
            try:
                f = open(task_path, "w")
                if not task.getAttribute("slices"):
                    wcet = float(task.getAttribute("wcet"))
                    period = int(task.getAttribute("period"))
                    cpu = int(task.getAttribute("cpu"))

                    f.write("%d %f %d 0 %d 0" % (task_id, wcet, period, cpu))
                else:
                    wcet = float(task.getAttribute("wcet"))
                    period = int(task.getAttribute("period"))
                    first_cpu = int(task.getAttribute("cpu"))
                    slice_num = int(task.getAttribute("slices"))

                    f.write("%d %f %d 0 %d %d\n" % (task_id, wcet, period, first_cpu, slice_num))
                    for slice in task.getElementsByTagName("slice"): # For each slice
                        slice_cpu = int(slice.getAttribute("cpu"))
                        slice_budget = float(slice.getAttribute("budget"))
                        f.write("%d %d %f\n" % (task_id, slice_cpu, slice_budget))
                        
            except IOError as (msg):
                raise IOError("Could not create temporary file: %s", (msg))
            finally:
                f.close()
                procs += [spawn(path.join(EXPERIMENTS_DIR, COMPUTE_TASK_HIME), ["-w", "-T", RUNLENGTH, task_path])]

    elif sched == 'EDF-WM':
        task_id = 0
        for task in tasks.getElementsByTagName("task"): # For each task
            task_id += 1
            task_path = ".task_input_wm_" + str(task_id)
            try:
                f = open(task_path, "w")
                if not task.getAttribute("slices"):
                    wcet = float(task.getAttribute("wcet"))
                    period = int(task.getAttribute("period"))
                    cpu = int(task.getAttribute("cpu"))

                    f.write("%d %f %d 0 %d 0" % (task_id, wcet, period, cpu))
                else:
                    wcet = float(task.getAttribute("wcet"))
                    period = int(task.getAttribute("period"))
                    first_cpu = int(task.getAttribute("cpu"))
                    slice_num = int(task.getAttribute("slices"))

                    f.write("%d %f %d 0 %d %d\n" % (task_id, wcet, period, first_cpu, slice_num))

                    for slice in task.getElementsByTagName("slice"): # For each slice
                        slice_cpu = int(slice.getAttribute("cpu"))
                        slice_deadline = float(slice.getAttribute("deadline"))
                        slice_budget = float(slice.getAttribute("budget"))
                        slice_offset = float(slice.getAttribute("offset"))
                        f.write("%d %d %f %f %f\n" % (task_id, slice_cpu, slice_deadline, slice_budget, slice_offset))
                        
            except IOError as (msg):
                raise IOError("Could not create temporary file: %s", (msg))
            finally:
                f.close()
                procs += [spawn(path.join(EXPERIMENTS_DIR, COMPUTE_TASK_EDFWM), ["-w", "-T", RUNLENGTH, task_path])]

    # wait for release
    release_taskset(num_tasks=len(procs)).wait()

    # wait for all tasks to terminate
    for p in procs:
        p.wait()
        assert p.returncode == 0

def trace_taskset(tasks, trace_file, sched):
    events = SCHED_EVENTS
    tracer = ftcat(trace_file, events=events)
    try:
        run_tasks(tasks, sched)
    finally:
        # tear down ftcat
        tracer.terminate()
        tracer.wait()

def start_background_tasks(num_cpus):
    return [spawn(BACKGROUND_TASK, [cpu], path=EXPERIMENTS_DIR)
            for cpu in xrange(num_cpus)]

def stop_background_tasks(bg_tasks):
    for t in bg_tasks:
        t.terminate()
    for t in bg_tasks:
        t.wait()

def decode(name):
    params = {}
    parts = name.split('_')
    for p in parts:
        kv = p.split('=')
        k = kv[0]
        v = kv[1] if len(kv) > 1 else None
        params[k] = v
    return params

def get_config(fname):
    return path.splitext(path.basename(fname))[0]

def get_data_file(fname):
    trace_file = get_config(fname)
    return "%s.ft" % trace_file 

def experiment(fname):
    params = decode(get_config(fname))
    sched = params['scheduler']
    host  = params['host']

    trace_dir = path.join(RESULTS_DIR, host)
    try:
        if not path.exists(trace_dir):
            makedirs(trace_dir)
    except OSError as (msg):
        raise OSError ("Could not create results directory: %s", (msg))

    tname = path.join(trace_dir, get_data_file(fname))

    if path.exists(tname):
        print "Skipped: %s exists." % tname
    else:
        print 'Running %s.' % fname

        try:
            tasks = minidom.parse(fname)
        except IOError as (msg):
            raise IOError("Could not read task set file: %s", (msg))

        bg = start_background_tasks(topology.CPUS[host])
        try:
            litmus.activate_scheduler(sched)
            trace_taskset(tasks, tname, sched)
            print 'Completed!'
        finally:
            stop_background_tasks(bg)


# for each selected scheduler
# for each task set in a directory
