# Ckan extension to allow for a user search by organization amd role

This ckan extensions adds a user search and user display by organization and roles.

## Prerequisites

- ckanext-hierarchy needs to be installed
- only two levels of hierarchy are allowed for organization

## Purpose

- adds a custom user_list, displaying organizations and roles that a user is involved in
- adds a user search form that allows to search for users by organization and role

## Update translations

To generate a new ckanext-switzerland.pot file inside the Docker container,
use the following command:

    docker-compose exec ckan bash
    source /usr/lib/ckan/venv/bin/activate
    cd /usr/lib/ckanext/ckanext-switzerland_users/
    python setup.py extract_messages

This will generate the `pot` files
Then update the `po` files with:

    python setup.py update_catalog -l de

Now the translations can be filled in. After that compile the po files into mo files:

    python setup.py compile_catalog