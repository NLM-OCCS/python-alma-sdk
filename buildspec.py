#!/usr/bin/env python3
import copy
import json
import logging
import sys
from argparse import ArgumentParser
from collections import defaultdict
from urllib.parse import urljoin

import requests
import yaml

LOG = logging.getLogger(__name__)

BOILERPLATE = {
    "openapi": "3.0.1",
    "info": {
        "version": "1.0",
        "title": "Ex Libris APIs",
        "description":
            ("For more information on how to use these APIs, including how to create an"
             "API key required for authentication, see "
             "[Alma REST APIs](https://developers.exlibrisgroup.com/alma/apis)."),
        "termsOfService": "https://developers.exlibrisgroup.com/about/terms"
    },
    "externalDocs": {
        "description": "Detailed documentation on these APIs at the Ex Libris Developer Network.",
        "url": "https://developers.exlibrisgroup.com/alma/apis/"
    },
    "security": [
        {
            "ApiKeyAuth": []
        }
    ],
    "servers": [
        {
            "url": "https://api-na.hosted.exlibrisgroup.com"
        }
    ],
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "description": (
                    "API key used to authorize requests. Learn about how to create"
                    "API keys at "
                    "[Alma REST APIs](https://developers.exlibrisgroup.com/alma/apis/#defining)"
                ),
                "in": "query",
                "name": "apikey"
            }
        },
        "headers": {
            "remaining": {
                "description": (
                    "The number of remaining calls according to the "
                    "[Governance Threshold](https://developers.exlibrisgroup.com/alma/apis/#threshold)"
                ),
                "schema": {
                    "type": "integer"
                }
            }
        }
    }
}


def update_refs(url, op):
    # update $ref in the output
    try:
        success_content = op['responses']['200']['content']
        for body in success_content.values():
            schema = body.get('schema')
            if schema and '$ref' in schema:
                schema['$ref'] = urljoin(url, schema['$ref'])
    except KeyError:
        pass

    # update requestBody content
    try:
        request_content = op['requestBody']['content']
        for body in request_content.values():
            schema = body.get('schema')
            if schema and '$ref' in schema:
                schema['$ref'] = urljoin(url, schema['$ref'])
    except KeyError:
        pass


def build_spec(path, output=None):
    if output is None:
        output = sys.stdout
    with open(path, 'r') as f:
        spec_of_specs = yaml.load(f, Loader=yaml.SafeLoader)

    tag_names = set()
    paths = defaultdict(dict)

    for to_spec in spec_of_specs:
        url = to_spec['url']
        change_tags = to_spec.get('tags')
        if change_tags and not isinstance(change_tags, list):
            change_tags = [change_tags]
        operations = to_spec['operations']
        print(f'Processing {url} ...', file=sys.stderr)
        r = requests.get(url)
        spec = r.json()
        inverted_ops = {value: key for key, value in operations.items()}
        for path, methods in spec['paths'].items():
            for method, op in methods.items():
                new_id = inverted_ops.get(op['operationId'], None)
                if not new_id:
                    print(f' {method} {path} not mapped', file=sys.stderr)
                else:
                    print(f' {method} {path} mapped to {new_id}', file=sys.stderr)
                    del inverted_ops[op['operationId']]
                    new_op = copy.deepcopy(op)
                    if change_tags:
                        new_op['tags'] = change_tags
                    new_op['operationId'] = new_id
                    update_refs(url, new_op)
                    paths[path][method] = new_op
                    for name in new_op['tags']:
                        tag_names.add(name)
        for key in inverted_ops.keys():
            print(f'   operationId {key}: not found', file=sys.stderr)
        print('', file=sys.stderr)

    new_spec = copy.copy(BOILERPLATE)
    new_spec.update({
        'tags': [{'name': name} for name in sorted(tag_names)],
        'paths': paths
    })
    json.dump(new_spec, output, indent=2)


def create_parser(program_name):
    parser = ArgumentParser(prog=program_name, description="OpenAPI Specification Builder")
    parser.add_argument('path', metavar='PATH',
                        help='Path to a YAML file that specifies which specifications to combine')
    parser.add_argument('--output', '-o', metavar='PATH', default=None,
                        help='Path for the output specification')
    return parser


def main(args=None):
    if args is None:
        args = sys.argv
    parser = create_parser(args[0])
    opts = parser.parse_args(args[1:])

    output = sys.stdout
    if opts.output:
        output = open(opts.output, 'w')

    build_spec(opts.path, output)

    if opts.output:
        output.close()


if __name__ == '__main__':
    main()
