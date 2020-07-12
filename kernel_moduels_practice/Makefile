
KERNEL_DIR = /home/pi/linux
obj-m = platform_drv.o

all:
	make -C ${KERNEL_DIR} M=$(PWD) modules
clean:
	make -C ${KERNEL_DIR} M=$(PWD) clean
