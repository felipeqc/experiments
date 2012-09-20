#include <stdio.h>
#include <stdlib.h>

#include <fcntl.h>
#include <unistd.h>

#include "litmus.h"

#include "busywork.h"

#define usage(fmt, args...) do { fprintf(stderr, "Error: " fmt "\n", ## args); _usage(1); }  while (0)

double loop_time = 0;
unsigned int num_loops = 0;
unsigned int num_jobs  = 0;

static int compute_job(int wss, double budget)
{
	double last_loop = 0, loop_start;
	int tmp = 0;

	double start = cputime();
	double now = cputime();

	while (now + last_loop < start + (budget / 1000)) {
		loop_start = now;
		tmp += dirty_kb(wss);
		now = cputime();
		last_loop = now - loop_start;
		/* stats */
		loop_time += last_loop;
		num_loops++;
	}

	num_jobs++;
	return tmp;
}

void _usage(int ret)
{
	fprintf(stderr,
		"\nUsage: compute-task [OPTIONS]\n"
		"\nOptions:\n"
  		"   -p PARTITION (0..m-1)\n"
		"   -E EXEC-BUDGET (ms)\n"
		"   -P PERIOD (ms)\n"
		"   -Q PRIORITY (1..%u)\n"
		"   -T TIMEOUT (sec)\n"
		"   -W WORKING-SET-SIZE (kB)\n"
		"   -v  -- verbose\n"
		"   -w  -- wait for task system release\n",
		0); /*LITMUS_MAX_PRIORITY);*/
	exit(ret);
}


#define OPTSTR "p:P:E:Q:T:W:wv"

int main(int argc, char** argv)
{
	int opt;
	int err = 0;
	double start;

	int budget  =  25; /* ms */
	int period  = 100; /* ms */
	unsigned int priority = 0;
	int timeout = 10;  /* s */
	int wss     = 64;  /* kb */
	int cpu     = 0;
	int migrate = 0;
	int wait    = 0;
	int verbose = 0;

	while ((opt = getopt(argc, argv, OPTSTR)) != -1) {
		switch (opt) {
		case 'w':
			wait = 1;
			break;
		case 'p':
			cpu = atoi(optarg);
			migrate = 1;
			break;

		case 'E':
		        budget = atoi(optarg);
			break;

		case 'P':
		        period = atoi(optarg);
			break;

		case 'Q':
			priority = atoi(optarg);
			if (priority == 0 || priority > LITMUS_MAX_PRIORITY)
				usage("Invalid priority (%s).", optarg);
			break;

		case 'T':
		        timeout = atoi(optarg);
			if (timeout < 0)
				usage("invalid timeout value (%s)", optarg);
			break;
		case 'W':
		        wss = atoi(optarg);
			if (wss <= 0)
				usage("invalid working set size (%s)", optarg);
			break;
		case 'v':
			verbose = 1;
			break;

		case ':':
			usage("Argument missing.");
			break;
		case '?':
		default:
			usage("Bad argument.");
			break;
		}
	}


	if (budget <= 0 || period < budget)
		usage("invalid task parameters (%d, %d)", budget, period);

	init_litmus();

	err = sporadic_task(budget, period, 0, cpu, priority,
			    RT_CLASS_HARD, NO_ENFORCEMENT, migrate);
	if (err != 0) {
		fprintf(stderr, "Could not set task parameters (%m).\n");
		exit(2);
	}

	err = task_mode(LITMUS_RT_TASK);
	if (err != 0) {
		fprintf(stderr, "could not become RT task (%m)\n");
		exit(5);
	}

	if (wait) {
		err = wait_for_ts_release();
		if (err != 0) {
			fprintf(stderr, "Could not wait for TS release (%m)\n.");
			exit(5);
		}
	}

	start = wctime();
	while (timeout == 0 || wctime() < start + timeout) {
		compute_job(wss, budget * 0.9);
		sleep_next_period();
	}

	task_mode(BACKGROUND_TASK);

	if (verbose)
		printf("%s/%d: jobs=%u loops=%u total=%.2fsec per-job=%.2fms per-loop=%.2fms\n",
		       argv[0], getpid(), num_jobs, num_loops, loop_time,
		       (loop_time / num_jobs) * 1000,
		       (loop_time / num_loops) * 1000);

	return 0;
}
