#include <linux/module.h>
#include <linux/vmalloc.h>
#include <sound/soc.h>

#include "fraser_utils.h"

static struct platform_device *fraser_device = NULL;

static int fraser_platform_drv_probe(struct platform_device *pdev)
{
	int err = 0;
	FRASER_PRINT("PROBE!!\n");
	return err;
}

static int fraser_platform_drv_remove(struct platform_device *pdev)
{
	FRASER_PRINT("Remove!!\n");
	return 0;
}

static const struct of_device_id of_dev_tbl[] = {
	{ .compatible = "fraser,fake_device0", },
	{},
};

static struct platform_driver asoc_machine_driver = {
	.driver = {
		.name = "fraser_device",
		.owner = THIS_MODULE,
#ifdef CONFIG_OF
		.of_match_table = of_dev_tbl,
#endif
	},
	.probe = fraser_platform_drv_probe,
	.remove = fraser_platform_drv_remove,
};

static int __init fraser_module_init(void)
{
	int err = 0;

	FRASER_PRINT("Init driver!!\n");
	fraser_device = platform_device_alloc("fraser_device", -1);
	if (!fraser_device) {
		FRASER_PRINT("platform device(%s) allocation failed!! err(%d)\n", fraser_device->name, err);
		return err;
	}

	err = platform_device_add(fraser_device);
	if (err) {
		FRASER_PRINT("platform device(%s) add failed!! err(%d)\n", fraser_device->name, err);
		return err;
	}

	err = platform_driver_register(&asoc_machine_driver);
	if (err) {
		FRASER_PRINT("driver(%s) registration failed!! err(%d)\n", asoc_machine_driver.driver.name, err);
		return err;
	}
	return err;
}

static void __exit fraser_module_exit(void)
{
	FRASER_PRINT("Exit driver!!\n");
	platform_device_unregister(fraser_device);
	platform_driver_unregister(&asoc_machine_driver);
}

module_init(fraser_module_init);
module_exit(fraser_module_exit);
MODULE_LICENSE("GPL v2");
