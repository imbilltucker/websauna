"""Support for reading Pyramid configuration files and having rollbacked transactions in tests.

https://gist.github.com/inklesspen/4504383
"""


import os

import pyramid.testing

import pytest
import transaction


from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from pyramid_web20 import Initializer
from pyramid_web20.models import DBSession

#: Make sure py.test picks this up
from pyramid_web20.tests.functional import web_server  # noqa


@pytest.fixture(scope='session')
def ini_settings(request):
    """Load INI settings from py.test command line."""
    if not getattr(request.config.option, "ini", None):
        raise RuntimeError("You need to give --ini test.ini command line option to py.test to find our test settings")

    config_uri = os.path.abspath(request.config.option.ini)
    setup_logging(config_uri)
    config = get_appsettings(config_uri)

    return config


@pytest.fixture(scope='session')
def init(request, ini_settings):
    """Initialize Pyramid web 2.0 using test settings"""
    if not getattr(request.config.option, "ini", None):
        raise RuntimeError("You need to give --ini test.ini command line option to py.test to find our test settings")

    init = Initializer(ini_settings)
    init.run(ini_settings)
    return init


@pytest.fixture(scope='function')
def test_case_ini_settings(request):
    """Pass INI settings to a test class as self.config."""

    if not getattr(request.config.option, "ini", None):
        raise RuntimeError("You need to give --ini test.ini command line option to py.test to find our test settings")

    config_uri = os.path.abspath(request.config.option.ini)
    setup_logging(config_uri)
    config = get_appsettings(config_uri)

    request.instance.config = config

    return config


@pytest.fixture(scope='session')
def sqlengine(request, ini_settings):
    engine = engine_from_config(ini_settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    # Make sure we don't have any old data left from the last run
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    def teardown():
        # There might be open transactions in the database. They will block DROP ALL and thus the tests would end up in a deadlock. Thus, we clean up all connections we know about.
        DBSession.close()
        Base.metadata.drop_all()

    request.addfinalizer(teardown)
    return engine


@pytest.fixture()
def dbtransaction(request, sqlengine):
    """Test runs within a single db transaction.

    The transaction is rolled back at the end of the test.
    """
    connection = sqlengine.connect()
    transaction = connection.begin()
    DBSession.configure(bind=connection)

    def teardown():
        connection.close()
        DBSession.remove()

    request.addfinalizer(teardown)

    return connection


@pytest.fixture()
def user_dbsession(request, ini_settings):
    """Get a database session where we have initialized user models.

    Tables are purged after the run.
    """

    from pyramid_web20 import defaultmodels

    transaction.begin()

    engine = engine_from_config(ini_settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    # Make sure we don't have any old data left from the last run
    defaultmodels.Base.metadata.drop_all(engine)
    defaultmodels.Base.metadata.create_all(engine)

    def teardown():
        # There might be open transactions in the database. They will block DROP ALL and thus the tests would end up in a deadlock. Thus, we clean up all connections we know about.
        DBSession.close()
        defaultmodels.Base.metadata.drop_all(engine)
        transaction.abort()

    request.addfinalizer(teardown)

    return DBSession


@pytest.fixture()
def http_request(request):
    """Dummy HTTP request for testing.

    For spoofing link generation, routing, etc.
    """
    request = pyramid.testing.DummyRequest()
    return request


def pytest_addoption(parser):
    parser.addoption("--ini", action="store", metavar="INI_FILE", help="use INI_FILE to configure SQLAlchemy")
