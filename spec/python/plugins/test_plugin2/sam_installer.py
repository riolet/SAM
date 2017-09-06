import os
from sam import constants

THIS_PATH = os.path.dirname(__file__)
import_hook_calls = []
boot_hook_calls = 0


def my_import_hook(db, sub_id, ds_id):
    global import_hook_calls
    import_hook_calls.append((sub_id, ds_id))


def my_boot_hook():
    global boot_hook_calls
    boot_hook_calls += 1


def install():
    # install endpoint
    constants.plugin_urls.extend([
        '/test_url', 'test_plugin2.pages.test_url.TestUrl'
    ])

    # install templates
    constants.plugin_templates.append('test_plugin2')

    # install static files
    constants.plugin_static.append('test_plugin2')

    # install models
    # constants.plugin_models.append(warnings.Warnings)

    # hook plugin into traffic import system.
    constants.plugin_hooks_traffic_import.append(my_import_hook)

    # hook plugin into server startup.
    constants.plugin_hooks_server_start.append(my_boot_hook)
