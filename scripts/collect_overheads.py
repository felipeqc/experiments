import sys
from os import path
from datetime import datetime

from trace import *

host = 'felipe'

def main():
    taskset_dir = path.join(EXPERIMENTS_DIR, 'tasksets', host)
    for taskset_file in listdir(taskset_dir):
        if taskset_file.lower().endswith('.ats'):
            try:
                experiment(path.join(taskset_dir, taskset_file))
            except (OSError, IOError) as msg:
                print 'Failed: %s\n%s' % (taskset_file, msg)
            except KeyboardInterrupt:
                print 'Aborted.'
                return

if __name__ == '__main__':
    main()

