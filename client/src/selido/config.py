from pathlib import Path
from dataclasses import dataclass
from config_file import ConfigFile, ParsingError


# Consts/locations
CONFIG_LOCATION = Path(str(Path.home()) + '/.selido/')
CONFIG_NAME = 'conf.toml'
CERTS_LOCATION = Path(str(Path.home()) + '/.selido/certs/')

##############################################
# Configuration commands


##############################################
# Configuration

@dataclass
class SelidoConfig:
    config: ConfigFile

    # Argparse specific
    def endpoint(self, args):
        self.set_endpoint(args.url)

    # Argparse specific
    def username(self, args):
        self.set_username(args.username)

    def get_username(self):
        return self.config.get('Cert.username')

    def get_endpoint(self, increment=0):
        return "{}:{}".format(self.config.get('Endpoint.url'), int(self.config.get('Endpoint.port')) + increment)

    def set_username(self, username):
        try:
            self.config.set('Cert.username', username)
        except:
            print("Couldn't set username, make sure username is one word")
            exit(1)
        self.config.save()

    def set_endpoint(self, url):
        url_split = url.split(':')

        # This is some jank shit, but https:// get split up so I'm merging them back together
        new_url = []
        new_url.append(url_split[0] + ':' + url_split[1])
        if len(url_split) == 3:
            new_url.append(url_split[2])
        try:
            self.config.set('Endpoint.url', new_url[0])
            if len(new_url) == 2:
                self.config.set('Endpoint.port', new_url[1])
            else:
                self.config.set('Endpoint.port', "")
        except:
            print("Invalid url, Should be: protocol://domain:port or protocol://IP:port")
            exit(1)
        self.config.save()


def get_config():
    try:
        config = ConfigFile(CONFIG_LOCATION / CONFIG_NAME)
        return config
    except ParsingError:
        print("Could not parse the config file, check that it hasn't been modified. Location: {}".format(
            str(CONFIG_LOCATION / CONFIG_NAME)))
        exit(1)
    except ValueError:
        print(
            "Config file extension that isn't supported was used or is a directory"
        )
        exit(1)
    except FileNotFoundError as e:
        print('Configuration file wasnt found at location {}'.format(
            str(CONFIG_LOCATION)))
        _init()


def _init():  # Should be more robust
    print("First time setup being performed..")
    try:
        Path(CONFIG_LOCATION).mkdir(parents=True, exist_ok=True)
        Path(CERTS_LOCATION).mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        print('Config file directory or certs directory already exists')
        exit(1)

    try:
        f = open(CONFIG_LOCATION / CONFIG_NAME, "x")
        config = ConfigFile(CONFIG_LOCATION / CONFIG_NAME)
        f.close()
    except OSError as e:
        print(e)
        exit(1)

    config_parser = SelidoConfig(config)

    e = input(
        "Where to connect to selido? If running locally it is likely \"https://localhost:3912\": ")
    config_parser.set_endpoint(e)

    u = input(
        "Type an identifying username: ")

    config_parser.set_username(u)
