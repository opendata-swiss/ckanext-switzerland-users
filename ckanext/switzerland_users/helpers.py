# coding=UTF-8

from webhelpers.html import tags
from ckan.lib.helpers import url_for
import ckan.logic as logic
from ckanext.switzerland.helpers.frontend_helpers import get_localized_value_for_display  # noqa


def ogdch_list_user(user, maxlength=0):
    """display user in user list"""
    user_obj = logic.get_action(u'user_show')(
        {}, {u'id': user})
    user_organization_roles = []
    if not user_obj.get('sysadmin'):
        userroles = logic.get_action('ogdch_get_roles_for_user')({}, {u'id': user_obj['id']})  # noqa
        for role in userroles:
            user_organization_roles.append(tags.link_to(
                role.get('role').capitalize() + ": " + get_localized_value_for_display(role.get('organization_title')),  # noqa
                url_for('organization_read', action='read', id=role.get('organization'))))  # noqa
    display_email = user_obj.get('email', '-')
    if not display_email:
        display_email = ''
    return {
        'link': tags.link_to(
            user_obj['name'],
            url_for('user.read', id=user_obj['id'])),
        'email': display_email,
        'userroles': user_organization_roles,
    }
