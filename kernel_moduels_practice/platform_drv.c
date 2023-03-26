#include <linux/module.h>     /* Needed by all modules */ 
#include <linux/kernel.h>     /* Needed for KERN_INFO */ 
#include <linux/init.h>       /* Needed for the macros */ 

#include <sound/soc.h>
#include <sound/pcm.h>
#include <sound/pcm_params.h>

#include "platform_drv.h"
  
MODULE_LICENSE("GPL"); 
MODULE_AUTHOR("Fraser-ben");
MODULE_DESCRIPTION("A simple Hello world LKM!"); 
MODULE_VERSION("0.1");

enum {
    OUTLANDER_DAI_PLAYBACK0 = 0,
    OUTLANDER_DAI_MAX,
};

#if 0 // support in kernel version < 5.4
// OT: outlander
static struct snd_soc_dai_link outlander_dai[] = {
    [OUTLANDER_DAI_PLAYBACK0] = {
	.name = "OUTLANDER PCM",
	.stream_name = "Playback",
	.cpu_dai_name = "OT-pcm.0",
	.codec_dai_name = "OT-pcm-playback",
	.codec_name = "OT-pcm.0-file",
	.platform_name = "outlander-pcm",
	// .init = ot_init,
    },
};

static struct snd_soc_card outlander_card = {
    .name = "outlander-card",
    .owner = THIS_MODULE,
    .dai_link = outlander_dai,
    .num_links = 1,
};
#endif

extern void dump_stack(void);
void backtrace(void)
{
    printk("=====Outlander backtrace start=====\n");
    dump_stack();
    printk("=====backtrace end=====\n");
    return;
}

static int outlander_plat_probe(struct platform_device *pdev) 
{ 
    printk(KERN_INFO "Probe outlander platform driver!!!\n");
    // backtrace();
    return 0; 
} 
  
static int outlander_plat_remove(struct platform_device *pdev) 
{ 
    printk(KERN_INFO "Remove outlander platform drv!!!\n"); 
    return 0;
}

static struct platform_driver outlander_plat_driver = {
	.driver = {
		.name = "outlander-audio",
		.owner = THIS_MODULE,
	},
	.probe = outlander_plat_probe,
	.remove = outlander_plat_remove,
};
// module_platform_driver(outlander_plat_driver);

static struct platform_device *outlander_snd_device;

static int __init outlander_drv_init(void) 
{
    int ret = 0;	
    printk(KERN_INFO "Loading outlander kernel module...\n"); 

    outlander_snd_device = platform_device_alloc("outlander-audio", -1);
    if (!outlander_snd_device) {
	printk(KERN_ERR "Fail to alloc platform device!\n");
	return -ENOMEM;
    } 
    
   ret = platform_device_add(outlander_snd_device);
   if (ret < 0) {
	printk(KERN_WARNING "Already registered a platform device!\n");
   }

    ret = platform_driver_register(&outlander_plat_driver);
    if (ret < 0) {
	printk(KERN_ERR "Fail to register platform driver! ret(%d)\n", ret);
	goto err_plat_device_add;
    }

    return 0;
err_plat_device_add:
    platform_device_put(outlander_snd_device);

    return ret; 
} 
module_init(outlander_drv_init); 
  
static void __exit outlander_drv_exit(void) 
{
    platform_driver_unregister(&outlander_plat_driver);
    platform_device_put(outlander_snd_device);
    printk(KERN_INFO "Goodbye outlander driver!!\n");
} 
module_exit(outlander_drv_exit);


/*
static int __init hello_start(void) 
{ 
    printk(KERN_INFO "Loading hello module...\n"); 
    printk(KERN_INFO "Hello world\n"); 
    return 0; 
} 
  
static void __exit hello_end(void) 
{ 
    printk(KERN_INFO "Goodbye Mr.\n"); 
} 
  
module_init(hello_start); 
module_exit(hello_end);
*/
