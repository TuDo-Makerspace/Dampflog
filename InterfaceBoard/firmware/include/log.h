#ifndef _LOG_H_INCLUDED
#define _LOG_H_INCLUDED

#include <stdio.h>

#define LOG(...)                                             \
	printf("%s:%d, %s: ", __FILE__, __LINE__, __func__); \
	printf(__VA_ARGS__);                                 \
	printf("\n");

#ifdef DEBUG
#define LOG_DEBUG(...) LOG(__VA_ARGS__)
#else
#define LOG_DEBUG(...)
#endif

#endif // _LOG_H_INCLUDED