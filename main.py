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

    parser.add_argument('--apikey', '-a',
                        help='API Key provided by Idealista to access their API.',
                        type=str)

    parser.add_argument('--secret', '-s',
                        help='Secret provided by Idealista to access their API.',
                        type=str)

    parser.add_argument('--latitude',
                        help='Latitude to be used as center of the search area.',
                        type=float)

    parser.add_argument('--longitude',
                        help='Longitude to be used as center of the search area.',
                        type=float)

    parser.add_argument('--distance', '-d',
                        help='Radius (distance from the center) to be used as search area, in meters (default: 1000).',
                        type=int,
                        default=1000)

    parser.add_argument('--order',
                        help='Ordering method for the results (default: distance).',
                        type=str,
                        default='distance')

    parser.add_argument('--sort',
                        help='Sort method, used in conjunction with the ordering method (default: asc).',
                        type=str,
                        default='asc')

    parser.add_argument('--property_type',
                        help='Property type (default: homes).',
                        type=str,
                        default='homes')

    parser.add_argument('--operation',
                        help='Operation associated to the property (default: sale).',
                        type=str,
                        default='sale')

    parser.add_argument('--country',
                        help='Country (default: es).',
                        type=str,
                        default='es')

    parser.add_argument('--num_items', '-n',
                        help='Number of items to retrieve, with the specified criteria (default: 50).',
                        type=int,
                        default=50)

    parser.add_argument('--output', '-o',
                        help='Path where the output CSV file should be written (default: output.csv).',
                        type=str,
                        default='output.csv')

    parser.add_argument('--config', '-c',
                        help='Path where the configuration file can be found, in YML format (default: conf/config.yaml).',
                        type=str,
                        default=os.path.join('conf', 'config.yaml'))

    return parser.parse_args()


def get_keys(config: dict) -> list:
    fields = config['keys']

    i = 0
    element_list = None
    while i < len(fields) and element_list is None:
        if isinstance(fields[i], dict) \
                and 'elementList' in fields[i] \
                and 'keys' in fields[i]['elementList']:
            element_list = fields[i]['elementList']
        i += 1

    return element_list['keys']


def encode_credentials_in_base64(apikey: str, secret: str) -> str:
    raw_credentials_str = apikey + ':' + secret
    raw_credentials_bytes = raw_credentials_str.encode('ascii')
    base64_credentials_bytes = base64.b64encode(raw_credentials_bytes)
    base64_credentials_str = base64_credentials_bytes.decode('ascii')

    return base64_credentials_str


def design_download_plan(total_items: int, max_per_batch: int = 50) -> list:
    remainder = total_items % max_per_batch
    num_pages = int((total_items - remainder) / max_per_batch) + (1 if remainder > 0 else 0)

    plan = []
    for page in range(num_pages):
        if page == num_pages - 1 and remainder > 0:
            plan.append({
                'page': page + 1,
                'items': remainder
            })
        else:
            plan.append({
                'page': page + 1,
                'items': max_per_batch
            })

    return plan


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

    if response.status_code == 429:
        raise TooManyRequestsException('You have reached your monthly quota.')

    return json.loads(response.content)


def extract_value(dictionary: object, key: object) -> object:
    return dictionary[key] if isinstance(dictionary, dict) and key in dictionary else None


def convert_results_from_json_to_table(results: dict, keys: list) -> list:
    results = [keys] + [
        [
            extract_value(
                json_item,
                list(field.keys())[0] if isinstance(field, dict) else field
            )
            for field in keys
        ]
        for json_item in results
    ]

    flatten_keys_with_nested_sub_keys(results)

    return results


def flatten_keys_with_nested_sub_keys(results: list) -> None:
    keys = results[0]
    column_index = len(keys) - 1
    while column_index >= 0:
        key = keys[column_index]

        # If this column contains multiple fields.
        if isinstance(key, dict):
            key_name = list(key.keys())[0]
            sub_keys = key[key_name]['keys'][::-1]

            for row in range(1, len(results)):
                flatten_value(results[row], column_index, sub_keys)

            flatten_key(keys, column_index)

        column_index -= 1


def flatten_key(keys: list, column_index: int) -> None:
    key = keys[column_index]
    key_name = list(key.keys())[0]
    sub_keys = key[key_name]['keys'][::-1]

    for sub_key in sub_keys:
        keys.insert(column_index + 1, sub_key)
    keys.pop(column_index)


def flatten_value(row: list, column_index: int, sub_keys: list) -> None:
    object_value = row[column_index]

    for sub_header in sub_keys:
        sub_value = extract_value(object_value, sub_header)
        row.insert(column_index + 1, sub_value)

    row.pop(column_index)


def export_to_csv_file(results: list, file_name: str) -> None:

    if results is None:
        print('No results found.')
    else:
        with open(file_name, 'w') as output_file:
            for line in results:
                output_file.write(';'.join(
                    [str(i) for i in line]
                ) + '\n')


def main():

    base_url = 'http://api.idealista.com'
    content_type = 'application/x-www-form-urlencoded;charset=UTF-8'

    args = process_args()
    with open(args.config, 'r') as ymlfile:

        config = yaml.load(ymlfile, Loader=yaml.FullLoader)
        keys = get_keys(config)

        access_token = login(base_url=base_url, content_type=content_type,
                             apikey=args.apikey, secret=args.secret)

        plan = design_download_plan(args.num_items)
        full_results = None

        for iteration in plan:

            try:
                partial_results = search(base_url=base_url, content_type=content_type,
                                         access_token=access_token, country=args.country,
                                         operation=args.operation, property_type=args.property_type,
                                         latitude=args.latitude, longitude=args.longitude,
                                         distance=args.distance, order=args.order, sort=args.sort,
                                         max_items=iteration['items'], num_page=iteration['page'])['elementList']

                partial_results = convert_results_from_json_to_table(partial_results, keys)

                if full_results is None:
                    full_results = partial_results
                else:
                    full_results.extend(partial_results[1:])

            except TooManyRequestsException as ex:
                print(ex)

        export_to_csv_file(full_results, args.output)


class TooManyRequestsException(Exception):
    pass


if __name__ == '__main__':
    main()
