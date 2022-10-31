from optparse import Values
from flask import render_template, abort,request,redirect,flash,url_for,make_response,session

from pkg import myapp,db


@myapp.route('/message_us')
def contact_us():
    return render_template('contact_us.html')
