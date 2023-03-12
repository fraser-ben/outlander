#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<stdbool.h>

void func_stack_corruption(long long *s64ptr)
{
    *s64ptr = 0LL;
}

int main(int argc, char *argv[])
{
#if 0
    char buf[8] = {' '};
    strcpy(buf, "aaaabbbbcccc");
#endif

    short x = 1;
    func_stack_corruption(&x);

    return 0;
}
