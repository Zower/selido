#!/usr/bin/env python3

import requests

r = requests.get('http://localhost:3000')

print(r.text)