# Copyright 2020 Planet Labs, Inc.
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
import json
import logging

import pytest

from planet import geojson, specs
from planet.api import order_details

LOGGER = logging.getLogger(__name__)

TEST_ID = 'doesntmatter'
TEST_PRODUCT_BUNDLE = 'analytic_sr'
TEST_FALLBACK_BUNDLE = 'analytic'
TEST_ITEM_TYPE = 'PSOrthoTile'
TEST_ARCHIVE_FILENAME = '{{name}}_b_{order_id}}.zip'


def test_OrderDetails():
    test_product = order_details.Product(
            [TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE)
    _ = order_details.OrderDetails('test', [test_product])

    _ = order_details.OrderDetails(
        'test',
        [test_product],
        order_details.Delivery(archive_type='zip'),
        order_details.Notifications(email=True),
        [order_details.Tool('file_format', 'COG')]
    )


def test_OrderDetails_from_dict():
    min_details = {
        'name': 'test',
        'products': [
            {
                'item_ids': [TEST_ID],
                'item_type': TEST_ITEM_TYPE,
                'product_bundle': TEST_PRODUCT_BUNDLE
            }
        ],
    }
    _ = order_details.OrderDetails.from_dict(min_details)

    details = {
        'name': 'test',
        'products': [
            {
                'item_ids': [TEST_ID],
                'item_type': TEST_ITEM_TYPE,
                'product_bundle': TEST_PRODUCT_BUNDLE
            }
        ],
        'subscription_id': 1,
        'delivery': {'archive_type': 'zip'},
        'notifications': {'email': True},
        'tools': [
            {'file_format': 'COG'},
            {'toar': {'scale_factor': 10000}}
        ]
    }

    od = order_details.OrderDetails.from_dict(details)
    assert od.subscription_id == 1
    assert od.delivery.archive_type == 'zip'
    assert od.notifications.email
    assert od.tools[0].name == 'file_format'
    assert od.tools[0].parameters == 'COG'
    assert od.tools[1].name == 'toar'
    assert od.tools[1].parameters == {'scale_factor': 10000}


def test_OrderDetails_to_dict():
    test_product = order_details.Product(
            [TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE)

    od = order_details.OrderDetails(
        'test',
        [test_product],
        subscription_id=1,
        delivery=order_details.Delivery(archive_type='zip'),
        notifications=order_details.Notifications(email=True),
        tools=[order_details.Tool('file_format', 'COG')]
        )

    expected = {
        'name': 'test',
        'products': [
            {
                'item_ids': [TEST_ID],
                'item_type': TEST_ITEM_TYPE,
                'product_bundle': TEST_PRODUCT_BUNDLE
            }
        ],
        'subscription_id': 1,
        'delivery': {'archive_type': 'zip'},
        'notifications': {'email': True},
        'tools': [{'file_format': 'COG'}]
    }
    assert expected == od.to_dict()


def test_Product():
    _ = order_details.Product([TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE,
                              fallback_bundle=TEST_FALLBACK_BUNDLE)

    with pytest.raises(specs.SpecificationException):
        _ = order_details.Product([TEST_ID],
                                  'notsupported',
                                  TEST_ITEM_TYPE,
                                  fallback_bundle=TEST_FALLBACK_BUNDLE)

        _ = order_details.Product([TEST_ID],
                                  TEST_PRODUCT_BUNDLE,
                                  'notsupported',
                                  fallback_bundle=TEST_FALLBACK_BUNDLE)

        _ = order_details.Product([TEST_ID],
                                  TEST_PRODUCT_BUNDLE,
                                  TEST_ITEM_TYPE,
                                  fallback_bundle='notsupported')


def test_Product_from_dict():
    test_details = {
      'item_ids': [TEST_ID],
      'item_type': TEST_ITEM_TYPE,
      'product_bundle': f'{TEST_PRODUCT_BUNDLE},{TEST_FALLBACK_BUNDLE}'
      }

    p = order_details.Product.from_dict(test_details)
    assert p.item_ids == [TEST_ID]
    assert p.item_type == TEST_ITEM_TYPE
    assert p.product_bundle == TEST_PRODUCT_BUNDLE
    assert p.fallback_bundle == TEST_FALLBACK_BUNDLE


def test_Product_to_dict():
    p = order_details.Product([TEST_ID], TEST_PRODUCT_BUNDLE, TEST_ITEM_TYPE,
                              fallback_bundle=TEST_FALLBACK_BUNDLE)
    p_dict = p.to_dict()

    expected = {
      "item_ids": [TEST_ID],
      "item_type": TEST_ITEM_TYPE,
      "product_bundle": f'{TEST_PRODUCT_BUNDLE},{TEST_FALLBACK_BUNDLE}'
      }

    assert p_dict == expected


def test_Notifications_from_dict():
    test_details = {
      'email': 'email',
      'webhook_url': 'webhookurl',
      'webhook_per_order': True
      }

    n = order_details.Notifications.from_dict(test_details)
    assert n.email == 'email'
    assert n.webhook_url == 'webhookurl'
    assert n.webhook_per_order


def test_Notifications_to_dict():
    n = order_details.Notifications(email='email')
    assert n.to_dict() == {'email': 'email'}

    n = order_details.Notifications(webhook_url='webhookurl')
    assert n.to_dict() == {'webhook_url': 'webhookurl'}

    n = order_details.Notifications(webhook_per_order=True)
    assert n.to_dict() == {'webhook_per_order': True}


def test_Delivery():
    d = order_details.Delivery(archive_type='Zip')
    assert d.archive_type == 'zip'


@pytest.fixture
def delivery_details():
    return {
      'archive_type': 'zip',
      'single_archive': True,
      'archive_filename': TEST_ARCHIVE_FILENAME
      }


def test_Delivery_from_dict(as3_details, abs_details, delivery_details,
                            gcs_details, gee_details):
    d = order_details.Delivery.from_dict(delivery_details)
    assert isinstance(d, order_details.Delivery)
    assert d.archive_type == 'zip'
    assert d.single_archive
    assert d.archive_filename == TEST_ARCHIVE_FILENAME

    subclass_details = [as3_details, abs_details, gcs_details, gee_details]
    subclasses = [order_details.AmazonS3Delivery,
                  order_details.AzureBlobStorageDelivery,
                  order_details.GoogleCloudStorageDelivery,
                  order_details.GoogleEarthEngineDelivery]
    for details, cls in zip(subclass_details, subclasses):
        assert isinstance(order_details.Delivery.from_dict(details), cls)


def test_Delivery_to_dict(delivery_details):
    d = order_details.Delivery(archive_type='zip',
                               single_archive=True,
                               archive_filename=TEST_ARCHIVE_FILENAME)
    details = d.to_dict()
    assert details == delivery_details

    d = order_details.Delivery(archive_type='zip')
    details = d.to_dict()
    expected = {
      'archive_type': 'zip',
      }
    assert details == expected


@pytest.fixture
def as3_details():
    return {
        'amazon_s3': {
            'aws_access_key_id': 'aws_access_key_id',
            'aws_secret_access_key': 'aws_secret_access_key',
            'bucket': 'bucket',
            'aws_region': 'aws_region'
            },
        'archive_type': 'zip',
    }


def test_AmazonS3Delivery_from_dict(as3_details):
    d2 = order_details.AmazonS3Delivery.from_dict(as3_details)
    assert d2.aws_region == 'aws_region'


def test_AmazonS3Delivery_to_dict(as3_details):
    aws_access_key_id = 'aws_access_key_id'
    aws_secret_access_key = 'aws_secret_access_key'
    bucket = 'bucket'
    aws_region = 'aws_region'
    archive_type = 'zip'

    d = order_details.AmazonS3Delivery(
        aws_access_key_id,
        aws_secret_access_key,
        bucket,
        aws_region,
        archive_type=archive_type)
    details = d.to_dict()
    assert details == as3_details


@pytest.fixture
def abs_details():
    return {
        'azure_blob_storage': {
            'account': 'account',
            'container': 'container',
            'sas_token': 'sas_token',
            },
        'archive_type': 'zip',
    }


def test_AzureBlobStorageDelivery_from_dict(abs_details):
    d2 = order_details.AzureBlobStorageDelivery.from_dict(abs_details)
    assert d2.sas_token == 'sas_token'


def test_AzureBlobStorageDelivery_to_dict(abs_details):
    account = 'account'
    container = 'container'
    sas_token = 'sas_token'
    archive_type = 'zip'

    d = order_details.AzureBlobStorageDelivery(
        account,
        container,
        sas_token,
        archive_type=archive_type)
    details = d.to_dict()
    assert details == abs_details


@pytest.fixture
def gcs_details():
    return {
        'google_cloud_storage': {
            'bucket': 'bucket',
            'credentials': 'credentials',
            },
        'archive_type': 'zip',
    }


def test_GoogleCloudStorageDelivery_from_dict(gcs_details):
    d2 = order_details.GoogleCloudStorageDelivery.from_dict(gcs_details)
    assert d2.credentials == 'credentials'


def test_GoogleCloudStorageDelivery_to_dict(gcs_details):
    bucket = 'bucket'
    credentials = 'credentials'
    archive_type = 'zip'

    d = order_details.GoogleCloudStorageDelivery(
        bucket,
        credentials,
        archive_type=archive_type)
    details = d.to_dict()
    assert details == gcs_details


@pytest.fixture
def gee_details():
    return {
        'google_earth_engine': {
            'project': 'project',
            'collection': 'collection',
            },
        'archive_type': 'zip',
    }


def test_GoogleEarthEngineDelivery_from_dict(gee_details):
    d2 = order_details.GoogleEarthEngineDelivery.from_dict(gee_details)
    assert d2.collection == 'collection'


def test_GoogleEarthEngineDelivery_to_dict(gee_details):
    project = 'project'
    collection = 'collection'
    archive_type = 'zip'

    d = order_details.GoogleEarthEngineDelivery(
        project,
        collection,
        archive_type=archive_type)
    details = d.to_dict()
    assert details == gee_details


def test_Tool():
    _ = order_details.Tool('band_math', 'jsonstring')

    with pytest.raises(specs.SpecificationException):
        _ = order_details.Tool('notsupported', 'jsonstring')


def test_Tool_from_dict():
    details = {
            'band_math': {'b1': 'b1+b2'}
    }
    tool = order_details.Tool.from_dict(details)
    assert tool.name == 'band_math'
    assert tool.parameters == {'b1': 'b1+b2'}

    with pytest.raises(order_details.ToolException):
        _ = order_details.Tool.from_dict({'name': 'val', 'oops': 'error'})


def test_Tool_to_dict():
    _ = order_details.Tool('band_math', 'jsonstring')

    with pytest.raises(specs.SpecificationException):
        _ = order_details.Tool('notsupported', 'jsonstring')


def test_ClipTool_success_dict(geom_geojson):
    ct = order_details.ClipTool(geom_geojson)
    assert ct.name == 'clip'
    assert ct.parameters['aoi'] == geom_geojson


def test_ClipTool_success_geom(geom_geojson):
    geo = geojson.Geometry(geom_geojson)
    ct = order_details.ClipTool(geo)
    assert ct.name == 'clip'
    assert ct.parameters['aoi'] == geom_geojson


def test_ClipTool_wrong_type(point_geom_geojson):
    geom = geojson.Geometry(point_geom_geojson)
    with pytest.raises(geojson.WrongTypeException):
        _ = order_details.ClipTool(geom)
