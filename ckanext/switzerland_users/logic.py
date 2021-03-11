# coding=UTF-8

from collections import namedtuple
from ckan import authz
import ckan.plugins.toolkit as tk

Member = namedtuple('member', 'role organization')
Admin = namedtuple('admin', 'role organizations')
CAPACITY_SYSADMIN = 'sysadmin'
CAPACITY_ADMIN = 'admin'


def ogdch_get_roles_for_user(context, data_dict):
    '''
    Get list of roles that a user has in organizations
    Roles in suborganizations are only included if they differ from the
    role in the top level organization
    '''
    organizations_for_user = tk.get_action('organization_list_for_user')(context, data_dict)  # noqa
    organizations = [organization.get('name')
                     for organization in organizations_for_user]
    userroles = [{'organization': organization.get('name'),
                  'role': organization.get('capacity'),
                  'organization_title': organization.get('title')}  # noqa
                 for organization in organizations_for_user]

    organization_trees = []
    for organization in organizations:
        if not _check_organization_in_organization_trees(organization, organization_trees):  # noqa
            organization_tree = tk.get_action('group_tree_section')(
                context, {'type': 'organization', 'id': organization})  # noqa
            userroles = _check_userrole_in_organization_tree(userroles, organization_tree)  # noqa
            organization_trees.append(organization_tree)
    return userroles


def _check_organization_in_organization_trees(organization, organization_trees):  # noqa
    """checks if a organization is in an organization tree"""
    for organization_tree in organization_trees:
        if organization == organization_tree.get('name'):
            return True
        suborganisations = organization_tree.get('children')
        if organization in [suborg.get('name') for suborg in suborganisations]:  # noqa
            return True
    return False


def _check_userrole_in_organization_tree(userroles, organization_tree):
    """returns userroles that a user has in organizations:
    roles in suborganizations are only included if they differ from the role in
    the top level organization"""
    top_organization = organization_tree.get('name')
    sub_organization_tree = organization_tree.get('children')
    if not sub_organization_tree:
        return userroles
    sub_organizations = [suborg.get('name') for suborg in sub_organization_tree]  # noqa
    userrole_organizations = [role['organization'] for role in userroles]
    if top_organization not in userrole_organizations:
        return userroles
    top_role = _get_role_from_userroles_for_organization(userroles, top_organization)  # noqa
    for suborg in sub_organizations:
        if suborg in userrole_organizations:
            suborg_role = _get_role_from_userroles_for_organization(userroles, suborg)  # noqa
            if suborg_role and suborg_role == top_role:
                userroles = _remove_role_from_userroles(userroles, suborg)
    return userroles


def _get_role_from_userroles_for_organization(userroles, organization):
    """gets the role of a user in an organization in the userrole list"""
    role_in_org = [role['role'] for role in userroles if role['organization'] == organization]  # noqa
    if role_in_org:
        return role_in_org[0]
    return None


def _remove_role_from_userroles(userroles, organization):
    """remove the role from the userroles list"""
    return [role for role in userroles if role['organization'] != organization]


def ogdch_get_admin_organizations_for_user(context, data_dict):
    '''
    Get list of organization where a user is admin of
    '''
    organizations_for_user = tk.get_action('organization_list_for_user')(context, data_dict)  # noqa
    organizations_where_user_is_admin = [
        organization.get('name')
        for organization in organizations_for_user
        if organization.get('capacity') == CAPACITY_ADMIN
    ]
    return organizations_where_user_is_admin


def ogdch_get_users_with_organizations(context, data_dict):
    """get member list of all users of their memberships in organizations"""
    organization_list = tk.get_action('organization_list')(context, {})
    users_with_organizations = {}
    for organization in organization_list:
        member_list = tk.get_action('member_list')(
            {'ignore_auth': True}, {'id': organization, 'object_type': 'user'})
        for item in member_list:
            user = item[0]
            role = item[2]
            organization_member = Member(role, organization)
            if user in users_with_organizations:
                users_with_organizations[user].append(organization_member)
            else:
                users_with_organizations[user] = [organization_member]
    return users_with_organizations


def ogdch_user_list(context, data_dict):
    """custom user list for ogdch: list users that are visible to the current user
    - for sysadmins: list all users
    - for organization admins: list all users of their organizations
    """
    current_user = context.get('user')
    q = data_dict.get('q')
    q_organization = data_dict.get('organization')
    q_role = data_dict.get('role')

    user_list = tk.get_action('user_list')(context, {'q': q})  # noqa

    admin_organizations_for_user = tk.get_action('ogdch_get_admin_organizations_for_user')(context, data_dict)  # noqa
    current_user_admin_capacity = _check_admin_capacity_for_user(current_user, admin_organizations_for_user)  # noqa
    if not current_user_admin_capacity:
        return _get_current_user_details(current_user, user_list)

    user_list_with_organizations = tk.get_action('ogdch_get_users_with_organizations')(context, data_dict)  # noqa
    user_organization_dict = {user['id']: user_list_with_organizations.get(user['id'], [])  # noqa
                              for user in user_list}
    user_list_filtered = _get_filter_user_list(user_list, user_organization_dict, current_user_admin_capacity, q_organization, q_role)  # noqa
    return user_list_filtered


def _check_admin_capacity_for_user(user, admin_organizations_for_user):  # noqa
    """determine the admin capacity of the user:
    - consist of the role and the organizations he administers
    - None if he does not adminster any organizations"""
    if authz.is_sysadmin(user):
        return Admin(CAPACITY_SYSADMIN, [])
    if admin_organizations_for_user:
        return Admin(CAPACITY_ADMIN, admin_organizations_for_user)
    return None


def _get_current_user_details(current_user, user_list):
    """returns a user list that contains only the current user"""
    return [user for user in user_list if user['name'] == current_user]  # noqa


def _get_filter_user_list(user_list, user_organization_dict, current_user_admin_capacity, q_organization=None, q_role=None):  # noqa
    """filter the user list: for each user in the list a check is
    preformed whether the user is visible to the current user
    """
    filtered_user_list = []
    for user in user_list:
        user_memberships = user_organization_dict.get(user['id'], [])
        user_organizations = [role.organization for role in user_memberships]
        if _user_filter(user, user_memberships, user_organizations, current_user_admin_capacity, q_organization, q_role):  # noqa
            filtered_user_list.append(user)
    return filtered_user_list


def _user_filter(user, user_memberships, user_organizations, current_user_admin_capacity, q_organization=None, q_role=None):  # noqa
    """filters a user for his visibility to the current user
    and for his match regarding the current query"""
    if not _user_admin_match(user, user_organizations, current_user_admin_capacity):  # noqa
        return False
    organization_restriction = None
    if current_user_admin_capacity.role == CAPACITY_ADMIN:
        organization_restriction = current_user_admin_capacity.organizations
    user_memberships_adjusted = _get_memberships_for_organization_restrictions(user_memberships, organization_restriction)  # noqa
    if q_organization and not q_role:
        if not _user_organization_match(user_organizations, q_organization, organization_restriction): # noqa
            return False
    if q_role and not q_organization:
        if not _user_role_match(user, user_memberships_adjusted, q_role):
            return False
    if q_role and q_organization:
        if not _user_role_organization_match(user_memberships_adjusted, q_role, q_organization):  # noqa
            return False
    return True


def _user_admin_match(user, user_organizations, current_user_admin_capacity):
    """checks whether the user is visible to the current user"""
    if current_user_admin_capacity.role == CAPACITY_SYSADMIN:
        return True
    if not user.get('sysadmin'):
        organizations_matches = [organization for organization in user_organizations  # noqa
                                 if organization in current_user_admin_capacity.organizations]  # noqa
        if organizations_matches:
            return True
    return False


def _get_memberships_for_organization_restrictions(user_memberships, organization_restriction=None):  # noqa
    """gets a restricted list of memberships: the list is
    restricted with regards to the given organizations"""
    if not organization_restriction:
        return user_memberships
    return [member for member in user_memberships if member.organization in organization_restriction]  # noqa


def _user_organization_match(user_organizations, q_organization, organization_restriction=None):  # noqa
    """checks whether the user is a match for an organizations
    with in a given range of organizations"""
    if not organization_restriction and q_organization in user_organizations:
        return True
    if q_organization in user_organizations and q_organization in organization_restriction:  # noqa
        return True
    return False


def _user_role_match(user, user_memberships, q_role):
    """checks whether the user is a match for a role"""
    if q_role.lower() == CAPACITY_SYSADMIN.lower() and user.get('sysadmin'):
        return True
    return [member for member in user_memberships if member.role.lower() == q_role.lower()]   # noqa


def _user_role_organization_match(user_memberships, q_role, q_organization):
    """checks whether the user is a match for a given membership of a
    role in an organization"""
    return [member for member in user_memberships
            if member.role.lower() == q_role.lower() and q_organization == member.organization]  # noqa
