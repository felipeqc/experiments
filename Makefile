# ##############################################################################
# User variables

# user variables can be specified in the environment or in a .config file
-include .config

# Where is the LITMUS^RT userspace library source tree?
LIBLITMUS ?= ../litmus/litmus-semi/liblitmus

# Where are the ft_tools installed?
FT_TOOLS ?= ../litmus/litmus-semi/ft_tools

# Where is Linux kernel?
LITMUS_KERNEL ?= ../litmus/litmus-semi/litmus2010

ARCH ?= x86_64

# Include default configuration from liblitmus
# Liblitmus must have been built before ft_tools can be built.
#include ${LIBLITMUS}/inc/config.makefile

# ##############################################################################
# Internal configuration.

# compiler flags
flags-debug    = -Wall -Werror -g -Wdeclaration-after-statement
flags-api      = -D_XOPEN_SOURCE=600 -D_GNU_SOURCE

# architecture-specific flags
flags-i386     = -m32
flags-x86_64   = -m64
flags-sparc64  = -mcpu=v9 -m64
# default: none

# name of the directory that has the arch headers in the Linux source
include-i386     = x86
include-x86_64   = x86
include-sparc64  = sparc
# default: the arch name
include-${ARCH} ?= ${ARCH}

# name of the file(s) that holds the actual system call numbers
unistd-i386      = unistd.h unistd_32.h
unistd-x86_64    = unistd.h unistd_64.h
# default: unistd.h
unistd-${ARCH}  ?= unistd.h

# by default we use the local version
LIBLITMUS ?= .

# where to find header files
headers = -I${LIBLITMUS}/include -I${LITMUS_KERNEL}/include -I${LITMUS_KERNEL}/arch/${include-${ARCH}}/include

# combine options
CPPFLAGS = ${flags-api} ${flags-${ARCH}} -DARCH=${ARCH} ${headers}
CFLAGS   = ${flags-debug}
LDFLAGS  = ${flags-${ARCH}}

# how to link against liblitmus
liblitmus-flags = -L${LIBLITMUS} -llitmus

# Force gcc instead of cc, but let the user specify a more specific version if
# desired.
ifeq (${CC},cc)
CC = gcc
endif

# incorporate cross-compiler (if any)
CC  := ${CROSS_COMPILE}${CC}
LD  := ${CROSS_COMPILE}${LD}
AR  := ${CROSS_COMPILE}${AR}

# all sources
vpath %.c src/

# local include files
CPPFLAGS += -Iinclude/ -I${FT_TOOLS}/include

# need RT clocks
LDLIBS += -lrt

# ##############################################################################
# Targets

#all = lockstress compute-task background-task busy-bench spinlock-task
all = compute-task-edfwm compute-task-hime alloc-hime alloc-wm background-task

.PHONY: all clean
all: ${all}
clean:
	rm -f ${all} *.o *.d
	find . -iname '*.pyc' -exec rm '{}' ';'

obj-compute-task-edfwm = compute-task-edfwm.o busywork.o ${LIBLITMUS}/bin/common.o ${LIBLITMUS}/src/litmus.o ${LIBLITMUS}/src/kernel_iface.o ${LIBLITMUS}/src/syscalls.o ${LIBLITMUS}/src/clocks.o ${LIBLITMUS}/src/task.o
compute-task-edfwm: ${obj-compute-task-edfwm}

obj-compute-task-hime = compute-task-hime.o busywork.o ${LIBLITMUS}/bin/common.o ${LIBLITMUS}/src/litmus.o ${LIBLITMUS}/src/kernel_iface.o ${LIBLITMUS}/src/syscalls.o ${LIBLITMUS}/src/clocks.o ${LIBLITMUS}/src/task.o
compute-task-hime: ${obj-compute-task-hime}

alloc-hime: allocation/hime.c
	gcc allocation/hime.c -o allocation/hime -lm -O3

alloc-wm: allocation/edfwm.c
	gcc  allocation/common.c allocation/edfwm_util.c allocation/edfwm.c -o allocation/edfwm -lm -O3

#obj-lockstress = lockstress.o busywork.o
#lockstress: ${obj-lockstress}

#obj-spinlock-task = spinlock-task.o busywork.o
#spinlock-task: ${obj-spinlock-task}

#obj-compute-task = compute-task.o busywork.o
#compute-task: ${obj-compute-task}

obj-background-task = background-task.o ${LIBLITMUS}/bin/common.o ${LIBLITMUS}/src/litmus.o ${LIBLITMUS}/src/kernel_iface.o ${LIBLITMUS}/src/syscalls.o ${LIBLITMUS}/src/clocks.o ${LIBLITMUS}/src/task.o
background-task: ${obj-background-task}

#obj-busy-bench = busy-bench.o busywork.o
#busy-bench: ${obj-busy-bench}

# dependency discovery
include ${LIBLITMUS}/inc/depend.makefile
