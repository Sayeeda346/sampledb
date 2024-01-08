# coding: utf-8
"""

"""

import pytest
from sampledb import config
from sampledb.logic import users, actions
import sampledb.__main__ as scripts


def test_set_up_demo(capsys):
    scripts.main([scripts.__file__, 'set_up_demo'])
    assert 'Success' in capsys.readouterr()[0]
    assert actions.get_actions()


def test_set_up_demo_one_user_exists(capsys):
    users.create_user("username", "example@example.com", users.UserType.PERSON)

    scripts.main([scripts.__file__, 'set_up_demo'])
    assert 'Success' in capsys.readouterr()[0]
    assert actions.get_actions()


def test_set_up_demo_two_users_exist(capsys):
    users.create_user("username", "example@example.com", users.UserType.PERSON)
    users.create_user("username", "example2@example.com", users.UserType.PERSON)

    with pytest.raises(SystemExit) as exc_info:
        scripts.main([scripts.__file__, 'set_up_demo'])
    assert exc_info.value != 0
    assert 'Error' in capsys.readouterr()[1]
    assert not actions.get_actions()


def test_set_up_demo_twice(capsys):
    scripts.main([scripts.__file__, 'set_up_demo'])
    assert 'Success' in capsys.readouterr()[0]
    assert actions.get_actions()

    num_actions = len(actions.get_actions())

    with pytest.raises(SystemExit) as exc_info:
        scripts.main([scripts.__file__, 'set_up_demo'])
    assert exc_info.value != 0
    assert 'Error' in capsys.readouterr()[1]
    assert len(actions.get_actions()) == num_actions


def test_set_up_demo_arguments(capsys):
    with pytest.raises(SystemExit) as exc_info:
        scripts.main([scripts.__file__, 'set_up_demo', __file__])
    assert exc_info.value != 0
    assert 'Usage' in capsys.readouterr()[0]
