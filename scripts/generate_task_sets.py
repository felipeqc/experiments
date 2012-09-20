import random
import sys
import os
import subprocess
from math import ceil
from functools import partial
import xml.dom.minidom as minidom
import multiprocessing
import tempfile

import litmus
import topology
from ts_params import setup_parameters

EXPERIMENTS_DIR = os.getenv('EXPERIMENTS', '/home/felipe/experiments')
TASKSETS_DIR = os.path.join(EXPERIMENTS_DIR, 'tasksets')
ALLOCATION_DIR = os.path.join(EXPERIMENTS_DIR, 'allocation')

def alloc_hime(taskset, host):
    fname = '.taskset' + str(os.getpid())
    try:
        f = open(fname, 'w')
        for task in taskset.getElementsByTagName("task"):
            f.write("%f %f %f\n" % (float(task.getAttribute('wcet')), float(task.getAttribute("period")), float(task.getAttribute('period'))))
    except IOError as (msg):
        raise IOError("Could not create temporary file: %s", (msg))
    finally:
        f.close()

    try:
        proc = subprocess.Popen(os.path.join(ALLOCATION_DIR, 'hime') + ' -u -f -m%d -l %s' % (topology.CPUS[host], fname), shell=True, stdout=subprocess.PIPE)
        output = proc.communicate()[0]

        if(output[0] == '1'): # Schedulable?
            return minidom.parseString(output[2:len(output)]) # Parse task set
        else:
            return None
    except OSError as (msg):
        raise OSError("Could not create taskset '%s': %s" % (fname, msg))    

def alloc_edfwm(taskset, host, maxdbftime):
    fname = '.taskset' + str(os.getpid())
    try:
        f = open(fname, 'w')
        for task in taskset.getElementsByTagName("task"):
            f.write("%f %f %f\n" % (float(task.getAttribute('wcet')), float(task.getAttribute("period")), float(task.getAttribute('period'))))
    except IOError as (msg):
        raise IOError("Could not create temporary file: %s", (msg))
    finally:
        f.close()

    try:
        proc = subprocess.Popen(os.path.join(ALLOCATION_DIR, 'edfwm') + ' -p -f -m%d -t %d -l %s' % (topology.CPUS[host], maxdbftime, fname), shell=True, stdout=subprocess.PIPE)
        output = proc.communicate()[0]

        if(output[0] == '1'): # Schedulable?
            return minidom.parseString(output[2:len(output)]) # Parse task set
        else:
            return None
    except OSError as (msg):
        raise OSError("Could not create taskset '%s': %s" % (fname, msg))  

def allocate_taskset(taskset, host, sched, ts_params):
    # Validate task set

    if ts_params[sched]['max_hyperperiod'] is not None:
        hp = int(taskset.getElementsByTagName("properties")[0].getAttribute('hyperperiod')) # Task set hyperperiod
        if hp > ts_params[sched]['max_hyperperiod']:
            return None

    allocated_taskset = None
    if(sched == 'HIME'):
        allocated_taskset = alloc_hime(taskset, host)
    elif(sched == 'EDF-WM'):
        allocated_taskset = alloc_edfwm(taskset, host, ts_params['EDF-WM']['max_dbf_time'])
    if allocated_taskset == None:
        return None

    if ts_params[sched]['max_percpu_hyperperiod'] is not None:
        percpu_hp = int(allocated_taskset.getElementsByTagName("properties")[0].getAttribute('max_percpu_hyperperiod'))
        if percpu_hp > ts_params[sched]['max_percpu_hyperperiod']:
            return None

    if (sched == 'HIME' or sched == 'EDF-WM') and (ts_params[sched]['min_slice_size'] is not None):
         for s in allocated_taskset.getElementsByTagName("slice"):
             if float(s.getAttribute('budget')) < ts_params[sched]['min_slice_size']:
                 return None

    return allocated_taskset

def make_taskset_file(host, sched, num, idx, ts_params, force_mig = False):
    fname = 'taskset_scheduler=%s_host=%s_n=%d_idx=%02d.ts' % \
                    (sched, host, num, idx)
    allocfname = 'taskset_scheduler=%s_host=%s_n=%d_idx=%02d.ats' % \
                    (sched, host, num, idx)
    path = 'taskgen -s 1 -n %d -u %f -p %d -q %d -g %d -d logunif' % \
                (num, random.uniform(ts_params[sched]['min_percpu_util'], \
                    ts_params[sched]['max_percpu_util'])*topology.CPUS[host], \
                    ts_params[sched]['min_period'], \
                    ts_params[sched]['max_period'], \
                    ts_params[sched]['gran_period'])

    allocation = None
    while allocation is None:
        try:
            proc = subprocess.Popen(path, shell=True, stdout=subprocess.PIPE)
            output = proc.communicate()[0]

            taskset = minidom.parseString(output)
            allocation = allocate_taskset(taskset, host, sched, ts_params)

            if force_mig == True and allocation is not None: # Force migratory tasks
                if not allocation.getElementsByTagName("slice"):
                    allocation = None

            if allocation is not None: # Task set was successfully allocated
                taskset_noxmlheader = taskset.getElementsByTagName("taskset")[0] # Remove <? xml...?>
                taskset_noxmlheader.writexml(open(os.path.join(TASKSETS_DIR, host, fname), 'w'))
                allocation_noxmlheader = allocation.getElementsByTagName("taskset")[0] # Remove <? xml...?>
                allocation_noxmlheader.writexml(open(os.path.join(TASKSETS_DIR, host, allocfname), 'w'))
        except OSError as (msg):
            raise OSError("Could not create taskset '%s': %s" % (fname, msg))

def make_taskset_file_wrapper(args):
    return make_taskset_file(*args)

def make_tasksets_multi(host, schedulers, ts_params):
    ts_dir = os.path.join(TASKSETS_DIR, host)
    try:
        if not os.path.exists(ts_dir):
            os.makedirs(ts_dir)
    except OSError as (msg):
        raise OSError ("Could not create task set directory: %s", (msg))

    # Make a list of the task sets to be generated: (host, sched, n, index, ts_params, force_mig) pairs
    ts_list = []

    for sched in schedulers:
        for n in ts_params[sched]['n_values']:

            mig_samples = 0
            idx = 1

            if n in ts_params['HIME']['n_values_with_forced_mig']:
                while mig_samples < ts_params[sched]['min_mig_samples']:
                    ts_list.append((host, sched, n, idx, ts_params, True))
                    mig_samples += 1
                    idx += 1

            while idx <= ts_params[sched]['samples']:
                ts_list.append((host, sched, n, idx, ts_params))
                idx += 1

    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    pool.map(make_taskset_file_wrapper, ts_list, 50) 

    pool.close()
    pool.join()

def make_tasksets(host, schedulers, ts_params):
    ts_dir = os.path.join(TASKSETS_DIR, host)
    try:
        if not os.path.exists(ts_dir):
            os.makedirs(ts_dir)
    except OSError as (msg):
        raise OSError ("Could not create task set directory: %s", (msg))

    for sched in schedulers:
        print 'Scheduler %s' % (sched)
        for n in ts_params[sched]['n_values']:
            print '%2d tasks ' % n,
            sys.stdout.flush()

            mig_samples = 0
            idx = 1

            if n in ts_params['HIME']['n_values_with_forced_mig']:
                while mig_samples < ts_params[sched]['min_mig_samples']:
                    make_taskset_file(host, sched, n, idx, ts_params, True)
                    mig_samples += 1
                    idx += 1
                    print '*',
                    sys.stdout.flush()

            while idx <= ts_params[sched]['samples']:
                make_taskset_file(host, sched, n, idx, ts_params)
                idx += 1
                print '*',
                sys.stdout.flush()
            print

def main(args=sys.argv):
    ts_params = setup_parameters('felipe')
    make_tasksets_multi('felipe', litmus.SEMIPARTITIONED, ts_params)
    #make_tasksets('felipe', litmus.SEMIPARTITIONED, ts_params)

if __name__ == '__main__':
    main()
