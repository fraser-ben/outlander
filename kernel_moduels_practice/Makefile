
KERNEL_DIR = /home/pi/linux
obj-m = sound_module.o

all:
	make -C ${KERNEL_DIR} M=$(PWD) modules
clean:
	make -C ${KERNEL_DIR} M=$(PWD) clean
