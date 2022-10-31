import os,string,random
import requests,json
from xml.etree.ElementTree import Comment
from flask import Flask,render_template,redirect,flash,request,session
from werkzeug.security import generate_password_hash,check_password_hash
from pkg import app,db,csrf
from pkg.forms import PostForm
from pkg.mymodels import Purchases, User,Products,State,Posts,Lga,Transaction


 


@app.route('/')
def home():
    response = requests.get("http://127.0.0.1:8082/api/v1/listall")
    rsp = response.json()
    return render_template('user/home.html',rsp=rsp)



@app.route('/paystack_step1',methods=['POST'])
def paystack():
    '''We connect to paystack here to create the payment page where user will enter their card details'''

    userid = session.get('loggedin')
    if userid != None:
        url = "https://api.paystack.co/transaction/initialize"
        '''Retrieve the user's email address, amount in kobo , refno '''
        userdeets = User.query.get(userid)
        deets = Transaction.query.filter(Transaction.trx_refno==session.get('tref')).first()
        '''Construct the json we are sending to PAYSTACK API'''
        data = {"email":userdeets.user_email,"amount":deets.trx_totalamt*100, "reference":deets.trx_refno}
        '''SET the authorization '''
        headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_3c5244cfb8965dd000f07a4cfa97185aab2e88d5"}

        response = requests.post(url, headers=headers, data=json.dumps(data))
        rspjson = json.loads(response.text) 
        if rspjson.get('status') == True:
            authurl = rspjson['data']['authorization_url']
            return redirect(authurl)
        else:
            return "Please try again"
    else:
        return redirect('/login')



@app.route('/paystack_reponse')
def paystack_response():
    '''This is the callback_url we set in our paystack dashboard for paystack to send us response'''
    userid = session.get('loggedin')
    if userid != None:
        refno = session.get('tref')

        headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_3c5244cfb8965dd000f07a4cfa97185aab2e88d5"}

        response = requests.get(f"https://api.paystack.co/transaction/verify/{refno}",headers=headers)
               
        '''Pick the JSON within the response object above '''
        rspjson = response.json()
        '''UPDATE YOUR TABLES. THE END''' 
        if rspjson['data']['status'] =='success':
            amt = rspjson['data']['amount']
            ipaddress = rspjson['data']['ip_address']
            t = Transaction.query.filter(Transaction.trx_refno==refno).first()
            t.trx_status = 'paid'
            db.session.add(t)
            db.session.commit()
            return "Payment Was Successful"  #update database and redirect them to the feedback page
        else:
            t = Transaction.query.filter(Transaction.trx_refno==refno).first()
            t.trx_status = 'failed'
            db.session.add(t)
            db.session.commit()
            return "Payment Failed" 
    else:
        return redirect('/login')

'''paystack......................................................................'''



@app.route('/userlayout')
def layout():
    return render_template('user/layout.html')


@app.route('/store',methods=['POST','GET'])
def store():
    '''THIS ROUTE DISPLAYS EVERYTHING ON THE Products Table for the User to Select Items of interest, The user submits to the same route via POST Where the items are inserted into Purchases and Transaction Table respectively. 
    After insertion, we redirect the user to /confirm where they are shown what they have just selected'''

    if session.get('loggedin') != None:
        if request.method =="GET":
            prods=Products.query.all()
            loggedin = session.get('loggedin')
            return render_template('user/store.html',prods=prods,loggedin=loggedin)
        else:
            '''Retrieve form data, and insert into purchases table'''
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
           
            productid = request.form.getlist('productid') #[1,2,3]
            total_amt = 0
            for p in productid:
                pobj = Purchases(pur_userid=userid,pur_product_id=p,pur_trxid=id)
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



@app.route('/userdash')
def user_dash():
    loggedin=session.get('loggedin')
    if loggedin !=None:
        data = db.session.query(User).filter(User.user_id==loggedin).first()
        return render_template('user/user_dashboard.html',data=data)
    else:
        return redirect('/')

@app.route('/signup',methods=['POST','GET'])

def user_signup():
    if request.method== "GET":
        return render_template('user/signup.html')

    else:
        fname =request.form.get('fname')
        lname =request.form.get('lname')
        email =request.form.get('email')
        pwd =request.form.get('pwd')
        en_pwd = generate_password_hash(pwd)

        u = User(user_email=email,user_fname=fname, user_lname=lname,user_pass=pwd)
        db.session.add(u)
        db.session.commit()
        id = u.user_id
        #flash("thank you joining ")

        return redirect('/login')


@app.route('/login',methods=['POST','GET'])

def login():
    if request.method== "GET":
        return render_template('user/user_login.html')
 
    else:
    
        username  = request.form.get('username')
        password  = request.form.get('password')
        
        record = db.session.query(User).filter(User.user_email==username,User.user_pass==password).first()
        if record:
            userID = record.user_id
            session['loggedin'] = userID
            return redirect('/userlayout')

        # if record and check_password_hash(record.user_pass,password):
        #     userID = record.user_id
        #     session['loggedin'] = userID
        #     return userID#redirect('/userlayout')

        else:
            flash('loggin failed')
            return redirect('/login')

@app.route('/user_logout')
def user_logout():
    if session.get('loggedin') !=None:
        session.pop('loggedin')
        return redirect('/login')




@app.route('/confirm')
def confirm_purchases():
    """The button here takes them to Paystack"""
    userid = session.get('loggedin')
    transaction_ref = session.get('tref')
    if userid !=None:
        '''Retrieve all the things this user has selected from Purchases table
        save it in a variable and Then send it to the template'''        
        data = db.session.query(Purchases).join(Transaction).filter(Transaction.trx_refno==transaction_ref).all()       
        return render_template('user/confirm.html',data=data)
    else:
        return redirect('/login')



@app.route('/update-profile',methods=['POST','GET'])
def update():
    if session.get('loggedin')!=None:
        if request.method=="GET":

            deets = db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
            states = db.session.query(State).all()
            return render_template('user/profile_update.html',deets=deets,states=states)

        else:
            fileobj = request.files['pix']

            allowed=['.jpg','png','jpeg']
            newfilename=''
            if fileobj.filename!='':
                original_name = fileobj.filename
                filename,ext = os.path.splitext(original_name)
                if ext.lower() in allowed:
                    xter_list = random.sample(string.ascii_letters,12)
                    newfilename = ''.join(xter_list)+ext
                    fileobj.save('pkg/static/upload/'+newfilename)

            fname =request.form.get('fname')
            lname =request.form.get('lname')
            state =request.form.get('state')
            phone =request.form.get('phone')
            userobj =db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
            userobj.user_fname=fname
            userobj.user_lname=lname
            userobj.user_state=state
            userobj.user_phone=phone
            fileobj.user_image =newfilename
            db.session.commit()
            flash("update has been successfully")
            return redirect('/update-profile')
    else:
        return redirect('/userdash')
    
    
@app.route('/conversation') 
def conversation():
    if session.get('loggedin'):
        data = db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
        allposts = Posts.query.all()
        return render_template('user/conversations.html',allposts=allposts,data=data) 

    else:
        return redirect('/login') 



@app.route('/makepost',methods=['GET','POST'])  
def makepost():
    if session.get('loggedin'):
        data = db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
        postform = PostForm()
        if request.method=="GET":

            return render_template('user/newpost.html',postform=postform,data=data)

        else:
            if postform.validate_on_submit:
                userid=session.get('loggedin')
                title =request.form.get('title')
                content =postform.content.data
                newpost =Posts(post_title=title,post_content=content,post_userid=userid)
                db.session.add(newpost)
                db.session.commit()
                if newpost.post_id:
                    flash("post sucessfully")
                return redirect('/conversation')
            else:
                 return render_template('user/newpost.html',postform=postform,data=data)

    else:
        return redirect('/login')

@app.route('/getlga')
def getlga():
    stateid = request.args.get('stateid')
    rows = db.session.query(Lga).filter(Lga.state_id==stateid).all()
    opt=''
    for r in rows:
        opt = opt + f"<option>{r.lga_name}</option>"
    return  opt


@app.route('/ajax/check_email')
def check_email_form():
    return render_template('user/check.html')


@app.route('/ajax/check_email',methods=["POST"])
def check_email():
    useremail = request.form.get('email')
    row = db.session.query(User).filter(User.user_email==useremail).first()
    if row:
        return "Email adress is use already"

    else:
        return "email is available"


@app.route('/details/<pid>',methods=["POST","GET"])
def details(pid):
    if request.method  =="GET":

        data = db.session.query(User).filter(User.user_id==session.get('loggedin')).first()
        deets =db.session.query(Posts).get_or_404(pid)

        return render_template('user/post_details.html',data=data,deets=deets)

    else:
        
        com =request.form.get('comment')
        userid = session.get('loggedin')
        comment = Comment(comment_by=userid,comment_content=com,comment_postid=pid)
        
        db.session.add(comment)
        db.session.commit()
        return com




