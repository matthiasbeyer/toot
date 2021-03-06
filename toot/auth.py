# -*- coding: utf-8 -*-

import webbrowser

from builtins import input
from getpass import getpass

from toot import api, config, DEFAULT_INSTANCE, User, App
from toot.exceptions import ApiError, ConsoleError
from toot.output import print_out


def register_app(domain):
    print_out("Looking up instance info...")
    instance = api.get_instance(domain)

    print_out("Found instance <blue>{}</blue> running Mastodon version <yellow>{}</yellow>".format(
        instance['title'], instance['version']))

    try:
        print_out("Registering application...")
        response = api.create_app(domain)
    except ApiError:
        raise ConsoleError("Registration failed.")

    base_url = 'https://' + domain

    app = App(domain, base_url, response['client_id'], response['client_secret'])
    path = config.save_app(app)
    print_out("Application tokens saved to: <green>{}</green>\n".format(path))

    return app


def create_app_interactive(instance=None):
    if not instance:
        print_out("Choose an instance [<green>{}</green>]: ".format(DEFAULT_INSTANCE), end="")
        instance = input()
        if not instance:
            instance = DEFAULT_INSTANCE

    return config.load_app(instance) or register_app(instance)


def create_user(app, email, access_token):
    user = User(app.instance, email, access_token)
    path = config.save_user(user)

    print_out("Access token saved to: <green>{}</green>".format(path))

    return user


def login_interactive(app, email=None):
    print_out("Log in to <green>{}</green>".format(app.instance))

    if email:
        print_out("Email: <green>{}</green>".format(email))

    while not email:
        email = input('Email: ')

    password = getpass('Password: ')

    try:
        print_out("Authenticating...")
        response = api.login(app, email, password)
    except ApiError:
        raise ConsoleError("Login failed")

    return create_user(app, email, response['access_token'])


BROWSER_LOGIN_EXPLANATION = """
This authentication method requires you to log into your Mastodon instance
in your browser, where you will be asked to authorize <yellow>toot</yellow> to access
your account. When you do, you will be given an <yellow>authorization code</yellow>
which you need to paste here.
"""


def login_browser_interactive(app):
    url = api.get_browser_login_url(app)

    print_out(BROWSER_LOGIN_EXPLANATION)

    print_out("This is the login URL:")
    print_out(url)
    print_out("")

    yesno = input("Open link in default browser? [Y/n]")
    if not yesno or yesno.lower() == 'y':
        webbrowser.open(url)

    authorization_code = ""
    while not authorization_code:
        authorization_code = input("Authorization code: ")

    print_out("\nRequesting access token...")
    response = api.request_access_token(app, authorization_code)

    # TODO: user email is not available in this workflow, maybe change the User
    # to store the username instead? Currently set to "unknown" since it's not
    # used anywhere.
    email = "unknown"

    return create_user(app, email, response['access_token'])
