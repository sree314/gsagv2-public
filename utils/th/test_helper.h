#pragma once
#include <stdint.h>

int th_check(int check, const char *message, ...);

int th_check_eq_ptr(void *a, void *b, const char *message);
int th_check_not_eq_ptr(void *a, void *b, const char *message);
int th_check_not_null(void *a, const char *message);

int th_check_eq_uint32(uint32_t a,  uint32_t b, const char *message);
int th_check_not_eq_uint32(uint32_t a, uint32_t b, const char *message);

int th_check_eq_int32(int32_t a,  int32_t b, const char *message);
int th_check_not_eq_int32(int32_t a, int32_t b, const char *message);

#define th_check_eq(x, y) _Generic((x),			\
								   uint32_t: th_check_eq_uint32,	\
								   int32_t: th_check_eq_int32,		\
								   void *: th_check_eq_ptr			\
								   )(x, y)

#define th_check_not_eq(x, y) _Generic((x),								\
									   uint32_t: th_check_not_eq_uint32, \
									   int32_t: th_check_not_eq_int32,	\
									   void *: th_check_not_eq_ptr		\
									   )(x, y)
