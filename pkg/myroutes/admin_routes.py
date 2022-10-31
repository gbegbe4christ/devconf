'''routes.py'''

from flask import render_template,abort,request,redirect,flash,url_for,make_response,session

from pkg import app,db
from pkg.mymodels import Admin,User,Products,State
from pkg.forms import ProductForm


@app.route('/admin/')
def admin_home():
    adminuser = session.get('adminlogged_in')
    if adminuser: 
       return 'New Product Form will be here'
    else:
        return redirect('/admin/dashboard')





@app.route('/admin/new-product', methods=['GET',"POST"])
def new_product():
    adminuser = session.get('adminlogged_in')
    if adminuser: 
        frm = ProductForm()
        if request.method =='GET':
            return render_template('admin/new_product.html',frm=frm)
        else:
            if frm.validate_on_submit():
                productname = request.form.get('item_name')
                productprice = frm.item_price.data
                prod = Products(product_name=productname,product_price=productprice)
                db.session.add(prod)
                db.session.commit()
                
                return  redirect('/admin/product')
            else:
                return render_template('admin/new_product.html',frm=frm)
    else:
        
        return redirect('/admin/login')




@app.route('/admin/product')
def admin_addproduct():
    adminuser = session.get('adminlogged_in')
    if adminuser: 
        all_products = db.session.query(Products).all()
        return render_template('admin/product.html', all_products=all_products)
    else:
        return redirect('/admin/login')


@app.route('/admin/login', methods=['POST','GET'])
def admin_login():
    if request.method =='GET':
        return render_template('admin/admin_login.html')
    else:#retrieve the data        
        username = request.form.get('username')
        pwd = request.form.get('password')#Run a query        
        data = db.session.query(Admin).filter(Admin.admin_username==username).filter(Admin.admin_password==pwd).first()
        if data:
            session['adminlogged_in'] = data.admin_id
            '''Redirect to the admin dashboard'''
            return redirect('/admin/dashboard')
        else:
            flash('Invcalid Credentials')
            return redirect('/admin/login')

@app.route('/admin')
def admin_main():
    return render_template('admin/admin_dashboard.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    '''Check if logged in..'''
    adminuser = session.get('adminlogged_in')
    if adminuser:
        total_reg = db.session.query(User).count()
        return render_template('admin/admin_dashboard.html',total_reg=total_reg)
    else:
        return redirect('/admin/login')
@app.route('/admin/logout')
def admin_logout():
    if session.get('adminlogged_in'):
        session.pop('adminlogged_in')
    return redirect('/admin/login')


@app.route('/admin/delete/<id>')
def delete_user(id):
    if session.get('adminlogged_in'):
        user =db.session.query(User).get(id)
        db.session.delete(user)
        db.session.commit()
        flash("user deleted ")
        return redirect('/admin/registration')

    else:
        return redirect('/admin/login')


@app.route('/admin/registrations')
def admin_register():
    adminuser = session.get('adminlogged_in')
    if adminuser:
        regs = User.query.join(State,User.user_state==State.state_id).add_columns(State).all()
        #regs1=db.session.query(User,State).join(State,User.user_state==State.state_id).all()
        return render_template('admin/registration.html',regs=regs)

    else:
        return redirect('/admin/login')

