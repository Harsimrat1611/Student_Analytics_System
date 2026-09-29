from flask import session, redirect

def login_user(username):
    session['user'] = username


def logout_user():
    session.pop('user', None)


def is_logged_in():
    return 'user' in session