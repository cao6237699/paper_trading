# encoding=UTF-8

from flask import render_template
from .views import blue

@blue.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@blue.app_errorhandler(500)
def interal_server_error(e):
    return render_template('500.html'),500