#define _GNU_SOURCE
#include <event2/event.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <semaphore.h>
#include <time.h>
#define HAVE_STRUCT_TIMESPEC
#include <pthread.h>

#include "utils.h"

#define STR_LEN 128

#define CHECK_RETURN_VAL(ret) \
do { \
    if (ret != 0) { \
        PRINT("return error: %d,%s\n", ret, strerror_r(ret, buf, STR_LEN)); \
    } \
} while (0)

static sem_t sem;
static bool bRun = true;
static pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
static pthread_condattr_t condattr;
static pthread_mutexattr_t lockattr;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static struct timespec ts;
char buf[STR_LEN] = {'\0'};

void thread_work(void *arg)
{
    int i = 0;
    int err = 0;

    PRINT("Thread starts!\n");

    while (1) {
        err = pthread_mutex_lock(&lock);
        if (err) {
            PRINT("mutex lock failed, err(%d)\n", err);
        }
        // err = pthread_cond_wait(&cond, &lock);
        clock_gettime(CLOCK_MONOTONIC, &ts);
        ts.tv_sec += 5;
        err = pthread_cond_timedwait(&cond, &lock, &ts);
        if (err) {
            PRINT("cond wait failed, err(%d)\n", err);
        }

        // clock_gettime(CLOCK_REALTIME, &ts);
        // ts.tv_sec += 2;
        // PRINT("deadlock test, current system time: %ld.%09ld \n", ts.tv_sec, ts.tv_nsec);
        // err = pthread_mutex_timedlock(&lock, &ts);
        // if (err) {
        //     PRINT("mutex lock failed, err(%d,%s)\n", err, strerror_r(err, buf, STR_LEN));
        // }
        PRINT("receive condition signal!! \n");

        sem_wait(&sem);
        if (bRun == false) {
            PRINT("Break the thread loop!\n");
            break;
        }
        PRINT("Receive a work. i(%d), it will take 1 secs to finish...\n", i++);
        err = pthread_mutex_unlock(&lock);
        if (err) {
            PRINT("mutex lock failed, err(%d)\n", err);
        }
        sleep(1);
    }

    PRINT("Thread exits!\n");
    pthread_exit(NULL);
}

void event_cb(evutil_socket_t socket, short what, void *arg)
{
    int ret = 0;
    int *pipe_fd = (int *)arg;
    char buf[16] = {[0 ... 15] = '\0'};
    PRINT("event callback! arg(%p) what(0x%X) arg: %p\n", arg, what, arg);
    PRINT("receive an event: fd = r:%d w:%d \n", pipe_fd[0], pipe_fd[1]);

    // PRINT("close write fd: %d\n", pipe_fd[1]);
    // if ((ret = close(pipe_fd[1])) < 0)
    //     PRINT("close write fd: %d failed, ret = %d\n", pipe_fd[1], ret);

    PRINT("read from fd: %d\n", pipe_fd[0]);
    if (ret = read(pipe_fd[0], buf, 1) != 1) {
        PRINT("read failed, ret = %d\n", ret);
        return;
    }
    PRINT("buf: '%s' \n", buf);
}

void *event_thread_work(void *arg)
{
    int ret = 0;
    int *pipe_fd = (int *)arg;
    struct event_base *base = event_base_new();
    struct event *ev = NULL;
    struct timeval tv = {.tv_sec = 10};
    PRINT("base = %p\n", base);

    PRINT("new an event: fd = r:%d w:%d \n", pipe_fd[0], pipe_fd[1]);
    ev = event_new(base, pipe_fd[0], EV_PERSIST | EV_READ, event_cb, pipe_fd);
    ret = event_add(ev, &tv);
    CHECK_RETURN_VAL(ret);
    if (base) {
        ret = event_base_loop(base, EVLOOP_NO_EXIT_ON_EMPTY);
        PRINT("base loop exit: %d\n", ret);
        CHECK_RETURN_VAL(ret);
    }
    return NULL;
}

int main(int argc, char *argv[])
{
    int ret;
    pthread_t t;
    int pipe_fd[2] = {-1, -1};
    char c = 'a';

    ret = pipe(pipe_fd);
    if (ret < 0)
        PRINT("pipe creation failed: %d\n", ret);

    PRINT("Create an event thread \n");
    ret = pthread_create(&t, NULL, (void *)event_thread_work, pipe_fd);

    while (1) {
        int a;
        PRINT("Enter 1 to send a work, or 0 to exit the program: \n");
        scanf("%d", &a);
        if (a == 1) {
            // PRINT("close read fd: %d \n", pipe_fd[0]);
            // if ((ret = close(pipe_fd[0])) < 0)
            //     PRINT("close read fd: %d failed, ret = %d\n", pipe_fd[0], ret);
            PRINT("write fd(%d) a character \n", pipe_fd[1]);
            if ((ret = write(pipe_fd[1], (void *)&c, sizeof(char))) != sizeof(char)) {
                PRINT("write error, ret = %d\n", ret);
            }
            c++;
        } else if (a == 0) {
            PRINT("exit the program \n");
            break;
        }
    }
#if 0
    pthread_mutexattr_init(&lockattr);
    pthread_mutex_init(&lock, &lockattr);

    pthread_condattr_init(&condattr);
    pthread_condattr_setclock(&condattr, CLOCK_MONOTONIC);
    pthread_cond_init(&cond, &condattr);
    PRINT("Create a thread \n");
    ret = pthread_create(&t, NULL, (void *)thread_work, NULL);
    PRINT("Ret(%d) of the thread creation\n", ret);

    while (1) {
        int a;
        PRINT("Enter 1 to send a work, or 0 to exit the program: \n");
        scanf("%d", &a);
        if (a == 1) {
            ret = pthread_cond_signal(&cond);
            if (ret) {
                PRINT("condition signal failed, err(%d)\n", ret);
            }
            sem_post(&sem);
        } else if (a == 0) {
            ret = pthread_mutex_lock(&lock);
            if (ret) {
                PRINT("mutex lock failed, err(%d)\n", ret);
            }
            PRINT("Exit the program. \n");
            ret = pthread_cond_signal(&cond);
            if (ret) {
                PRINT("condition signal failed, err(%d)\n", ret);
            }
            bRun = false;
            ret = pthread_mutex_unlock(&lock);
            if (ret) {
                PRINT("mutex lock failed, err(%d)\n", ret);
            }
            sem_post(&sem);
            // pthread_cancel(t); this is not recommended.
            break;
        } else {
            PRINT("Unknown command. a: %d\n", a);
        }
    }

    pthread_join(t, NULL);
#endif

    return 0;
}
