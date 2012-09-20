#ifndef I386_MEM_H
#define I386_MEM_H

/* ludwig */
#define CACHE_LINE_SIZE 64
#define CACHE_LINE_ALIGNED  __attribute__ ((aligned(CACHE_LINE_SIZE)))

static inline void mb(void)
{
	__asm__ __volatile__("mfence" : : : "memory");
}

static inline void cpu_relax(void)
{
	__asm__ __volatile__("pause");
	mb();
}


#define lsb32(word) ((uint8_t*) word)


#endif
