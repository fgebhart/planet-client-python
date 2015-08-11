# Copyright 2015 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from . import exceptions
import json
import os
import re
from ._fatomic import atomic_open

_ISO_FMT = '%Y-%m-%dT%H:%M:%S.%f+00:00'


def _planet_json_file():
    return os.path.join(os.path.expanduser('~'), '.planet.json')


def read_planet_json():
    fname = _planet_json_file()
    contents = {}
    if os.path.exists(fname):
        with open(fname, 'r') as fp:
            contents = json.loads(fp.read())
    return contents


def build_conditions(workspace):
    '''Convert a workspace to conditions/filters that can be used in API
    queries. Walks the workspace.filters object and returns a dict of query
    parameters in the form of [metadata name].[comparator]:[value] pairs.
    '''
    conditions = {}
    filters = workspace.get('filters')

    keys = set(filters.keys())
    keys.remove('geometry')

    # workspace stores this as an int, API wants a label
    rules = filters.get('image_statistics.image_quality', None)
    if rules:
        labels = ['test', 'standard', 'target']
        for k, v in rules.items():
            rules[k] = labels[int(v)]
        filters['image_statistics.image_quality'] = rules

    for key in keys:
        rules = filters[key]
        conditions.update([
            ('%s.%s' % (key, r), v) for r, v in rules.items()
        ])
    return conditions


def write_planet_json(contents):
    fname = _planet_json_file()
    with atomic_open(fname, 'w') as fp:
        fp.write(json.dumps(contents))


def feature_collection(geometry):
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": geometry
        }]
    }


def get_workspace_geometry(workspace):
    return workspace['filters'].get('geometry', {}).get('intersects', None)


def geometry_from_json(obj):
    '''try to find a geometry in the provided JSON object'''
    obj_type = obj.get('type', None)
    if not obj_type:
        return None
    if obj_type == 'FeatureCollection':
        features = obj.get('features', [])
        if len(features):
            obj = obj['features'][0]
            obj_type = obj.get('type', None)
        else:
            return None
    if obj_type == 'Feature':
        geom = obj['geometry']
    else:
        # @todo we're just assuming it's a geometry at this point
        geom = obj
    return geom


def check_status(response):
    '''check the status of the response and if needed raise an APIException'''
    status = response.status_code
    if status == 200:
        return
    exception = {
        400: exceptions.BadQuery,
        401: exceptions.InvalidAPIKey,
        403: exceptions.NoPermission,
        404: exceptions.MissingResource,
        429: exceptions.OverQuota,
        500: exceptions.ServerError
    }.get(status, None)

    if exception:
        raise exception(response.text)

    raise exceptions.APIException('%s: %s' % (status, response.text))


def get_filename(response):
    cd = response.headers.get('content-disposition', '')
    match = re.search('filename="?([^"]+)"?', cd)
    if match:
        return match.group(1)


def write_to_file(directory=None, callback=None):
    def writer(body):
        file = os.path.join(directory, body.name) if directory else None
        body.write(file, callback)
    return writer


def strp_timestamp(value):
    return datetime.strptime(value, _ISO_FMT)


def strf_timestamp(when):
    return datetime.strftime(when, _ISO_FMT)


class GeneratorAdapter(list):
    '''Allow a generator to be used in JSON serialization'''
    def __init__(self, gen):
        self.gen = gen

    def __iter__(self):
        return self.gen

    def __len__(self):
        return 1
