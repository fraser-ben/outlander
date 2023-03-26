
KERNEL_DIR = /home/tzupin/linux
obj-m = machine_drv.o
obj-m += platform_drv.o

all:
	make -C ${KERNEL_DIR} M=$(PWD) modules
clean:
	make -C ${KERNEL_DIR} M=$(PWD) clean
