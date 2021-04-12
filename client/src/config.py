from pathlib import Path

from config_file import ConfigFile, ParsingError

# Consts/locations
config_location = Path(str(Path.home()) + '/.selido/')
config_name = 'conf.toml'
certs_location = Path(str(Path.home()) + '/.selido/certs/')

##############################################
# Configuration commands


def init(args):  # Should be more robust
    try:
        Path(config_location).mkdir(parents=True, exist_ok=True)
        Path(certs_location).mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        print('Config file directory or certs directory already exists')
        exit(1)

    e = input(
        "Where to connect to selido? If running locally it is likely \"https://localhost:3912\": ")
    set_endpoint(e)

    u = input(
        "Type an identifying username: ")
    set_username(u)


def endpoint(args):
    set_endpoint(args.url)


def username(args):
    set_username(args.username)


##############################################
# Actually configuring

def set_username(username):
    config = get_config()
    try:
        config.set('Cert.username', username)
    except:
        print("Couldn't set username, make sure username is one word")
        exit(1)
    config.save()


def set_endpoint(url):
    config = get_config()

    url_split = url.split(':')

    # This is some jank shit, but https:// get split up so I'm merging them back together
    new_url = []
    new_url.append(url_split[0] + ':' + url_split[1])
    if len(url_split) == 3:
        new_url.append(url_split[2])
    try:
        config.set('Endpoint.url', new_url[0])
        if len(new_url) == 2:
            config.set('Endpoint.port', new_url[1])
        else:
            config.set('Endpoint.port', "")
    except:
        print("Invalid url, Should be: protocol://domain:port or protocol://IP:port")
        exit(1)
    config.save()


def get_config():
    try:
        config = ConfigFile(config_location / config_name)
        return config
    except ParsingError:
        print("Could not parse the config file, check that it hasn't been modified. Location: {}".format(
            str(config_location / config_name)))
        exit(1)
    except ValueError:
        print(
            "Config file extension that isn't supported was used or is a directory"
        )
        exit(1)
    except FileNotFoundError:
        print('Configuration file wasnt found at location {}, maybe run selido init?'.format(
            str(config_location)))
        exit(1)
