'''routes.py'''
import os,random,string,requests,json
from flask import jsonify, render_template,abort,request,redirect,flash,url_for,make_response,session

from werkzeug.security import generate_password_hash, check_password_hash

from pkg import app,db,csrf

from pkg.mymodels import Purchases, Transaction, User,State,Products,Posts,Lga,Comment

from pkg.forms import PostForm


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
    """The button here takes them to Paystack"""
    userid = session.get('loggedin')
    transaction_ref = session.get('tref')
    if userid !=None:
        '''Retrieve all the things this user has selected from Purchases table
        save it in a variable and Then send it to the template'''        
        data = db.session.query(Purchases).join(Transaction).filter(Transaction.trx_refno==transaction_ref).all()       
        return render_template('user/confirm_purchases.html',data=data)
    else:
        return redirect('/login')


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