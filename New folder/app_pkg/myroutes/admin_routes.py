from flask import Flask,render_template,abort,request,redirect,flash,make_response,session
from app_pkg import myapp,db
from app_pkg.forms import ProductForm
from app_pkg.mymodels import Admin,User,Products,State


@myapp.route("/")
def home():
   return render_template("home.html")

@myapp.route("/admin/login/",methods=['GET','POST'])
def admin_login():
   if request.method=="GET":
      return render_template("admin/admin_login.html")
   else:
      username= request.form.get("username")
      pwd = request.form.get("password")
      record= db.session.query(Admin).filter(Admin.admin_username==username).filter(Admin.admin_password==pwd).first()

      if record:
         session['loggedinadmin'] = record.admin_id
         return redirect("/admin/dashboard/")
      else:
         flash("Invalid credentials, please try again")
         return redirect("/")

@myapp.route("/admin/dashboard/")
def admin_dashboard():
   admin_user=session.get("loggedinadmin")

   if admin_user:
      total_reg = db.session.query(User).count()
      return render_template("admin/admin_dashboard.html",total_reg=total_reg)
   else:
      return redirect("/admin/login")

@myapp.route("/admin/logout/")
def admin_logout():
   if session.get('loggedinadmin') != None:
        session.pop('loggedinadmin')
   return redirect("/")

@myapp.route("/admin/product/")
def add_product():
   admin_user=session.get("loggedinadmin")

   if admin_user:
      all_products = db.session.query(Products).all()
      return render_template("admin/products.html",all_products=all_products)
   else:
      return redirect("/admin/login")

@myapp.route("/admin/new-product/",methods=["POST",'GET'])
def new_product():
   admin_user=session.get("loggedinadmin")
   if admin_user:
      frm=ProductForm()
      if request.method=='GET':
         return render_template("admin/new_product.html",frm=frm)
      else:
         if frm.validate_on_submit():
            name = frm.item_name.data
            price = frm.item_price.data
            x = Products(product_name=name,product_price=price)
            db.session.add(x)
            db.session.commit()
            flash("Product added")
            return redirect("/admin/product/") 
         else:
            return render_template("admin/new_product.html")    
   else:
      return redirect("/admin/login")

@myapp.route("/admin/registrations/")
def all_users():
   admin_user=session.get("loggedinadmin")

   if admin_user:
      # regs = db.session.query(User,State).join(State).all()
      regs = db.session.query(User).all()
      return render_template("admin/registrations.html",regs=regs)
   else:
      return redirect("/admin/login")

@myapp.route("/admin/details/<id>/")
def user_details(id):
   admin_user=session.get("loggedinadmin")

   if admin_user:
      regs = db.session.query(User,State).join(State).filter(User.user_id==id)
      
      return render_template("admin/details.html",regs=regs,id=id)
   else:
      return redirect("/admin/login")


@myapp.route("/admin/registrations/<id>")
def delete_user(id):
   admin_user=session.get("loggedinadmin")

   if admin_user:
      deets= db.session.query(User).get(id)
      db.session.delete(deets)
      db.commit()
      return render_template("admin/registrations.html",deets=deets)
   else:
      return redirect("/admin/login")