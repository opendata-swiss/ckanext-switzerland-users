# coding=UTF-8

import ckan.logic as logic
import ckan.plugins.toolkit as tk


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
