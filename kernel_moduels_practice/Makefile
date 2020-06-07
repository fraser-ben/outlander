
KERNEL_DIR = /home/pi/linux
obj-m = test.o

all:
	make -C ${KERNEL_DIR} M=$(PWD) modules
clean:
	make -C ${KERNEL_DIR} M=$(PWD) clean
