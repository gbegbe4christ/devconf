from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TextAreaField
from wtforms.validators import DataRequired,Length

class ProductForm(FlaskForm):
   item_name = StringField("Product Name",validators=[DataRequired()])
   item_price = StringField("Product Price",validators=[Length(min=4)])
   submit = SubmitField("Add Product")

class PostForm(FlaskForm):
   title = StringField("Post Title ",validators=[DataRequired()])
   content = TextAreaField("Content ",validators=[DataRequired(),Length(min=10)])
   submit = SubmitField("Post")