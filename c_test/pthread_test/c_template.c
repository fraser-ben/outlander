#define _GNU_SOURCE
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <semaphore.h>
#include <time.h>
#define HAVE_STRUCT_TIMESPEC
#include <pthread.h>

static sem_t sem;
static bool bRun = true;
static pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static struct timespec ts;
char buf[128] = {'\0'};

void thread_work(void *arg)
{
    int i = 0;
    int err = 0;

    printf("Thread starts!\n");

    while (1) {
        err = pthread_mutex_lock(&lock);
        if (err) {
            printf("mutex lock failed, err(%d)\n", err);
        }
        err = pthread_cond_wait(&cond, &lock);
        if (err) {
            printf("cond wait failed, err(%d)\n", err);
        }

        clock_gettime(CLOCK_MONOTONIC, &ts);

        printf("deadlock test, current system time: %ld.%09ld \n", ts.tv_sec, ts.tv_nsec);
        ts.tv_sec += 5;
        // err = pthread_mutex_timedlock(&lock, &ts);
        err = pthread_mutex_lock(&lock);
        if (err) {
            printf("mutex lock failed, err(%d,%s)\n", err, strerror_r(err, buf, 128));
        }
        printf("receive condition signal!! \n");

        sem_wait(&sem);
        if (bRun == false) {
            printf("Break the thread loop!\n");
            break;
        }
        printf("Receive a work. i(%d), it will take 1 secs to finish...\n", i++);
        err = pthread_mutex_unlock(&lock);
        if (err) {
            printf("mutex lock failed, err(%d)\n", err);
        }
        sleep(1);
    }

    printf("Thread exits!\n");
    pthread_exit(NULL);
}

int main(int argc, char *argv[])
{
    int ret;
    pthread_t t;

    printf("Create a thread \n");
    ret = pthread_create(&t, NULL, (void *)thread_work, NULL);
    printf("Ret(%d) of the thread creation\n", ret);

    while (1) {
        int a;
        printf("Enter 1 to send a work, or 0 to exit the program: \n");
        scanf("%d", &a);
        if (a == 1) {
            ret = pthread_cond_signal(&cond);
            if (ret) {
                printf("condition signal failed, err(%d)\n", ret);
            }
            sem_post(&sem);
        } else if (a == 0) {
            ret = pthread_mutex_lock(&lock);
            if (ret) {
                printf("mutex lock failed, err(%d)\n", ret);
            }
            printf("Exit the program. \n");
            ret = pthread_cond_signal(&cond);
            if (ret) {
                printf("condition signal failed, err(%d)\n", ret);
            }
            bRun = false;
            ret = pthread_mutex_unlock(&lock);
            if (ret) {
                printf("mutex lock failed, err(%d)\n", ret);
            }
            sem_post(&sem);
            // pthread_cancel(t); this is not recommended.
            break;
        } else {
            printf("Unknown command. a: %d\n", a);
        }
    }

    pthread_join(t, NULL);

    return 0;
}
