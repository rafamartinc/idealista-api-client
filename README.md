# Python Client for Idealista's Search API

You can request access to the API at http://developers.idealista.com/access-request.

### Usage

```
usage: main.py [-h] [--apikey APIKEY] [--secret SECRET]
               [--latitude LATITUDE] [--longitude LONGITUDE]
               [--distance DISTANCE] [--order ORDER] [--sort SORT]
               [--property_type PROPERTY_TYPE]
               [--operation OPERATION] [--country COUNTRY]
               [--num_items NUM_ITEMS] [--output OUTPUT]
               [--config CONFIG]

Runs the script.

optional arguments:
  -h, --help            show this help message and exit
  --apikey APIKEY, -a APIKEY
                        API Key provided by Idealista to access
                        their API.
  --secret SECRET, -s SECRET
                        Secret provided by Idealista to access
                        their API.
  --latitude LATITUDE   Latitude to be used as center of the
                        search area.
  --longitude LONGITUDE
                        Longitude to be used as center of the
                        search area.
  --distance DISTANCE, -d DISTANCE
                        Radius (distance from the center) to be
                        used as search area, in meters (default:
                        1000).
  --order ORDER         Ordering method for the results (default:
                        distance).
  --sort SORT           Sort method, used in conjunction with the
                        ordering method (default: asc).
  --property_type PROPERTY_TYPE
                        Property type (default: homes).
  --operation OPERATION
                        Operation associated to the property
                        (default: sale).
  --country COUNTRY     Country (default: es).
  --num_items NUM_ITEMS, -n NUM_ITEMS
                        Number of items to retrieve, with the
                        specified criteria (default: 50).
  --output OUTPUT, -o OUTPUT
                        Path where the output CSV file should be
                        written (default: output.csv).
  --config CONFIG, -c CONFIG
                        Path where the configuration file can be
                        found, in YML format (default:
                        conf/config.yaml).
```

Example:

```
PYTHONPATH=. python3 -u main.py --apikey API_KEY --secret SECRET --latitude 40.456176 --longitude -3.690273 -d 900 --order distance --sort asc --property_type homes --operation sale --country es -n 100 -o output.csv -c conf/config.yaml
```
