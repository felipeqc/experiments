#ifndef SYNC_ATOMIC_H
#define SYNC_ATOMIC_H

#define cmpxchg32(m, old, new) __sync_val_compare_and_swap(m, old, new)
#define cmpxchg64(m, old, new) __sync_val_compare_and_swap(m, old, new)
#define cmpxchgptr(m, old, new) __sync_val_compare_and_swap(m, old, new)
#define cmpxchg(m, old, new) __sync_val_compare_and_swap(m, old, new)
#define xchgptr(new, mem) __sync_lock_test_and_set(mem, new)

#define xadd32(i, mem) __sync_add_and_fetch(mem, i)


typedef struct { volatile int counter; } atomic_t;

#define ATOMIC_INIT(i)	{ (i) }

/**
 * atomic_read - read atomic variable
 * @v: pointer of type atomic_t
 *
 * Atomically reads the value of @v.
 */
#define atomic_read(v)		((v)->counter)

/**
 * atomic_set - set atomic variable
 * @v: pointer of type atomic_t
 * @i: required value
 *
 * Atomically sets the value of @v to @i.
 */
#define atomic_set(v,i)		(((v)->counter) = (i))

/**
 * atomic_add_return - add and return
 * @v: pointer of type atomic_t
 * @i: integer value to add
 *
 * Atomically adds @i to @v and returns @i + @v
 */
static __inline__ int atomic_add_return(int i, atomic_t *v)
{
	return (int) xadd32((uint32_t) i, (uint32_t*)&v->counter);
}

static __inline__ int atomic_add_return_old(int i, atomic_t *v)
{
	return atomic_add_return(i, v) - i;
}


static __inline__ void atomic_add(int i, atomic_t *v)
{
	atomic_add_return(i, v);
}

#define atomic_inc_return(v)  (atomic_add_return(1,v))
#define atomic_inc(v) (atomic_add(1, v))

#endif
