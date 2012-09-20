#include "litmus.h"

#define INT_KB (1024/sizeof(int))

/* access wss on the stack */
int dirty_kb(int kb)
{
	volatile int one_kb[INT_KB];
	int sum = 0, other = 0;
	int i;

	for (i = 0; i < INT_KB; i++) {
		/* read garbage */
		sum += one_kb[i];
		/* write */
		one_kb[i] = sum;
	}
	kb--;
	if (kb) {
		other = dirty_kb(kb);
	}

	/* prevent tail recursion */
	for (i = 0; i < INT_KB; i++) {
		sum += one_kb[i];
		one_kb[i] = sum % (other ? other : 10);
	}

	return sum;
}


int do_busywork(int wss, double budget)
{
	double last_loop = 0;
	double loop_start;
	int tmp = 0;

	double start = cputime();
	double now = cputime();

	while (now + last_loop < start + (budget / 1000)) {
		loop_start = now;
		tmp += dirty_kb(wss);
		now = cputime();
		last_loop = now - loop_start;
	}

	return tmp;
}
