from flask import Flask
app = Flask(__name__,instance_relative_config=True)
from flask_wtf.csrf import CSRFProtect
app.config.from_pyfile("config.py")
from flask_sqlalchemy import SQLAlchemy
db =SQLAlchemy(app)
csrf = CSRFProtect(app)
from pkg import mymodels
from pkg.myroutes  import admin_routes,user_routes