from subprocess import Popen

def chomp(val):
    if val and val[-1] == '\n':
        return val[:-1]
    else:
        return val

def echo(value, fname):
    with open(fname, 'w') as f:
        f.write(str(value))

def cat(fname):
    with open(fname, 'r') as f:
        val = "\n".join(f.readlines())
    return chomp(val)

def echo_and_test(value, fname):
    echo(value, fname)
    res = cat(fname)
    if res != chomp(value):
        raise IOError("echo not successful ('%s' -> '%s' resulted in '%s')"
                      % (value, fname, res))

def spawn(cmd, args, path=None, stdout=None):
    if path:
        cmd = "%s/%s" % (path, cmd)
        shell = False
    else:
        shell = True

    args = [cmd] + [str(x) for x in args]
    if shell:
        args = " ".join(args)

    try:
        if stdout:
            with open(stdout, 'w') as f:
                proc = Popen(args, shell=shell, stdout=f)
        else:
            proc = Popen(args, shell=shell)
        return proc
    except OSError as (msg):
        raise OSError("Could not spawn '%s': %s" % (cmd, msg))
