#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <stdint.h>

static FILE *results = NULL;

static int BUF_SZ = 1024; /* stack-based buffer for messages */

/* deprecated for external use */
int th_check(int check, const char *message, ...) {
  int szr;
  char buffer[BUF_SZ];
  va_list argp;

  va_start(argp, message);
  szr = vsnprintf(buffer, BUF_SZ, message, argp);
  va_end(argp);

  if(szr >= BUF_SZ) {
	fprintf(stderr, "ERROR: Ran out of buffer space in th_check (needed: %d)\n", szr);
    exit(1);
  }

  fprintf(stderr, "%s: %s\n", check ? "PASS" : "FAIL", buffer);
  if(results) {
	fprintf(results, "%s: %s\n", check ? "PASS" : "FAIL", buffer);
	fflush(results);
  }
  return check;
}

/* use to prepare a message for passing to the th_check_* functions,
   especially if you have custom data to incorporate into the message 

   th_msg(buf, bufsz, "iteration %d: pointer %%p should be same as %%p", i)
*/
const char *th_msg(char *buf, int bufsz, const char *message, ...) {
  int szr;
  va_list argp;

  va_start(argp, message);
  szr = vsnprintf(buf, bufsz, message, argp);
  va_end(argp);

  if(szr >= bufsz) {
	fprintf(stderr, "ERROR:th_msg: Ran out of buffer space (needed: %d)\n", szr);
    exit(1);
  }

  return buf;
}

#define th_gen_message(buffer, ...)				\
  { \
  int szr; \
  \
  szr = snprintf((buffer), BUF_SZ, message, __VA_ARGS__);	\
  if(szr >= BUF_SZ) { \
	fprintf(stderr, "ERROR:%s:%d:Ran out of buffer space (needed: %d)\n", __FILE__, __LINE__, szr); \
    exit(1); \
  } \
  }

/* TODO: use the _Generic mechanism */
int th_check_eq_ptr(void *a, void *b, const char *message) {
  char buffer[BUF_SZ];

  th_gen_message(buffer, a, b);
  return th_check(a == b, buffer);
}

int th_check_not_eq_ptr(void *a, void *b, const char *message) {
  char buffer[BUF_SZ];
  th_gen_message(buffer, a, b);
  return th_check(a != b, buffer);
}

int th_check_not_null(void *a, const char *message) {
  char buffer[BUF_SZ];
  th_gen_message(buffer, a);

  return th_check(a != NULL, buffer);
}


int th_check_eq_uint32(uint32_t a,  uint32_t b, const char *message) {
  char buffer[BUF_SZ];

  th_gen_message(buffer, a, b);
  return th_check(a == b, buffer);
}

int th_check_not_eq_uint32(uint32_t a, uint32_t b, const char *message) {
  char buffer[BUF_SZ];
  th_gen_message(buffer, a, b);
  return th_check(a != b, buffer);
}


int th_check_eq_int32(int32_t a,  int32_t b, const char *message) {
  char buffer[BUF_SZ];

  th_gen_message(buffer, a, b);
  return th_check(a == b, buffer);
}

int th_check_not_eq_int32(int32_t a, int32_t b, const char *message) {
  char buffer[BUF_SZ];
  th_gen_message(buffer, a, b);
  return th_check(a != b, buffer);
}

int th_set_results_file(const char *results_file) {
  if(results_file) {
	results = fopen(results_file, "w");
	if(!results) {
	  fprintf(stderr, "ERROR: unable to open results file '%s' for writing\n", results_file);
	  return 0;
	}
  }

  return 1;
}

__attribute__((constructor)) void write_results_to_file() {
  char *results_file;

  results_file = getenv("TH_RESULTS_FILE");
  if(results_file) {
	th_set_results_file(results_file);
  }
}
