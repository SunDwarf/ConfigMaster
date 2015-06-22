import io
import yaml
import yaml.scanner
from .ConfigFile import ConfigFile

from . import exc

from . import ConfigKey

def cload_safe(fd):
    """
    Wrapper for the YAML Cloader.
    :param fd: The file descriptor to open.
    :return: The YAML dict.
    """
    return yaml.load(fd, Loader=yaml.CSafeLoader)

def cload_load(fd):
    """
    Wrapper for the YAML Cloader.
    :param fd: The file descriptor to open.
    :return: The YAML dict.
    """
    return yaml.load(fd, Loader=yaml.CLoader)

class YAMLConfigFile(ConfigFile):
    """
    The core YAMLConfigFile class.

    This handles automatically opening/creating the YAML configuration files.

    >>> import configmaster.YAMLConfigFile
    >>> cfg = configmaster.YAMLConfigFile.YAMLConfigFile("test.yml") # Accepts a string for input

    >>> fd = open("test.yml") # Accepts a file descriptor too
    >>> cfg2 = configmaster.YAMLConfigFile.YAMLConfigFile(fd)

    ConfigMaster objects accepts either a string for the relative path of the YAML file to load, or a :io.TextIOBase: object to read from.
    If you pass in a string, the file will automatically be created if it doesn't exist. However, if you do not have permission to write to it, a :PermissionError: will be raised.

    To access config objects programmatically, a config object is exposed via the use of cfg.config.
    These config objects can be accessed via cfg.config.attr, without having to resort to looking up objects in a dict.

    >>> # Sample YAML data is abc: [1, 2, 3]
    ... print(cfg.config.abc) # Prints [1, 2, 3]

    ConfigMaster automatically uses YAML's CLoader/CSafeLoader and CDumper for speed performances.

    By default, all loads are safe. You can turn this off by passing safe_load as False.
    However, you must remember that these can construct **ANY ARBITARY PYTHON OBJECT**. Make sure to verify the data before you unsafe load it.
    """
    def __init__(self, fd: io.TextIOBase, safe_load: bool=True):
        """
        :param fd: The file to load.
                Either a string or a :io.TextIOBase: object.
        :param safe_load: Should we safe_load or not?
        """
        super().__init__(fd)
        self.safe_load = safe_load
        self.config = None

        self.load()

    def load(self):
        # Should we safe load the file?
        # This is always on by default, for security reasons.
        if self.safe_load:
            # Assign 'loader' to the safe YAML CSafeLoader.
            if yaml.__with_libyaml__:
                loader = cload_safe
            else:
                loader = yaml.safe_load
        # Otherwise, use the YAML CLoader.
        else:
            if yaml.__with_libyaml__:
                loader = cload_load
            else:
                loader = yaml.load
        # Setup dumper.
        if yaml.__with_libyaml__:
            self.dumper = yaml.CDumper
        else:
            self.dumper = yaml.Dumper
        # Load the YAML file.
        try:
            data = loader(self.fd)
        except UnicodeDecodeError:
            raise exc.LoaderException("Selected file was not in a valid encoding format.")
        except yaml.scanner.ScannerError:
            raise exc.LoaderException("Selected file had invalid YAML tokens.")
        # Serialize the data into new sets of ConfigKey classes.
        self.config = ConfigKey.ConfigKey.parse_data(data)


    def dump(self):
        """
        Dumps all the data into a YAML file.
        """
        name = self.fd.name
        self.fd.close()
        self.fd = open(name, 'w')

        data = self.config.dump()
        yaml.dump(data, self.fd, Dumper=self.dumper, default_flow_style=False)
        self.reload()

    def initial_populate(self, data):
        """
        Repopulate the ConfigMaster object with data.
        :param data: The data to populate.
        :return: If it was populated.
        """
        if self.config.parsed:
            return False
        # Otherwise, create a new ConfigKey.
        self.config = ConfigKey.ConfigKey.parse_data(data)
        return True