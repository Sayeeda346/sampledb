# coding: utf-8
"""

"""

import requests
import pytest
from bs4 import BeautifulSoup

import sampledb
import sampledb.models
import sampledb.logic


from tests.test_utils import flask_server, app


@pytest.fixture
def user(flask_server):
    with flask_server.app.app_context():
        user = sampledb.models.User(name="Basic User", email="example@fz-juelich.de", type=sampledb.models.UserType.PERSON)
        sampledb.db.session.add(user)
        sampledb.db.session.commit()
        # force attribute refresh
        assert user.id is not None
    return user


def test_user_preferences(flask_server):
    # Try logging in with ldap-test-account
    session = requests.session()
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    assert document.find('input', {'name': 'username', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'password', 'type': 'password'}) is not None
    assert document.find('input', {'name': 'remember_me', 'type': 'checkbox'}) is not None
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': flask_server.app.config['TESTING_LDAP_LOGIN'],
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'remember_me': False,
        'csrf_token': csrf_token
    })

    assert r.status_code == 200

    r = session.get(flask_server.base_url + 'users/me/preferences')
    assert r.status_code == 200
    assert document.find('input', {'name': 'name', 'type': 'text'}) is None
    assert document.find('input', {'name': 'email', 'type': 'text'}) is None


def test_user_preferences_userid_wrong(flask_server):
    # Try logging in with ldap-test-account
    session = requests.session()
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    assert document.find('input', {'name': 'username', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'password', 'type': 'password'}) is not None
    assert document.find('input', {'name': 'remember_me', 'type': 'checkbox'}) is not None
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': flask_server.app.config['TESTING_LDAP_LOGIN'],
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'remember_me': False,
        'csrf_token': csrf_token
    })

    assert r.status_code == 200

    r = session.get(flask_server.base_url + 'users/10/preferences')
    assert r.status_code == 403


def test_user_preferences_change_name(flask_server):
    # Try logging in with ldap-test-account
    session = requests.session()
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    assert document.find('input', {'name': 'username', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'password', 'type': 'password'}) is not None
    assert document.find('input', {'name': 'remember_me', 'type': 'checkbox'}) is not None
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': flask_server.app.config['TESTING_LDAP_LOGIN'],
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'remember_me': False,
        'csrf_token': csrf_token
    })

    assert r.status_code == 200

    url = flask_server.base_url + 'users/me/preferences'
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers['Location'].startswith(flask_server.base_url + 'users/')
    assert r.headers['Location'].endswith('/preferences')
    url = r.headers['Location']
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 200

    with flask_server.app.app_context():
        user = sampledb.models.users.User.query.filter_by(email="d.henkel@fz-juelich.de").one()

    assert user.name == "Doro Testaccount"

    document = BeautifulSoup(r.content, 'html.parser')
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']

    # Submit the missing information and complete the registration
    r = session.post(url, {
        'name': 'Doro Testaccount1111',
        'email': 'd.henkel@fz-juelich.de',
        'csrf_token': csrf_token,
        'change': 'Change'
    })

    #check, if email was changed
    assert r.status_code == 200
    with flask_server.app.app_context():
        user = sampledb.models.users.User.query.filter_by(email="d.henkel@fz-juelich.de").one()

    assert user.name == "Doro Testaccount1111"


def test_user_preferences_change_contactemail(flask_server):
    # Try logging in with ldap-test-account
    session = requests.session()
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    assert document.find('input', {'name': 'username', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'password', 'type': 'password'}) is not None
    assert document.find('input', {'name': 'remember_me', 'type': 'checkbox'}) is not None
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': flask_server.app.config['TESTING_LDAP_LOGIN'],
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'remember_me': False,
        'csrf_token': csrf_token
    })

    assert r.status_code == 200

    url = flask_server.base_url + 'users/me/preferences'
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers['Location'].startswith(flask_server.base_url + 'users/')
    assert r.headers['Location'].endswith('/preferences')
    url = r.headers['Location']

    user_id = int(url[len(flask_server.base_url + 'users/'):].split('/')[0])

    r = session.get(url, allow_redirects=False)
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    assert document.find('input', {'name': 'name', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'email', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'name', 'type': 'text'})["value"] != ""
    assert document.find('input', {'name': 'email', 'type': 'text'})["value"] != ""

    # Send a POST request to the confirmation url
    # TODO: require authorization
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    with flask_server.app.app_context():
        assert sampledb.logic.user_log.get_user_log_entries(user_id) == []
    # Submit the missing information and complete the registration
    with sampledb.mail.record_messages() as outbox:
        r = session.post(url, {
            'name': 'Doro Testaccount1',
            'email': 'example@fz-juelich.de',
            'csrf_token': csrf_token,
            'change': 'Change'
        })
        assert r.status_code == 200

    with flask_server.app.app_context():
        user_log_entries = sampledb.logic.user_log.get_user_log_entries(user_id)
        assert len(user_log_entries) == 1
        assert user_log_entries[0].type == sampledb.models.UserLogEntryType.EDIT_USER_PREFERENCES
        assert user_log_entries[0].user_id == user_id
        assert user_log_entries[0].data == {}
    assert r.status_code == 200

    # Check if an invitation mail was sent
    assert len(outbox) == 1
    assert 'example@fz-juelich.de' in outbox[0].recipients
    message = outbox[0].html
    assert 'Welcome to iffsample!' in message

    confirmation_url = flask_server.base_url + message.split(flask_server.base_url)[1].split('"')[0]
    assert confirmation_url.startswith(flask_server.base_url + 'users/confirm-email')
    r = session.get(confirmation_url)


    # check, if email was changed after open confirmation_url
    with flask_server.app.app_context():
        user = sampledb.models.users.User.query.filter_by(email="example@fz-juelich.de").one()

    assert user.name == "Doro Testaccount1"


    with flask_server.app.app_context():
        user_log_entries = sampledb.logic.user_log.get_user_log_entries(user_id)
        assert len(user_log_entries) == 2
        for user_log_entry in user_log_entries:
            assert user_log_entry.type == sampledb.models.UserLogEntryType.EDIT_USER_PREFERENCES
            assert user_log_entry.user_id == user_id
            assert user_log_entry.data == {}
    assert r.status_code == 200


def test_user_add_general_authentication_method(flask_server):
    # Try logging in with ldap-test-account
    session = requests.session()
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    assert document.find('input', {'name': 'username', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'password', 'type': 'password'}) is not None
    assert document.find('input', {'name': 'remember_me', 'type': 'checkbox'}) is not None
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': flask_server.app.config['TESTING_LDAP_LOGIN'],
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'remember_me': False,
        'csrf_token': csrf_token
    })
    assert r.status_code == 200

    url = flask_server.base_url + 'users/me/preferences'
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers['Location'].startswith(flask_server.base_url + 'users/')
    assert r.headers['Location'].endswith('/preferences')
    url = r.headers['Location']
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 200

    document = BeautifulSoup(r.content, 'html.parser')
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form

    #  add authentication_method with password is to short
    r = session.post(url, {
        'login': 'test',
        'password': 'xx',
        'authentication_method': 'O',
        'csrf_token': csrf_token,
        'add': 'Add'
    })
    assert r.status_code == 200
    assert 'The password must be of minimum 4 characters'

    #  add identically authentication_method
    r = session.post(url, {
        'login': flask_server.app.config['TESTING_LDAP_LOGIN'],
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'authentication_method': 'L',
        'csrf_token': csrf_token,
        'add': 'Add'
    })
    assert r.status_code == 200
    assert 'Ldap-Account already exists' in r.content.decode('utf-8')

    #  add wrong ldap-account , password wrong
    r = session.post(url, {
        'login': 'henkel',
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'authentication_method': 'L',
        'csrf_token': csrf_token,
        'add': 'Add'
    })
    assert r.status_code == 200
    assert 'Ldap login or password wrong' in r.content.decode('utf-8')

    #  add authentication-email without email
    r = session.post(url, {
        'login': 'web.de',
        'password': 'xxxx',
        'authentication_method': 'E',
        'csrf_token': csrf_token,
        'add': 'Add'
    })
    assert r.status_code == 200
    assert 'Login must be an email if the authentication_method is email'

    #  add authentication-method other
    r = session.post(url, {
        'login': 'xxx',
        'password': 'xxxx',
        'authentication_method': 'O',
        'csrf_token': csrf_token,
        'add': 'Add'
    })
    assert r.status_code == 200
    # Check if authentication-method add to db
    with flask_server.app.app_context():
        assert len(sampledb.models.Authentication.query.all()) == 2


def test_user_add_email_authentication_method(flask_server):
    # Try logging in with ldap-test-account
    session = requests.session()
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    assert document.find('input', {'name': 'username', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'password', 'type': 'password'}) is not None
    assert document.find('input', {'name': 'remember_me', 'type': 'checkbox'}) is not None
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': flask_server.app.config['TESTING_LDAP_LOGIN'],
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'remember_me': False,
        'csrf_token': csrf_token
    })
    assert r.status_code == 200

    url = flask_server.base_url + 'users/me/preferences'
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers['Location'].startswith(flask_server.base_url + 'users/')
    assert r.headers['Location'].endswith('/preferences')
    url = r.headers['Location']

    r = session.get(url, allow_redirects=False)
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')

    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form

    #  add valid email authentication-method
    with sampledb.mail.record_messages() as outbox:
        r = session.post(url, {
            'login': 'd.henkel@fz-juelich.de',
            'password': 'abc.123',
            'authentication_method': 'E',
            'csrf_token': csrf_token,
            'add': 'Add'
        })
    assert r.status_code == 200

    # Check if an confirmation mail was sent
    assert len(outbox) == 1
    assert 'd.henkel@fz-juelich.de' in outbox[0].recipients
    message = outbox[0].html
    assert 'Welcome to iffsample!' in message

    # Check if authentication-method add to db
    with flask_server.app.app_context():
        assert len(sampledb.models.Authentication.query.all()) == 2

    # Create new session
    session = requests.session()

    assert session.get(flask_server.base_url + 'users/me/loginstatus').json() is False
    # initially, the a link to the sign in page will be displayed
    r = session.get(flask_server.base_url)
    assert r.status_code == 200
    assert '/users/me/sign_in' in r.content.decode('utf-8')
    # Try to login
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': 'd.henkel@fz-juelich.de',
        'password': 'abc.123',
        'remember_me': False,
        'csrf_token': csrf_token
    })
    assert r.status_code == 200
    # expect False, user is not confirmed
    assert session.get(flask_server.base_url + 'users/me/loginstatus').json() is False

    # Get the confirmation url from the mail and open it
    confirmation_url = flask_server.base_url + message.split(flask_server.base_url)[1].split('"')[0]
    assert confirmation_url.startswith(flask_server.base_url + 'users/confirm-email')
    r = session.get(confirmation_url)
    assert r.status_code == 200

    assert session.get(flask_server.base_url + 'users/me/loginstatus').json() is False
    # initially, the a link to the sign in page will be displayed
    r = session.get(flask_server.base_url)
    assert r.status_code == 200
    assert '/users/me/sign_in' in r.content.decode('utf-8')
    # Try to login
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': 'd.henkel@fz-juelich.de',
        'password': 'abc.123',
        'remember_me': False,
        'csrf_token': csrf_token
    })
    assert r.status_code == 200
    # expect True, user is confirmed
    assert session.get(flask_server.base_url + 'users/me/loginstatus').json() is True


def test_user_remove_authentication_method(flask_server):
    # Try logging in with ldap-test-account
    session = requests.session()
    r = session.get(flask_server.base_url + 'users/me/sign_in')
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')
    assert document.find('input', {'name': 'username', 'type': 'text'}) is not None
    assert document.find('input', {'name': 'password', 'type': 'password'}) is not None
    assert document.find('input', {'name': 'remember_me', 'type': 'checkbox'}) is not None
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form
    r = session.post(flask_server.base_url + 'users/me/sign_in', {
        'username': flask_server.app.config['TESTING_LDAP_LOGIN'],
        'password': flask_server.app.config['TESTING_LDAP_PW'],
        'remember_me': False,
        'csrf_token': csrf_token
    })
    assert r.status_code == 200

    url = flask_server.base_url + 'users/me/preferences'
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers['Location'].startswith(flask_server.base_url + 'users/')
    assert r.headers['Location'].endswith('/preferences')
    url = r.headers['Location']

    r = session.get(url, allow_redirects=False)
    assert r.status_code == 200
    document = BeautifulSoup(r.content, 'html.parser')

    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form

    #  delete  authentication-method, only one exists
    r = session.post(url, {
        'id': '1',
        'csrf_token': csrf_token,
        'remove': 'Remove'
    })
    assert r.status_code == 200
    assert 'one authentication-method must at least exist, delete not possible' in r.content.decode('utf-8')

    url = flask_server.base_url + 'users/me/preferences'
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 302
    assert r.headers['Location'].startswith(flask_server.base_url + 'users/')
    assert r.headers['Location'].endswith('/preferences')
    url = r.headers['Location']
    r = session.get(url, allow_redirects=False)
    assert r.status_code == 200

    document = BeautifulSoup(r.content, 'html.parser')
    # it also contains a hidden CSRF token
    assert document.find('input', {'name': 'csrf_token', 'type': 'hidden'}) is not None
    csrf_token = document.find('input', {'name': 'csrf_token'})['value']
    # submit the form

    #  add authentication_method for testing remove
    r = session.post(url, {
        'login': 'test',
        'password': 'xxxxx',
        'authentication_method': 'O',
        'csrf_token': csrf_token,
        'add': 'Add'
    })
    assert r.status_code == 200

    # Check if authentication-method add to db
    with flask_server.app.app_context():
        assert len(sampledb.models.Authentication.query.all()) == 2

    #  delete  authentication-method, only one exists
    r = session.post(url, {
        'id': '2',
        'csrf_token': csrf_token,
        'remove': 'Remove'
    })
    assert r.status_code == 200

    # Check if authentication-method remove from db
    with flask_server.app.app_context():
        assert len(sampledb.models.Authentication.query.all()) == 1

