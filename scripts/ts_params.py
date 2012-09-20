import topology
import litmus

# Parameters for task set generation

def setup_parameters(host):
    # Parameters #
    ts_params = dict([(x, {}) for x in litmus.ALL])
    # HIME

    ts_params['HIME']['min_percpu_util'] = 0.8
    ts_params['HIME']['max_percpu_util'] = 0.95

    ts_params['HIME']['min_period'] = 1
    ts_params['HIME']['max_period'] = 100
    ts_params['HIME']['gran_period'] = 1

    ts_params['HIME']['m'] = m = topology.CPUS[host]
    ts_params['HIME']['n_values'] = range(m, 3*m) + range(3*m, 15*m, m) + range(15*m, 20*m + 1, 10)
    ts_params['HIME']['samples'] = 50

    ts_params['HIME']['min_mig_samples'] = int(max(0.5 * ts_params['HIME']['samples'], 1))
    ts_params['HIME']['n_values_with_forced_mig'] = range(m+1, 3*m)

    ts_params['HIME']['max_hyperperiod'] = None # Use None to skip checking. Checks before allocating, so you can use this to exclude task sets that may have a slow allocation. But use a very large number in order not to generate bias.
    ts_params['HIME']['max_percpu_hyperperiod'] = None # Use None to skip checking. Checks only after allocating, so beware of allocation algorithms that use dbf. Depending on the period distribution, they may run for too long.

    ts_params['HIME']['min_slice_size'] = 0.05

    # EDF-WM
    ts_params['EDF-WM'] = ts_params['HIME']

    ts_params['EDF-WM']['max_dbf_time'] = 600000 # Use None for not forcing. 600000 = 10*(time we are going to run the task sets)
    
    return ts_params
