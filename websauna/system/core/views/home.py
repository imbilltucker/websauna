"""Default home view for test runs."""

from pyramid.view import view_config
from websauna.system.admin.utils import get_admin


@view_config(route_name='home', renderer='core/home.html')
def home(request):
    """The default home view of Websauna.

    You should really never see this is, as this view should be only active during Websauna test run and dev server.
    """
    return {}



