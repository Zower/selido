import requests

import commands
import helpers
import config
import option

from threading import Timer


def request(args):
    args = helpers.check_url(args, True)

    # Yeah..
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    r = requests.get(args.url + '/authenticate/ca/', verify=False)

    parsed = commands.parse_response(r.text, False)

    helpers.print_sha3_hex_hash(parsed['objects'])

    ans = input(
        "Type 'selido auth hash' on an authenticated machine, then make absolutely sure the two hashes match, if not, ABORT. Continue? (y/n): ")

    if ans == 'y':
        try:
            with open(config.certs_location / 'ca.crt', "w") as f:
                f.write(parsed['objects'])
                f.close()
        except OSError as e:
            print(e)
            exit(1)

        a = requests.get(args.url + '/authenticate/' + args.name,
                         verify=config.certs_location / 'ca.crt')
        parsed = commands.parse_response(a.text, False)

        try:
            with open(config.certs_location / (args.name + '.key'), "w") as f:
                f.write(parsed['objects']['key'])
                f.close()
        except OSError as e:
            print(e)
            exit(1)

        print("-------------------------------------------------------------------")
        print("Your code is: ", end='')
        for code in parsed['objects']['code']:
            print(code, end=" ")
        print()
        print("Type selido auth verify on an authenticated client.")
        print("-------------------------------------------------------------------")
        print("Waiting for verification from authenticated client....")

        body = {}
        obj = {'name': args.name, 'code': parsed['objects']['code']}
        body = commands.add_to_body(body, 'code', obj)

        Timer(0.5, authenticated_yet, [
            args, body]).start()


def authenticated_yet(args, body):
    r = requests.post(args.url + '/authenticated/',
                      json=body,
                      verify=config.certs_location / 'ca.crt')

    parsed = commands.parse_response(r.text, False)
    if r.status_code == 200:
        try:
            with open(config.certs_location / (args.name + '.crt'), "w") as f:
                f.write(parsed['objects'])
            print("You are now verified!")
            exit(0)
        except OSError as e:
            print(e)
            exit(1)
    elif r.status_code == 401:
        # Still waiting
        Timer(0.5, authenticated_yet, [args, body]).start()
    elif r.status_code == 403:
        print(parsed['message'])
        exit(1)
    else:
        print("Something went wrong, exiting")
        print(parsed)
        exit(1)


def hash(args):
    args = helpers.check_ca_cert(args)

    with open(args.ca_file, "r") as f:
        helpers.print_sha3_hex_hash(str(f.read()))


def verify(args):
    args = helpers.check_defaults(args)

    r = commands.send_request(args, commands.Method.GET, '/authenticate/')
    parsed = commands.parse_response(r.text, False)

    oc = option.Option(parsed['objects'])
    send = oc.print_and_return_answer()

    print(send)

    body = {}
    body = commands.add_to_body(body, "code", send)

    p = commands.send_request(
        args, commands.Method.POST, '/authenticate/', body)
    parsed = commands.parse_response(p.text, False)
    print(parsed['message'])
