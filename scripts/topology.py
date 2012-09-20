import litmus

LUDWIG = {
# Socket0  Socket1  Socket2  Socket3
# ------   -------  -------  -------
# | 0, 4|  | 1, 5|  | 2, 6|  | 3, 7|
# | 8,12|  | 9,13|  |10,14|  |11,15|
# |16,20|  |17,21|  |18,22|  |19,23|
# -------  -------  -------  -------
    'L2' : [(0, 4), ( 8, 12), (16, 20),
            (1, 5), ( 9, 13), (17, 21),
            (2, 6), (10, 14), (18, 22),
            (3, 7), (11, 15), (19, 23)],

    'L3' : [(0, 4,  8, 12, 16, 20),
            (1, 5,  9, 13, 17, 21),
            (2, 6, 10, 14, 18, 22),
            (3, 7, 11, 15, 19, 23)],
}


HOSTS = {
    'ludwig' : LUDWIG
}

CPUS = {
    'ludwig'     : 24,
    'kvm'        :  4,
    'district10' :  4,
    'felipe'     :  4,
}


non_clustered = set([s for s in litmus.ALL
                     if not s in litmus.CLUSTERED])

SCHEDULERS = {
    'ludwig'     : litmus.ALL,
    'kvm'        : non_clustered,
    'district10' : non_clustered,
    'felipe'     : litmus.SEMIPARTITIONED,
}
