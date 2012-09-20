#ifndef MCS_RW_PROTO_QLOCK
#define MCS_RW_PROTO_QLOCK

#include "mem.h"
#include "atomic.h"
#include "spin.h"

typedef enum {
	NONE   = 0,
	READER = 1,
	WRITER = 2,
} mcs_rw_class_t ;

struct __mcs_rw_state {
	volatile uint16_t blocked; /* volatile needed for spinning in C */
	uint16_t next_cls;
};

typedef union {
	struct __mcs_rw_state state;
	uint32_t raw;
} __mcs_atomic_u;

typedef struct __mcsrwnode
{
	mcs_rw_class_t cls;
	volatile struct __mcsrwnode *next; /* volatile needed for spinning in C */
	__mcs_atomic_u u;
} CACHE_LINE_ALIGNED mcs_rwnode_t;

typedef struct
{
	uint32_t count;
	mcs_rwnode_t*	tail;
	mcs_rwnode_t*   nextw;
} CACHE_LINE_ALIGNED mcs_rwlock_t;

#define DEFINE_MCS_RWLOCK(name) mcs_rwlock_t name = { 0, NULL, NULL }
#define DEFINE_MCS_RWNODE(name) mcs_rwnode_t name

static inline cycles_t mcs_write_lock(mcs_rwlock_t* lock, mcs_rwnode_t *self)
{
	mcs_rwnode_t* prev;

	*self = (mcs_rwnode_t) {.cls = WRITER, .next = NULL,
				.u.state.blocked = 1, .u.state.next_cls = NONE};

	prev = xchgptr(self, (void**)  &lock->tail);
	mb(); /* needed i386 */
	if (!prev) {
		lock->nextw = self;
		mb(); /* Can't have the compiler nor CPU reorder the store of
		       * next before the load of count, otherwise we could
		       * deadlock (as seen on both the Niagara by courtesy of
		       * the GCC optimizer and on Intel Xeon CPUs).
		       */
		if (lock->count == 0 &&	xchgptr(NULL, &lock->nextw) == self)
			self->u.state.blocked = 0;
	} else {
		prev->u.state.next_cls = WRITER;
		mb(); /* needed */
		prev->next = self;
	}

	return spin_while(self->u.state.blocked);
}

static inline void mcs_write_unlock(mcs_rwlock_t* lock, mcs_rwnode_t *self)
{
	if (self->next ||
	    (void*) cmpxchgptr(&lock->tail, self, NULL) != self) {
		while (!self->next)
			cpu_relax();
		mb(); /* probably needed */
		if (self->next->cls == READER)
			xadd32(1, &lock->count);
		self->next->u.state.blocked = 0;
	}
}

static inline cycles_t mcs_read_lock(mcs_rwlock_t* lock, mcs_rwnode_t *self)
{
	mcs_rwnode_t* prev;
	 __mcs_atomic_u old, new;
	 cycles_t spin = 0;

	*self = (mcs_rwnode_t) {.cls = READER, .next = NULL,
				.u.state.blocked = 1, .u.state.next_cls = NONE};

	prev = xchgptr(self, (void**)  &lock->tail);
	if (!prev) {
		xadd32(1, &lock->count);
		self->u.state.blocked = 0;
	} else {
		old.state = (struct __mcs_rw_state) {1, NONE};
		new.state = (struct __mcs_rw_state) {1, READER};
		if (prev->cls == WRITER ||
		    cmpxchg32(&prev->u.raw, old.raw, new.raw) == old.raw) {
			prev->next = self;
			spin = spin_while(self->u.state.blocked);
		} else {
			xadd32(1, &lock->count);
			prev->next = self;
			self->u.state.blocked = 0;
		}
	}
	mb(); /* needed  */
	if (self->u.state.next_cls == READER) {
		while (!self->next)
			cpu_relax();
		xadd32(1, &lock->count);
		self->next->u.state.blocked = 0;
	}
	return spin;
}

static inline void mcs_read_unlock(mcs_rwlock_t* lock, mcs_rwnode_t *self)
{
	mcs_rwnode_t *nextw;

	if (self->next ||
	    ((void*) cmpxchgptr(&lock->tail, self, NULL)) != self) {
		while (!self->next)
			cpu_relax();
		mb(); /* needed */
		if (self->u.state.next_cls == WRITER)
			lock->nextw = (mcs_rwnode_t*) self->next;
	}
	if (!xadd32(-1, &lock->count) &&
	    (nextw = lock->nextw)     &&
	    lock->count == 0          &&
	    ((void*) cmpxchgptr(&lock->nextw, nextw, NULL)) == nextw) {
		nextw->u.state.blocked = 0;
	}
}



#endif
