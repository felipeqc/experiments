#ifndef PF_Q_PROTO_H
#define PF_Q_PROTO_H

#include "mem.h"
#include "atomic.h"
#include "spin.h"

typedef struct __pfqnode
{
	volatile struct __pfqnode *next; /* volatile needed for spinning in C */
	volatile uint32_t blocked;
} CACHE_LINE_ALIGNED pfq_rwnode_t;

typedef struct {
	volatile uint32_t rin, rout, last;
	pfq_rwnode_t *rtail[2];
	pfq_rwnode_t *wtail, *whead;
} CACHE_LINE_ALIGNED pfq_rwlock_t;

#define DEFINE_PFQ_RWLOCK(x) pfq_rwlock_t x =	\
	{ 0, 0, 0, {NULL, NULL}, NULL, WAIT }

#define DEFINE_PFQ_RWNODE(x) pfq_rwnode_t x

#define RINC 0x100
#define PHID 0x1
#define PRES 0x2
#define WMSK 0x3
#define WAIT ((pfq_rwnode_t*) 0xbad)

static inline cycles_t pfq_write_lock(pfq_rwlock_t *lock, pfq_rwnode_t *self)
{
	uint32_t ticket, exit;
	pfq_rwnode_t *prev;
	cycles_t spin = 0;

	self->next = NULL;
	self->blocked = 1;
	mb();
	/* writer mutex */
	prev = xchgptr(self, (void**) &lock->wtail);
	if (prev) {
		prev->next = self;
		spin = spin_while(self->blocked);
	}
	mb();
	/* at  head of writer queue */
	self->blocked = 1;
	lock->whead   = self;
	lock->rtail[lock->rin & PHID] = WAIT;
	mb();
	ticket     = xadd32(PRES, &lock->rin) & ~WMSK;
	lock->last = ticket;
	mb();
	exit = (xadd32(PRES, &lock->rout) & ~WMSK);
	if (exit != ticket)
		/* wait for readers to drain */
		spin += spin_while(self->blocked);
	lock->whead = WAIT;
	return spin;
}

static inline void pfq_write_unlock(pfq_rwlock_t *lock, pfq_rwnode_t *self)
{
	uint32_t phase;
	pfq_rwnode_t *prev;

	mb();
	phase = lock->rin & PHID;
	*lsb32((uint32_t*) &lock->rout) = 0;
	*lsb32((uint32_t*) &lock->rin)  = (phase + 1) & PHID;
	mb();
	prev =  xchgptr(NULL, (void**) &lock->rtail[phase]);
	if (prev != WAIT)
		prev->blocked = 0;
	if (self->next ||
	    (void*) cmpxchgptr(&lock->wtail, self, NULL) != self)
		while (!self->next)
			cpu_relax();
	mb();
	if (self->next)
		self->next->blocked = 0;
}

static inline cycles_t  pfq_read_lock(pfq_rwlock_t *lock, pfq_rwnode_t *self)
{
	uint32_t ticket;
	pfq_rwnode_t *prev;
	cycles_t spin = 0;

	ticket = xadd32(RINC, &lock->rin);
	if (ticket & PRES) {
		self->blocked = 1;
		mb();
		prev =  xchgptr(self, (void**) &lock->rtail[ticket & PHID]);
		if (prev != NULL) {
			spin = spin_while(self->blocked);
			if (prev != WAIT)
				prev->blocked = 0;
		} else {
			/* already unlocked */
			prev = xchgptr(NULL, (void**) &lock->rtail[ticket & PHID]);
			prev->blocked = 0;
			/* await that next--if next!=NULL--unblocks self, thereby
			 * avoiding that next references a stale pointer
			 */
			while (self->blocked)
				cpu_relax();
		}
	}
	mb();
	return spin;
}

static inline void pfq_read_unlock(pfq_rwlock_t *lock, pfq_rwnode_t *self)
{
	uint32_t ticket;

	mb();

	ticket = xadd32(RINC, &lock->rout);
	if ((ticket & PRES) && (ticket & ~WMSK) == lock->last) {
		mb();
		lock->whead->blocked = 0;
	}
}

#endif
