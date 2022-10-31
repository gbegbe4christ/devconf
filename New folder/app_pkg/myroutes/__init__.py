from flask import Flask
from flask_sqlalchemy import SQLAlchemy

myapp = Flask(__name__,instance_relative_config=True)

myapp.config.from_pyfile("config.py")

db = SQLAlchemy(myapp)

from app_pkg.myroutes import user_routes
