#ifndef _FRASER_UTILS_H_
#define _FRASER_UTILS_H_

#define FRASER_PRINT(fmt, args...) \
	do { \
		printk("[%s][%d] " fmt, __func__, __LINE__, ##args); \
	} while (0)

#endif
