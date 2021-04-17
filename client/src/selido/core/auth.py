import requests
from threading import Timer
import hashlib
import urllib3

import selido.config as config

from selido.core.client import Body, Method, send_request
from selido.printing import TagPrinter
from selido.options import Options
from selido.parsing import SelidoParser


def request(args):
    # Yeah..
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    r = requests.get(args.url + '/authenticate/ca/', verify=False)

    parser = SelidoParser(r.text)
    ca = parser.parse()

    print_hash(ca['objects'])

    ans = input(
        "Type 'selido auth hash' on an authenticated machine, then make absolutely sure the two hashes match, if not, ABORT. Continue? (y/n): ")

    if ans == 'y':
        try:
            with open(config.CERTS_LOCATION / 'ca.crt', "w") as f:
                f.write(ca['objects'])
                f.close()
        except OSError as e:
            print(e)
            exit(1)

        a = requests.get(args.url + '/authenticate/' + args.name,
                         verify=config.CERTS_LOCATION / 'ca.crt')

        parser = SelidoParser(a.text)
        response = parser.parse()

        try:
            with open(config.CERTS_LOCATION / (args.name + '.key'), "w") as f:
                f.write(response['objects']['key'])
                f.close()
        except OSError as e:
            print(e)
            exit(1)

        print("-------------------------------------------------------------------")
        print("Your code is: ", end='')
        for code in response['objects']['code']:
            print(code, end=" ")
        print()
        print("Type selido auth verify on an authenticated client.")
        print("-------------------------------------------------------------------")
        print("Waiting for verification from authenticated client....")

        b = Body()
        obj = {'name': args.name, 'code': response['objects']['code']}
        b.add('code', obj)

        Timer(0.5, authenticated_yet, [
            args, b.get()]).start()


def authenticated_yet(args, body):
    r = requests.post(args.url + '/authenticated/',
                      json=body,
                      verify=config.CERTS_LOCATION / 'ca.crt')

    parser = SelidoParser(r.text)
    response = parser.parse(False, False)

    if r.status_code == 200:
        try:
            with open(config.CERTS_LOCATION / (args.name + '.crt'), "w") as f:
                f.write(response['objects'])
            print("You are now verified!")
            exit(0)
        except OSError as e:
            print(e)
            exit(1)
    elif r.status_code == 401:
        # Still waiting
        Timer(0.5, authenticated_yet, [args, body]).start()
    elif r.status_code == 403:
        print(response['message'])
        exit(1)
    else:
        print("Something went wrong, exiting")
        print(response)
        exit(1)


def hash(args):
    with open(args.ca_file, "r") as f:
        print_hash(str(f.read()))
        f.close()


def verify(args):
    r = send_request(args, Method.GET, '/authenticate/')

    parser = SelidoParser(r.text)
    resources = parser.parse()

    oc = Options(resources['objects'])
    send = oc.print_and_return_answer()

    b = Body()
    b.add('code', send)

    p = send_request(
        args, Method.POST, '/authenticate/', b.get())
    parser = SelidoParser(p.text)
    parser.parse(True)


#############################################
def print_hash(string):
    s = hashlib.sha3_256()
    s.update(string.encode('utf-8'))

    print("Hash is:")
    print(s.hexdigest())
