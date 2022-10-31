from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField
from wtforms.validators import DataRequired

class ProductForm(FlaskForm):
    item_name = StringField("product name")
    item_price = StringField("product price")
    submit = SubmitField("Submit")


class PostForm(FlaskForm):
    title=StringField("Title")
    content=TextAreaField("content")
    submit=SubmitField("Submit")