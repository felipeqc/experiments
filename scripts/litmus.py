from proc import cat, echo, chomp, echo_and_test, spawn

import os

LITMUS_ACTIVE_PLUGIN  = '/proc/litmus/active_plugin'
LITMUS_LOADED_PLUGINS = '/proc/litmus/plugins/loaded'
LITMUS_PLUGIN_DIR     = '/proc/litmus/plugins'
LITMUS_RELEASE_MASTER = '/proc/litmus/release_master'

# Path to external tools. If None, then the shell is invoked to find them based
# on the current PATH.
LIBLITMUS             = os.getenv('LIBLITMUS', '/home/felipe/litmus/litmus-semi/liblitmus')
FT_TOOLS              = os.getenv('FT_TOOLS', '/home/felipe/litmus/litmus-semi/ft_tools')

def get_active_plugin():
    return chomp(cat(LITMUS_ACTIVE_PLUGIN))

def set_active_plugin(plugin):
    echo_and_test(plugin, LITMUS_ACTIVE_PLUGIN)

def set_cluster_size(plugin, cluster):
    cluster_file = "%s/%s/cluster" % (LITMUS_PLUGIN_DIR, plugin)
    echo_and_test(cluster, cluster_file)

def get_release_master():
    return chomp(cat(LITMUS_RELEASE_MASTER))

def set_release_master(cpu='NO_CPU'):
    echo_and_test(cpu, LITMUS_RELEASE_MASTER)

SCHEDULERS = {

    # EDF family
    'P-EDF'    : ('PSN-EDF',  None, None),
    'C-EDF-L2' : ('C-EDF',    'L2', None),
    'C-EDF-L3' : ('C-EDF',    'L3', None),
    'C-EDF-ALL': ('C-EDF',   'ALL', None),
    'G-EDF'    : ('GSN-EDF',  None, None),

    # Pfair family
    'PD2-L2'   : ('PFAIR',    'L2', None),
    'PD2-L3'   : ('PFAIR',    'L3', None),
    'PD2'      : ('PFAIR',   'ALL', None),

    # Future plugins?
    'G-FP'     : ('C-FP',    'ALL', None),
    'C-FP-L2'  : ('C-FP',     'L2', None),
    'C-FP-L3'  : ('C-FP',     'L3', None),
    'P-FP'     : ('P-FP',     None, None),

    # Global and clustered with dedicated interrupt handling
    'P-EDF-RM'    : ('PSN-EDF',  None,  '0'),
    'C-EDF-L2-RM' : ('C-EDF',    'L2',  '0'),
    'C-EDF-L3-RM' : ('C-EDF',    'L3',  '0'),
    'C-EDF-ALL-RM': ('C-EDF',   'ALL',  '0'),
    'G-EDF-RM'    : ('GSN-EDF',  None,  '0'),

    'P-FP-RM'     : ('P-FP',     None,  '0'),
    'C-FP-L2-RM'  : ('C-FP',     'L2',  '0'),
    'C-FP-L3-RM'  : ('C-FP',     'L3',  '0'),
    'G-FP-RM'     : ('C-FP',    'ALL',  '0'),

    'PD2-L2-RM'   : ('PFAIR',    'L2',  '0'),
    'PD2-L3-RM'   : ('PFAIR',    'L3',  '0'),
    'PD2-RM'      : ('PFAIR',   'ALL',  '0'),

    # Semi-partitioned family
    'HIME'     : ('HIME', None, None),   
    'EDF-WM'   : ('EDF-WM', None, None),
}

ALL = set(SCHEDULERS.keys())

GLOBAL      = set([s for s in ALL
                   if s.startswith('G-') or s == 'PD2' or s == 'PD2-RM'])

PARTITIONED = set([s for s in ALL
                   if s.startswith('P-')])

CLUSTERED = set([s for s in ALL
                 if not (s in PARTITIONED or s in GLOBAL)])

RELEASE_MASTER = set([s for s in ALL
                      if s.endswith('-RM')])

STATIC_PRIO = set([s for s in ALL
                   if '-FP' in s])

SEMIPARTITIONED = set([s for s in ALL
                       if s == 'EDF-WM'])
                       #if s == 'HIME' or s == 'EDF-WM'])
                       #if s == 'HIME'])

LOCKING_PROTOCOLS = {
    'P-FP'    : ['FMLP', 'MPCP', 'MPCP-VS', 'DPCP', 'MX-Q', 'TF-Q', 'PF-Q'],
    'C-EDF'   : ['OMLP', 'MX-Q', 'TF-Q', 'PF-Q'],
    'PSN-EDF' : ['OMLP', 'FMLP', 'MX-Q', 'TF-Q', 'PF-Q'],
    'GSN-EDF' : ['OMLP', 'FMLP', 'MX-Q', 'TF-Q', 'PF-Q'],
}

SPINLOCKS = set(['MX-Q', 'PF-Q', 'TF-Q'])
SEMAPHORE = set(['FMLP', 'OMLP', 'MPCP', 'MPCP-VS', 'DPCP'])

def activate_scheduler(name):
    plugin, cluster, rm = SCHEDULERS[name]

    # Play it safe and switch to Linux first.
    set_active_plugin('Linux')

    # Config cluster size for cluster-aware plugins.
    if cluster:
        set_cluster_size(plugin, cluster)

    # Set or reset release master.
    set_release_master(rm if rm != None else 'NO_CPU')

    # Activate plugin.
    set_active_plugin(plugin)


def release_taskset(wait=True, delay=None, num_tasks=None):
    cmd = []
    if wait:
        cmd.append('-w')
    if delay != None:
        cmd.append('-d')
        cmd.append(delay)
    if num_tasks:
        cmd.append('-f')
        cmd.append(num_tasks)
    return spawn('release_ts', cmd,
                 path=LIBLITMUS)
