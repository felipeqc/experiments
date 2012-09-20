#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <unistd.h>

#include "litmus.h"

#define WSS 12288 /* 12 Mb */

#define NUM_VARS WSS * 1024 / sizeof(long)

long data[NUM_VARS];

int main(int argc, char** argv)
{
	int i;
	long sum;
	FILE* sink;

	if (argc != 2 ||
	    (atoi(argv[1]) == 0 && strcmp(argv[1], "0")) ||
	    be_migrate_to(atoi(argv[1]))) {
		fprintf(stderr, "Usage: %s CPU-ID\n", argv[0]);
		exit(1);
	}

	srand(time(NULL) + getpid());

	sink = fopen("/dev/null", "r");

	while (1) {
		for (i = 0; i < NUM_VARS; i++)
			data[i] = rand();
		sum = 0;
		for (i = 0; i < NUM_VARS; i++)
			sum += (i % 2 ? 1 : -1) * data[i];
		for (i = NUM_VARS - 1; i >= 0; i--)
			sum += (i % 2 ? -1 : 1) * 100  /  (data[i] ? data[i] : 1);
		fprintf(sink, "sum: %ld\n", sum);
	}
}
