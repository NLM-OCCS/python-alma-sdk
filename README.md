# Python Alma SDK

## Summary

Cherry pick OpenAPI operations from multiple ExLibris Alma and Primo OpenAPI specifications,
combine into one OpenAPI specification, and generate a Python SDK.

## Background

ExLibris provides a robust REST API for both Alma and Primo. Since the applications
are complex, ExLibris structures their offering by making multiple OpenAPI documents
available.

## Features

- Combine multiple OpenAPI specifications into one
- Cherry pick API calls based on their ExLibris assigned operationId
- Remap these API calls to our own operationId, for better method naming
- Overlay source code for add-on capabilities and a more capable client

## Dependencies

- Python 3.5+ (CPython 3.6 used for development)
- Java 1.8+
- Apache Ant

## How to build

- Update `metaspec.yaml` with all the OpenAPI specs and operations you will need.
- Run `ant bootstrap` to install Apache Ivy into `$HOME/.ant/lib`.
- Run `ant resolve` to download swagger-codegen-cli into the `lib` sub-directory.
- Run `ant build` to build your SDK in the `target` sub-directory.

## Theory of Operation

- A YAML file specifies which OpenAPI specifications to combine,
  and which operations to cherry pick.
- The code reads this YAML and downloads each specification
- Only the operations listed are copied to a new combined specification.
- schema references to external ExLibris schemas are resolved, in the sense
  that we make the URLs to these full rather than relative URIs.
- swagger-codegen-cli is then used to create a Python SDK using only the APIs
  needed, across multiple ExLibris provided specifications.
- The `src` sub directory is then copied on top of the created SDK

## What this is not

This is not a general purpose tool.  It rests on some assumptions:

* The server URLs are the same for all of these, and they use
  a common api key mechanism for authentication.
* ExLibris does not embed definitions in their OpenAPI specifications, but
  always uses external references.
* Only response status code 200 and requestBody are considered when
  rewriting schema references.
* Only top-level occurrences of $ref are considered.
