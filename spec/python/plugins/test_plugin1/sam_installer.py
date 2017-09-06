import os
from sam import constants
from test_plugin1.models.test_model import TestModel


def install():
    # install endpoint
    for i in range(len(constants.default_urls)/2):
        if constants.default_urls[i*2] == '/test_url':
            constants.default_urls[i*2+1] = 'test_plugin2.pages.test_url.TestUrl'

    # install models
    constants.plugin_models.append(TestModel)

    # install importer
    constants.plugin_importers.append('test_plugin1')
