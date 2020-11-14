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
import json
import yaml
import os


def process_args():
    parser = argparse.ArgumentParser(description='Runs the script.')

    parser.add_argument('--config', '-c',
                        help='Path where the configuration file can be found, in YML format.',
                        type=str,
                        default=os.path.join('conf', 'config.yaml'))

    parser.add_argument('--apikey', '-a',
                        help='API Key provided by Idealista to access their API.',
                        type=str)

    parser.add_argument('--secret', '-s',
                        help='Secret provided by Idealista to access their API.',
                        type=str)

    return parser.parse_args()


def encode_credentials_in_base64(apikey: str, secret: str) -> str:
    raw_credentials_str = apikey + ':' + secret
    raw_credentials_bytes = raw_credentials_str.encode('ascii')
    base64_credentials_bytes = base64.b64encode(raw_credentials_bytes)
    base64_credentials_str = base64_credentials_bytes.decode('ascii')

    return base64_credentials_str


def login(base_url: str, content_type: str, apikey: str, secret: str) -> str:
    login_credentials = encode_credentials_in_base64(apikey, secret)

    url = base_url + '/oauth/token'
    response = requests.post(url, headers={
        'Content-Type': content_type,
        'Authorization': 'Basic ' + login_credentials
    }, data={
        'scope': 'read',
        'grant_type': 'client_credentials'
    })

    return json.loads(response.content)['access_token']


def search(base_url: str, content_type: str, access_token: str, country: str, operation: str,
           property_type: str, latitude: float, longitude: float, distance: int,
           order: str, sort: str, max_items: int, num_page: int) -> dict:
    url = base_url + '/3.5/' + country + '/search'

    response = requests.post(url, headers={
        'Content-Type': content_type,
        'Authorization': 'Bearer ' + access_token
    }, data={
        'operation': operation,
        'propertyType': property_type,
        'center': str(latitude) + ',' + str(longitude),
        'distance': distance,
        'order': order,
        'sort': sort,
        'maxItems': max_items,
        'numPage': num_page
    })

    return json.loads(response.content)


def extract_key(dictionary: object, key: object) -> object:
    return dictionary[key] if isinstance(dictionary, dict) and key in dictionary else None


def main():
    base_url = 'http://api.idealista.com'
    content_type = 'application/x-www-form-urlencoded;charset=UTF-8'

    args = process_args()
    with open(args.config, 'r') as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.FullLoader)

        access_token = login(base_url=base_url, content_type=content_type,
                             apikey=args.apikey, secret=args.secret)

        results_json = search(base_url=base_url, content_type=content_type, access_token=access_token,
                              country='es', operation='sale', property_type='homes',
                              latitude=40.456176, longitude=-3.690273, distance=900,
                              order='distance', sort='asc',
                              max_items=2, num_page=1)['elementList']

        fields = config['fields']
        element_list = None
        i = 0
        while i < len(fields) and element_list is None:
            if isinstance(fields[i], dict) \
                    and 'elementList' in fields[i] \
                    and 'fields' in fields[i]['elementList']:
                element_list = fields[i]['elementList']
            i += 1
        fields = element_list['fields']

        results_list = [fields] + [
            [
                extract_key(
                    json_item,
                    list(field.keys())[0] if isinstance(field, dict) else field
                )
                for field in fields
            ]
            for json_item in results_json
        ]

        # Flatten columns that contain multiple fields.
        fields = results_list[0]
        column_index = len(fields) - 1
        while column_index >= 0:
            field = fields[column_index]

            # If this column contains multiple fields.
            if isinstance(field, dict):
                field_name = list(field.keys())[0]
                sub_headers = field[field_name]['fields'][::-1]

                # For each row of data.
                for row in range(1, len(results_list)):
                    object_value = results_list[row][column_index]

                    # Flatten field within row.
                    for sub_header in sub_headers:
                        sub_value = extract_key(object_value, sub_header)
                        results_list[row].insert(column_index + 1, sub_value)
                    results_list[row].pop(column_index)

                # Finally, update the headers accordingly.
                for sub_header in sub_headers:
                    fields.insert(column_index + 1, sub_header)
                fields.pop(column_index)

            column_index -= 1

        print(results_list)


if __name__ == '__main__':
    main()
