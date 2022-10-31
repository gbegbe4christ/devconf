from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
myapp = Flask(__name__,instance_relative_config=True)

myapp.config.from_pyfile("config.py")

db = SQLAlchemy(myapp)

csrf = CSRFProtect(myapp)
from app_pkg import mymodels

from app_pkg.myroutes import user_routes,admin_routes

