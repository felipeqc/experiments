#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>
#include <sys/sysinfo.h>

#include "litmus.h"

#include "busywork.h"

void jump(void)
{
	int cpu;

	cpu = rand() % get_nprocs();

	be_migrate_to(cpu);
}


void measure(int wss, double target)
{
	double start, stop, error, delta;

	start = cputime();

	do_busywork(wss, target / 1000);

	stop =  cputime();

	delta = (stop - start) * 1000000;

	error = (delta - target) / target;

	printf("%4dKB %5.2fus => error: %7.4fus (%3.0f%%)\n", wss, target, delta - target, error * 100);
}

void test_wss(int wss)
{
	double target = 10.0;
	int loops;

	for (target = 5; target <= 1000; target += 5)
		for (loops = 0; loops < 10; loops++)
		{
			jump();
			measure(wss, target);
		}
}

int main(int argc, char** argv)
{

	srand((int) time(NULL) + (int) getpid());

	test_wss(1);

	test_wss(4);

	test_wss(64);

	return 0;
}
