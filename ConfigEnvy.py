from ConfigParser import SafeConfigParser
import os


class ConfigEnvy(SafeConfigParser, object):
    default_file_name = 'default.cfg'

    def __init__(self, namespace, defaults=None, filenames=None):
        self.namespace = namespace
        super(ConfigEnvy, self).__init__(defaults)
        BASE_PATH = os.path.dirname(__file__)
        default_file_name = os.path.join(BASE_PATH, self.default_file_name)
        if os.path.isfile(default_file_name):
            if filenames:
                filenames.push(default_file_name)
            else:
                filenames = default_file_name
        if filenames is not None:
            super(ConfigEnvy, self).read(filenames)

    def get(self, section, option, raw=False, vars=None, default=None):
        """Get an option value for a given section.
        Almost like ConfigParser, but look in the Environment variables first
        Env variables take the form <NAMESPACE>__<SECTION>__<OPTION>"""
        env_option = "{}__{}__{}".format(self.namespace, section, option).upper()
        if env_option in os.environ:

            return os.environ[env_option]
        else:
            if default is not None:
                if not self.has_option(section, option):
                    return default
            return super(ConfigEnvy, self).get(section, option, raw, vars)

    def items(self, section, raw=False, vars=None):
        prefix = '{}__{}__'.format(self.namespace, section).upper()
        overrides = [(k[len(prefix):].lower(), v) for k, v in os.environ.iteritems() if k.startswith(prefix)]
        pairs = dict(super(ConfigEnvy, self).items(section, raw, vars))
        pairs.update(overrides)
        return pairs.items()
