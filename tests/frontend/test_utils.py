import json

import requests

import sampledb.frontend.utils as utils


def test_custom_format_number():
    assert utils.custom_format_number(0) == "0"
    assert utils.custom_format_number(10) == "10"
    assert utils.custom_format_number(0.1) == "0.1"
    assert utils.custom_format_number(0.12) == "0.12"
    assert utils.custom_format_number(0.123) == "0.123"
    assert utils.custom_format_number(0.1234) == "0.1234"
    assert utils.custom_format_number(0.12345) == "0.12345"
    assert utils.custom_format_number(0.123456) == "0.123456"
    assert utils.custom_format_number(0.1234567) == "0.1234567"
    assert utils.custom_format_number(0.12345678) == "0.12345678"
    assert utils.custom_format_number(0.123456789) == "0.123456789"
    assert utils.custom_format_number(0.1234567890) == "0.123456789"
    assert utils.custom_format_number(0.12345678901) == "0.12345678901"
    assert utils.custom_format_number(0.123456789012) == "0.123456789012"
    assert utils.custom_format_number(0.1234567890123) == "0.1234567890123"
    assert utils.custom_format_number(0.12345678901234) == "0.12345678901234"
    assert utils.custom_format_number(0.123456789012345) == "0.123456789012345"
    assert utils.custom_format_number(0.01) == "0.01"
    assert utils.custom_format_number(0.001) == "0.001"
    assert utils.custom_format_number(0.0001) == "0.0001"
    assert utils.custom_format_number(0.00001) == "1E-5"
    assert utils.custom_format_number(0.000001) == "1E-6"
    assert utils.custom_format_number(0.000000123456789) == "1.23456789E-7"
    assert utils.custom_format_number(100) == "100"
    assert utils.custom_format_number(1000) == "1000"
    assert utils.custom_format_number(10000) == "10000"
    assert utils.custom_format_number(100000) == "100000"
    assert utils.custom_format_number(1000000) == "1E6"
    assert utils.custom_format_number(1234567) == "1.234567E6"


def test_relative_url_for(app):
    app.config['SERVER_NAME'] = 'https://localhost'
    with app.app_context():
        assert utils.relative_url_for('frontend.object', object_id=1) == 'objects/1'
        assert utils.relative_url_for('frontend.object', object_id=1, _external=True) == 'objects/1'