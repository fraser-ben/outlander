#ifndef _UTILS_H_
#define _UTILS_H_
#include <unistd.h>
#include <sys/types.h>
#include <math.h>
#include <sys/time.h>
#include <syscall.h>
#include <time.h>

#define STRING_TIME_BUFFER_LEN 64

static char string_buffer[STRING_TIME_BUFFER_LEN] = {'\0'};

#define GET_STR_TIME() \
({ \
    char tmp[STRING_TIME_BUFFER_LEN] = {'\0'}; \
    struct timeval tv; \
    struct tm *tm_info; \
    gettimeofday(&tv, NULL); \
    tm_info = localtime(&tv.tv_sec); \
    strftime(tmp, STRING_TIME_BUFFER_LEN, "%Y-%m-%d %H:%M:%S.%%u", tm_info); \
    snprintf(string_buffer, STRING_TIME_BUFFER_LEN, tmp, tv.tv_usec); \
    string_buffer; \
})

#define PRINT(fmt, args...) \
    do { \
        printf("%s  %-d  %-d [%s][%d]" fmt, GET_STR_TIME(), getpid(), gettid(), __FUNCTION__, __LINE__, ##args); \
    } while (0)

#endif