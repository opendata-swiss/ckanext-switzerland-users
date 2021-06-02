# Ckan extension to allow for a user search by organization amd role

This ckan extensions adds a user search and user display by organization and roles.

## Prerequisites

- ckanext-hierarchy needs to be installed
- only two levels of hierarchy are allowed for organization

## Purpose

- adds a custom user_list, displaying organizations and roles that a user is involved in
- adds a user search form that allows to search for users by organization and role

## Update translations

To generate an updated ckanext-switzerland_users.pot file inside the Docker
container, use the following commands:

    docker-compose exec ckan bash
    source /usr/lib/ckan/venv/bin/activate
    cd /usr/lib/ckanext/ckanext-switzerland_users/
    python setup.py extract_messages

Copy any new strings that you want to translate from the new
`ckanext-switzerland_users.pot` into the `ckanext-switzerland_users.po` file for each
language, and add the translations.

After that compile the po files into mo files:

    python setup.py compile_catalog

Log out of the ckan container (ctrl+D) and restart it for the new translations
to be used:

    docker-compose restart ckan
