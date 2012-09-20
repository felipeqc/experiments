#ifndef __MCS_Q_LOCK_H__
#define __MCS_Q_LOCK_H__

#include "mem.h"
#include "atomic.h"
#include "spin.h"

typedef struct __mcspnode
{
	volatile int	            blocked;
	volatile struct __mcspnode* next;
} CACHE_LINE_ALIGNED mcs_node_t;

typedef struct
{
	volatile mcs_node_t*	tail;
} CACHE_LINE_ALIGNED  mcs_lock_t;

#define DEFINE_MCSPLOCK(name) mcs_lock_t name = { NULL }
#define DEFINE_MCSPNODE(name) mcs_node_t name


static inline cycles_t mcs_lock(mcs_lock_t* lock, mcs_node_t *self)
{
	mcs_node_t* prev;

	self->next     = NULL;

	do {
		prev = (mcs_node_t*) lock->tail;
	} while ((mcs_node_t*) cmpxchgptr(&lock->tail, prev, self)
		 != prev);

	if (prev) {
		self->blocked = 1;
		prev->next    = self;
		return spin_while(self->blocked);
	} else
		return 0;
}

static inline void mcs_unlock(mcs_lock_t* lock, mcs_node_t *self)
{
	if (!self->next && ((mcs_node_t*)
			    cmpxchgptr(&lock->tail, self, 0)) != self)
		while (!self->next)
			cpu_relax();
	if (self->next)
		self->next->blocked = 0;
}


#endif

