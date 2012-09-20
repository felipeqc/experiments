from proc   import spawn
from litmus import FT_TOOLS

DEVICE = '/dev/litmus/ft_trace0'

SCHED_EVENTS = [
    'SCHED_END',
    'SCHED_START',
    'SCHED2_END',
    'SCHED2_START',
    'TICK_END',
    'TICK_START',
    'PULL_TIMER_END',
    'PULL_TIMER_START',
    'RELEASE_END',
    'RELEASE_START',
    'CXS_END',
    'CXS_START',
    'SEND_RESCHED_END',
    'SEND_RESCHED_START',
    'RELEASE_LATENCY'
    ]

LOCK_EVENTS = [
    'SYSCALL_IN_END',
    'SYSCALL_IN_START',
    'SYSCALL_OUT_END',
    'SYSCALL_OUT_START',
    'LOCK_END',
    'LOCK_RESUME',
    'LOCK_SUSPEND',
    'LOCK_START',
    'UNLOCK_END',
    'UNLOCK_START'
    ]

ALL_EVENTS = SCHED_EVENTS + LOCK_EVENTS

def ftcat(saveas, device=None, events=ALL_EVENTS):
    if device is None:
        device = DEVICE
    return spawn('ftcat', [device] + events,
                 stdout=saveas,
                 path=FT_TOOLS)
