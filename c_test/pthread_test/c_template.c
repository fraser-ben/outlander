#include<unistd.h>
#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<stdbool.h>
#include<semaphore.h>
#include<pthread.h>

static sem_t sem;
static bool bRun = true;


void thread_work(void *arg)
{
    int i = 0;

    printf("Thread starts!\n");

    while (1) {
        sem_wait(&sem);
        if (bRun == false) {
            printf("Break the thread loop!\n");
            break;
        }
        printf("Receive a work. i(%d), it will take 5 secs to finish...\n", i++);
        sleep(5);
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
    printf("Ret(%d) of the thread creation\n");

    while (1) {
        int a;
        printf("Enter 1 to send a work, or 0 to exit the program: \n");
        scanf("%d", &a);
        if (a == 1) {
            sem_post(&sem);
        } else if (a == 0) {
            printf("Exit the program. \n");
            bRun = false;
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
