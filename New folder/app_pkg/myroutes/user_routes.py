import os,random,string,requests
from flask import Flask, jsonify,render_template,abort,request,redirect,flash,make_response,session

from werkzeug.security import generate_password_hash, check_password_hash
from app_pkg import myapp,db
from app_pkg.mymodels import Comments, User,State,Products,Purchases,Posts,Lga,Transaction
from app_pkg.forms import PostForm


@myapp.route("/")
def home_page():
   # response = requests.get("http://127.0.0.1:8088/api/v1/listall/")
   # rsp = response.json()
   return render_template("home.html") #rsp=rsp

@myapp.route("/user/myhome")
def user_home():
   return render_template("user/user_dashboard.html")

@myapp.route("/register/",methods=["POST","GET"])
def sign_up():
   if request.method== "GET":
      return render_template("user/user_reg.html")
   else:
      fname = request.form.get("fname")
      lname = request.form.get("lname")
      email = request.form.get("email")
      pwd = request.form.get("pwd")
      securepwd = generate_password_hash(pwd)
      u =   User(user_fname=fname,user_lname=lname,user_email=email,user_pass=securepwd)
      db.session.add(u)
      db.session.commit()
      id= u.user_id
      flash("Thank you for joining us!")
   return redirect("/login/")

@myapp.route("/login/",methods=["POST","GET"])
def user_login():
   if request.method== "GET":
      return render_template("user/user_login.html")
   else:
      username= request.form.get("username")
      pwd = request.form.get("password")
      record = db.session.query(User).filter(User.user_email==username).first()

      if check_password_hash(record.user_pass,pwd)== True:
         session['loggedin'] = record.user_id
         return redirect("/userdashboard/")
      else:
         flash("Invalid credentials, please try again")
         return redirect("/login/")

@myapp.route("/userdashboard/")
def user_dashboard():
   userid = session.get("loggedin")
   user=db.session.query(User).filter(User.user_id==userid).first()

   return render_template("user/user_dashboard.html",details=user)

@myapp.route("/logout/")
def log_out():
   if session.get("loggedin") != None:
      session.pop("loggedin")
   return redirect("/")

@myapp.route("/update-profile/",methods=["GET","POST"])
def update_profile():
   if session.get("loggedin") != None:
      if request.method == "GET":
         details= db.session.query(User).filter(User.user_id==session.get("loggedin")).first()
         states=db.session.query(State).all()
         return render_template("user/update_profile.html",details=details,states=states)
      else:
         allowed=[".jpg",".png",".jpeg"]
         fileobj = request.files['pic']
         error=[]
         userobj=db.session.query(User).get(session.get("loggedin"))
         if fileobj != "":
            original_name = fileobj.filename
            filename,ext = os.path.splitext(original_name)
            if ext.lower() in allowed:
               xlist = random.sample(string.ascii_letters,12)
               newfilename = ''.join(xlist) + ext
               image = newfilename
               fileobj.save(f'app_pkg/static/uploads/{newfilename}')
               userobj.user_image=image
               
            else:
               flash("Extension not allowed")
         else:
            flash("Please select a file")


         fname= request.form.get("fname")
         lname= request.form.get("lname")
         state= request.form.get("state")
         phone= request.form.get("phone")
         userobj.user_fname= fname
         userobj.user_lname= lname
         userobj.user_state= state
         userobj.user_phone= phone
         
         db.session.commit()
         flash("Profile successfully updated.")
         return redirect("/update-profile/")
   else:
      return redirect("/login/")

@myapp.route("/getlga/")
def getlga():
   if session.get("loggedin") != None:
      stateid = request.args.get("state")
      record = db.session.query(Lga).filter(Lga.state_id==stateid).all()
      opt = ""

      for r in record:
         opt= opt + f"<option>{r.lga_name}</option>"
      return opt
   else:
      return redirect("/login/")


@myapp.route("/store/",methods=['POST',"GET"])
def store():
   if session.get("loggedin") != None:
      if request.method =="GET":
         user=db.session.query(User).filter(User.user_id==session.get("loggedin")).first()
         loggedin = session.get('loggedin')
         all_products = Products.query.order_by(Products.product_name)
         return render_template("user/store.html",all_products=all_products,details=user,loggedin=loggedin)
      else:
         '''Retrieve form data, and insert into purchases table, 
         but hold on!, remember to delete the previously entered purchases'''
         userid = session.get('loggedin')
         
         '''Generate a transation ref no and keep it in a session variable'''
         refno = int(random.random() * 1000000000)
         session['tref'] = refno

         '''Insert into Transaction Table'''
         trans = Transaction(trx_user=userid,trx_refno=refno,trx_status='pending',trx_method='cash',trx_totalamt=0)            
         db.session.add(trans) 
         db.session.commit()
         '''Get the id from transaction table and insert into purchases table'''
         id = trans.trx_id

         userid= session.get("loggedin")
         db.session.execute(f"DELETE from purchases where purchase_user_id='{userid}'")
         db.session.commit()
         productid = request.form.getlist("productid")
         total_amt = 0
         for p in productid:
            pobj = Purchases(purchase_user_id=session.get("loggedin"),product_id=p,pur_trxid=id)
            db.session.add(pobj)
            db.session.commit()
            product_amt = pobj.productdeets.product_price
            total_amt = total_amt+ product_amt
         trans.trx_totalamt = total_amt
         db.session.commit()
         return redirect("/confirm/")
   else:
      return redirect("/login/")

@myapp.route("/confirm/",methods=["GET","POST"])
def confirm():
   if session.get("loggedin") != None:
      user=db.session.query(User).filter(User.user_id==session.get("loggedin")).first()
      data=db.session.query(Purchases).filter(Purchases.purchase_user_id==session.get("loggedin")).all()
      return render_template("user/confirm_purchase.html",details=user,product=data)
   else:
      return redirect("/login/")

@myapp.route("/conversation/")
def conversation():
   if session.get("loggedin") != None:
      user=db.session.query(User).filter(User.user_id==session.get("loggedin")).first()
      all_posts = db.session.query(Posts).order_by(Posts.post_content.desc()).all()
      return render_template("user/conversation.html",allposts=all_posts,details=user)
   else:
      return redirect("/login/")

@myapp.route("/post/<id>",methods=["GET","POST"])
def post(id):
   if session.get("loggedin") != None:
      if request.method == "GET":
         user=db.session.query(User).filter(User.user_id==session.get("loggedin")).first()
         post = db.session.query(Posts).filter(Posts.post_id==id).first()
         comments = db.session.query(Comments).filter(Comments.comment_postid==id).all()
         return render_template("user/post.html",post=post,details=user,comments=comments)
      else:
         com = request.form.get("comment")
         userid = session.get("loggedin")
         comment= Comments(comment_by=userid, comment_content=com, comment_postid=id)
         db.session.add(comment)
         db.session.commit()
         data = {"fname":comment.commentuser.user_fname, "comment":com,"lname":comment.commentuser.user_lname}
         data_json = jsonify(data)
         return data_json

   else:
      return redirect("/login/")


@myapp.route("/makepost/",methods=["GET","POST"])
def make_post():
   if session.get("loggedin") != None:
      form= PostForm()
      user=db.session.query(User).filter(User.user_id==session.get("loggedin")).first()
      if request.method== "GET":
         return render_template("user/makepost.html",details=user,form=form)
      else:
         if form.validate_on_submit():
            title = request.form.get('title')
            content = request.form.get("content")

            post = Posts(post_title=title, post_content=content,post_user_id=session.get("loggedin"))
            db.session.add(post)
            db.session.commit()
            if post.post_id:
               flash("Post Created!")
               return redirect("/conversation/")
            else:
               flash("Ooops an error occured!")
               return redirect("user/makepost/")
         else:
            return render_template("user/makepost.html",details=user,form=form)

   else:
      return redirect("/login/")

@myapp.route("/ajax/checkemail")
def check_email():
   user=db.session.query(User).filter(User.user_id==session.get("loggedin")).first()
   email = request.form.get("email")
   row = db.session.query(User).filter(User.user_email==email)
   if row:
      return render_template("check_email.html",details=user)

@myapp.route("/paystack_response/")
def paystack_response():
   return "Paystack will send us response here as JSON"