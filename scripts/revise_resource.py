"""
Given a Resource JSON file, add in some denormalized bits.

This ensures that we're not doing expensive lookups, nor loading more JSON
files, at run-time.

Transformations Applied:

* Denormalized shape information into the Resources themselves

"""
import json
import logging
import os
import sys


BASE_PATH = os.path.dirname(__file__)
DEFAULT_AWS_RESOURCE_PATH = os.path.join(
    BASE_PATH,
    'boto3',
    'data',
    'aws',
    'resources'
)


class RevisionError(Exception):
    pass


class ShapeNotFound(RevisionError):
    pass


class Revisor(object):
    def __init__(self, service_json_path, resource_json_path, output_path=None):
        self.service_json_path = service_json_path
        self.resource_json_path = resource_json_path
        self.output_path = output_path
        self.log = self.get_log()

        if self.output_path is None:
            base = os.path.basename(self.resource_json_path)
            self.output_path = os.path.join(DEFAULT_AWS_RESOURCE_PATH, base)
            self.log.info(
                "No output path provided. Outputting to '{0}'...".format(
                    self.output_path
                )
            )

    def get_log(self):
        return logging.getLogger(__file__)

    def load_json(self, json_path):
        if not os.path.exists(json_path):
            raise RevisionError(
                "File '{0}' does not exist.".format(
                    json_path
                )
            )

        with open(json_path, 'r') as json_file:
            return json.load(json_file)

    def find_shape(self, service_json, shape_name):
        if 'shape_name' in service_json:
            if shape_name == service_json['shape_name']:
                # Return the surrounding structure.
                return service_json
        else:
            # TODO: This is very depth-first-y. Should it be breadth-first
            #       instead?
            for key, value in service_json.items():
                if isinstance(value, dict):
                    found = self.find_shape(value, shape_name)

                    if found is not None:
                        return found

        # We didn't find it. Return ``None`` & hope some other recursive call
        # finds it.
        return None

    def revise(self):
        # * Load the (service) JSON.
        # * Load the resource_description JSON.
        # * Iterate over the resource keys.
        #   * Look for ``shape_name``.
        #   * Recusively descend through the (service) JSON looking for that shape.
        #   * When it's found, denorm its details into the (resource) JSON.
        # * Dump the resulting (modified resource) JSON to the proper place on the
        #   FS.
        service_json = self.load_json(self.service_json_path)
        resource_json = self.load_json(self.resource_json_path)

        # Need a copy, since we'll be modifying the original.
        data = resource_json['resources'].copy()

        for resource_name, resource_data in data.items():
            if 'shape_name' in resource_data:
                shape_name = resource_data['shape_name']
                shape = self.find_shape(service_json, shape_name)

                if shape is None:
                    # This is bad. Toss an exception.
                    raise ShapeNotFound(
                        "Could not find shape '{0}' within '{1}.".format(
                            shape_name,
                            self.service_json_path
                        )
                    )

                resource_json[resource_name]['shape'] = shape

        self.dump_json(resource_json)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s',
        '--service',
        action='store',
        dest='service',
        help='The path to the service JSON file (ex. `/path/to/botocore/services/s3.json`).'
    )
    parser.add_argument(
        '-r',
        '--resource',
        action='store',
        dest='resource',
        help='The path to the resource JSON file (ex. `/path/to/boto3/resource_descriptions/s3-2006-03-01.json`).'
    )
    parser.add_argument(
        '-o',
        '--output',
        action='store',
        dest='output',
        required=False,
        default=None,
        help='The output path for the revised resource JSON file.'
    )

    opts = parser.parse_args()
    rev = Revisor(
        service_json_path=opts.service,
        resource_json_path=opts.resource,
        output_path=opts.output,
    )
    rev.revise()
