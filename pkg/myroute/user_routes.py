import os,random,string,requests
from flask import render_template,request,redirect,flash,make_response,session,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from pkg import app,db
from pkg.mymodels import User,State,Products,Purchases,Posts,Lga,Comment
from pkg.forms import MakeForm

@app.route('/')
def homepage(): 
    response = requests.get('http://127.0.0.1:5000/api/v1/listall')
    """Convert the response object above to JSON"""
    rsp = response.json()
    return render_template('user/home.html', rsp=rsp)

@app.route('/signup',methods=['POST', 'GET'])
def user_signup():
    if request.method == 'GET':
        return render_template('user/regform.html')
    else:
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        enc_pwd = generate_password_hash(pwd)
        # Insert into the table
        u = User(user_fname=fname,user_email=email,user_lname=lname,user_pass=enc_pwd)
        db.session.add(u)
        db.session.commit()
        # id = u.user_id-
        flash('Thank you for joining')
        return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def user_login():
    if request.method == 'GET':
        return render_template('user/user_login.html')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        record = db.session.query(User).filter(User.user_email == username).first()
        if record and check_password_hash(record.user_pass,password):
            userId = record.user_id
            session['loggedin'] = userId
            # username = session['username']
            return redirect('/userdash')
        else:
            msg = 'Login Failed'
            flash(msg)
            return redirect('/login')

# we import csrf and use @csrf.exempt after app route to exempt some routes

@app.route('/userdash')
def userdash():
    loggedin = session.get('loggedin')
    if loggedin != None:
        data = db.session.query(User).filter(User.user_id == loggedin).first()
        return render_template('user/user_dashboard.html',data=data)
    else:
        return redirect('/')

@app.route('/user_logout')
def user_logout():
    if session.get('loggedin') != None:
        session.pop('loggedin')
    return redirect('/')

@app.route('/update_profile/', methods=['POST','GET'])
def update_profile():
    if session.get('loggedin') != None:
        if request.method=="GET":
            deets = db.session.query(User).filter(User.user_id == session.get('loggedin')).first()
            states = db.session.query(State).all()
            return render_template('user/profile_update.html',deets=deets,states=states)
        else:
            # retrieve form data and uodate here
            file = request.files['pix']
            allowed = ['.jpg','.png','.jpeg']
            newname = ''
            if file.filename != '':
                originalfilename = file.filename
                filename,ext =os.path.splitext(originalfilename)
                # checking if extension is allowed
                if ext.lower() in allowed:
                    # generating a random name
                    xcharacterlist = random.sample(string.ascii_letters,12)
                    newname = ''.join(xcharacterlist) + ext 
                    file.save('pkg/static/uploads/'+newname)
                else:
                    flash('Extension not found')

            fname = request.form.get('fname')
            lname = request.form.get('lname')
            state = request.form.get('state')
            phone = request.form.get('phone')

            userobj = db.session.query(User).get(session.get('loggedin'))
            userobj.user_fname = fname
            userobj.user_image = newname
            userobj.user_lname = lname
            userobj.user_state = state
            userobj.user_phone = phone

            db.session.commit()
            flash('User successfully updated')
            return redirect('/update_profile')
    else:
        return redirect("/login")

@app.route('/store',methods=['POST','GET'])
def store():
    if session.get('loggedin') != None:
        if request.method =="GET":
            prods=Products.query.all()
            loggedin = session.get('loggedin')
            return render_template('user/store.html',prods=prods,loggedin=loggedin)
        else:
            '''Retrieve form data, and insert into purchases table, 
            but hold on!, remember to delete the previously entered purchases'''
            userid = session.get('loggedin')
            
            '''Generate a transation ref no and keep it in a session variable'''
            refno = int(random.random() * 1000000000)
            session['tref'] = refno

            '''Insert into Transaction Table'''
            trans = Transaction(trx_user=userid,trx_refno=refno,trx_status='pending',trx_method='cash')            
            db.session.add(trans) 
            db.session.commit()
            '''Get the id from transaction table and insert into purchases table'''
            id = trans.trx_id
            
            '''Before you insert new purchases, delete existing ones first'''
            db.session.execute(f'delete from purchases where pur_userid="{userid}"')
            db.session.commit()            

            productid = request.form.getlist('productid') #[1,2,3]
            total_amt = 0
            for p in productid:
                pobj = Purchases(pur_userid=userid,pur_productid=p,pur_trxid=id)
                db.session.add(pobj)
                db.session.commit() 
                product_amt = pobj.proddeets.product_price
                total_amt = total_amt+ product_amt

            '''UPDATE the total amount on transaction table with product_amt'''

            trans.trx_totalamt = total_amt
            db.session.commit()
           
            return redirect('/confirm') 
    else:
        return redirect('/login')
@app.route('/confirm')
def confirm_purchases():
    loggedin = session.get('loggedin')
    if loggedin != None:
        """Retrieve all the things this user have selected from purchases table save it in a variable and then send it to the template"""
        data = db.session.query(Purchases).filter(Purchases.pur_userid == loggedin).all()
        return render_template('user/confirm_purchases.html',data=data)
    else:
        return redirect('/login')

@app.route('/conversation')
def conversation():
    if session.get('loggedin'):
        '''Write a query that fetches everything from the posts table'''
        # allpost = db.session.query(Posts).all()
        allposts = Posts.query.order_by(Posts.post_date.desc()).all()
        return render_template('user/conversation.html',allposts=allposts)
    else:
        return redirect('/login')

@app.route('/makepost',methods=['POST', 'GET'])
def makepost():
    if session.get('loggedin'):
        mak = MakeForm()
        if request.method == 'GET':
            return render_template('user/newpost.html',mak=mak)
        else:
            if mak.validate_on_submit():
                title = mak.post_title.data
                content = mak.post_content.data
                x = Posts(post_title=title, post_content=content,post_userid = session.get('loggedin') )
                db.session.add(x)
                db.session.commit()
                if x.post_id:
                    flash('Posted Successfully')
                    return redirect('/conversation')
                else:
                    flash('Oops Try Again')
                    return redirect('/makepost')
            else:
                return render_template('user/newpost.html',mak=mak)
    else:
        return redirect('/login')

@app.route('/getlga')
def getlga():
    stateid = request.args.get('stateid')
    opt = ''
    records = db.session.query(Lga).filter(Lga.state_id==stateid).all()
    for r in records:
        opt = opt + f"<option>{r.lga_name}</option>" 
    return opt

@app.route('/details/<pid>', methods=['POST','GET'])
def details(pid):
    if request.method =='GET':
        deets = db.session.query(Posts).get_or_404(pid)
        return render_template('user/post_details.html',deets=deets)
    else:
        com =request.form.get('comment')
        userid = session.get('loggedin')
        comment = Comment(comment_by=userid,comment_content=com,comment_postid=pid)
        db.session.add(comment)
        db.session.commit()
        
        data2return ={"madeby":comment.commentuser.user_fname,"comment":com}
        '''Convert to Json'''
        # data2return=(comment.commentuser.user_fname,com)
        data_json = jsonify(data2return)
        
        '''If you are returning the data as a string'''
        #return com
        return data_json

@app.route('/ajax/check_email_form')
def check_email_form():
    return render_template('check_email.html')

@app.route('/ajax/check_email',methods=['POST'])
def check_email():
    useremail = request.form.get('email')
    row = db.session.query(User).filter(User.user_email==useremail).first()
    if row:
        return 'Email Adress Exist'
    else:
        return 'Email Availabe'




@app.route('/paystack_response')
def
    
