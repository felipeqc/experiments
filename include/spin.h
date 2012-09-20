#ifndef _SPIN_H
#define _SPIN_H

#include "litmus.h"

#define spin_while(cond)      \
	({					\
		cycles_t __start, __stop;		\
		__start = get_cycles();			\
		while ((cond))				\
			cpu_relax();			\
		__stop = get_cycles();			\
		__stop -= __start;			\
		__stop;					\
	})

#endif
