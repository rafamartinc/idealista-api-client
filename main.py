#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2020 Rafael Martín-Cuevas Redondo

"""
Script used to obtain data from Idealista, through their API, with
the appropriate credentials.
"""

from __future__ import print_function
import argparse
import requests
import base64


def process_args():
    parser = argparse.ArgumentParser(description='Runs the script.')

    parser.add_argument('--apikey', '-a',
                        help='API Key provided by Idealista to access their API.',
                        type=str)

    parser.add_argument('--secret', '-s',
                        help='Secret provided by Idealista to access their API.',
                        type=str)

    return parser.parse_args()


def main():

    base_url = 'http://api.idealista.com'
    args = process_args()

    raw_credentials_str = args.apikey + ':' + args.secret
    raw_credentials_bytes = raw_credentials_str.encode('ascii')
    base64_credentials_bytes = base64.b64encode(raw_credentials_bytes)
    base64_credentials_str = base64_credentials_bytes.decode('ascii')

    url = base_url + '/oauth/token'
    response = requests.post(url, headers={
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Authorization': 'Basic ' + base64_credentials_str
    }, data={
        'scope': 'read',
        'grant_type': 'client_credentials'
    })

    print(response.content)


if __name__ == '__main__':
    main()
