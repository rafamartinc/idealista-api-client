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


def process_args():
    parser = argparse.ArgumentParser(description='Runs the script.')

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

    access_token = login(base_url=base_url, content_type=content_type,
                         apikey=args.apikey, secret=args.secret)

    results = search(base_url=base_url, content_type=content_type, access_token=access_token,
                     country='es', operation='sale', property_type='homes',
                     latitude=40.456176, longitude=-3.690273, distance=900,
                     order='distance', sort='asc',
                     max_items=2, num_page=1)

    json_contents = results['elementList']

    headers = [
        'address', 'bathrooms', 'country', 'distance', 'district', 'exterior',
        'floor', 'hasVideo', 'latitude', 'longitude', 'municipality', 'neighborhood',
        'numPhotos', 'operation', 'price', 'propertyCode', 'province', 'region',
        'rooms', 'showAddress', 'size', 'subregion', 'thumbnail', 'url', 'status',
        'newDevelopment', 'tenantGender', 'garageType',
        {
            'object_name': 'parkingSpace',
            'headers': ['hasParkingSpace', 'isParkingSpaceIncludedInPrice', 'parkingSpacePrice']
        },
        'hasLift', 'newDevelopmentFinished', 'isSmokingAllowed', 'priceByArea',
        {
            'object_name': 'detailedType',
            'headers': ['typology', 'subTypology']
        },
        'externalReference'
    ]

    list_contents = [headers] + [
        [
            extract_key(
                json_item,
                header['object_name'] if isinstance(header, dict) else header
            )
            for header in headers
        ]
        for json_item in json_contents
    ]

    # Flatten columns that contain multiple fields.
    headers = list_contents[0]
    column_index = len(headers) - 1
    while column_index >= 0:
        header = headers[column_index]

        # If this column contains multiple fields.
        if isinstance(header, dict):
            sub_headers = header['headers'][::-1]

            # For each row of data.
            for row in range(1, len(list_contents)):
                object_value = list_contents[row][column_index]

                # Flatten field within row.
                for sub_header in sub_headers:
                    sub_value = extract_key(object_value, sub_header)
                    list_contents[row].insert(column_index + 1, sub_value)
                list_contents[row].pop(column_index)

            # Finally, update the headers accordingly.
            for sub_header in sub_headers:
                headers.insert(column_index + 1, sub_header)
            headers.pop(column_index)

        column_index -= 1

    print(list_contents)


if __name__ == '__main__':
    main()
