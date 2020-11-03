from flask import Flask , render_template , session , redirect , request , url_for , flash 
from flask_bcrypt import Bcrypt  
from functools import wraps
import json
import razorpay
from flask_pymongo import PyMongo
import pymongo
import random 
from flask_mail import Message 
#from flask_mail import Mail
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import re 
app = Flask(__name__) 
app.secret_key = '\xec;o\x87\xb2/\xea8\x0f\xbb\xff\xb0N_P!\x90\x06U\xf471\xa1\xc4\xf2\x85\xc4\xaa\xad\xca\xa21\x82\x83\x84#k\xb5\x87s\xe1\xc2-\xba\x8bU\xdc\x0f\x9b'

app.config["MONGO_URI"] = "mongodb://localhost:27017/dvc"
app.config["DEBUG"] = app.debug
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] =  465 
app.config["MAIL_DEBUG"] = True 
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USE_TSL"] = False 
app.config["MAIL_USERNAME"] = "ogtechtest2@gmail.com"
app.config["MAIL_PASSWORD"] = "ogtech@123"
app.config["MAIL_DEFAULT_SENDER"] = "ogtechtest2@gmail.com"
app.config["MAIL_MAX_EMAILS"] = None 
app.config["MAIL_SUPPRESS_SEND "] = False
app.config["MAIL_ASCII_ATTACHMENTS"] = None


mongo = PyMongo(app)
mail = Mail(app) 
bcrypt = Bcrypt(app) 
razorpay_client = razorpay.Client(auth=("rzp_test_gkxon0rqWQ67W8", "FYPJtunTCHTAbju7ATyLxd47")) 
def login_required(f):
    @wraps(f)
    def wrap(*arg, **kwarg):
        if 'logged_in' in session:
            return(f(*arg,*kwarg))
        else:
            return(redirect('/'))   
    return(wrap)    

from user import routes 

@app.route("/")
def home(): 

    return(render_template("home.html")) 

@app.route("/sign/")
def sign():
    return(render_template("sign2.html"))
@app.route("/signup/",methods = ["GET" , "POST"]) 
def signup():
    user = {}
    print("This works fine AF")
    pattern = re.compile('[@_!#$%^&*()<>?/\|}{~:]') 
    if request.method == "POST":
        user = {
            "name": request.form.get('name'), 
            "email" : request.form.get('email') ,
            "contact": request.form.get('contact') ,
            "password" :  request.form.get('password') , 
            "cpassword" : request.form.get('cpassword') ,
            "token" : "none" 
        }
       
        if user["email"]=="":
            flash("Email cannot be empty ." , "danger")
            return(render_template("signup.html" , user = user))
        if user["name"] == "" :
            flash("Name cannot be empty ." , "danger")
            return(render_template("signup.html" , user = user))
        if not user["contact"].isnumeric() or len(user["contact"])!=10:
            flash("Please enter a valid mobile number ." , "danger")
            return(render_template("signup.html" , user = user))
        if user["password"] == "":
            flash("Password cannot be empty" , "danger")
            return(render_template("signup.html" , user = user))
        if user["password"] != user["cpassword"]:
            flash("Both the passwords should match","danger")
            return(render_template("signup.html" , user = user))
        if len(user["password"]) <8:
            flash("Password should atleast contain 8 characters ." ,"warning")
            return(render_template("signup.html" , user = user))
        if user["password"].isdigit():
            flash("The password cannot be only numeric ." , "warning")
            return(render_template("signup.html" , user = user))
        if user["password"].isalpha():
            flash('The password must contain atleast one numeric character .' , "warning")
            return(render_template("signup.html"))
        if(re.search(pattern,user["password"]) == None):
            flash("The passwotd must contain atleast one special character" , "warning")
            return(render_template("signup.html" , user = user))
        if mongo.db.users.find_one({"contact" : user["contact"]}):
            flash("This mobile number is already in use ." , "danger")
            return(render_template("signup.html" , user = user))
        if mongo.db.users.find_one({"email" : user["email"]}):
            flash("Email address already taken ." , "danger")
            return(render_template("signup.html" , user = user))
        hashed = bcrypt.generate_password_hash(user["password"]).decode("utf-8")
        user["password"] = hashed

        mongo.db.users.insert_one(user)
        flash("You have been signed up ! Please login to continue " , "success")
        return(redirect(url_for("login"))) 
    return(render_template("signup.html")) 
@app.route("/login/" , methods = ["POST" , "GET"])
def login():
    if 'logged_in' in session:
        return(redirect(url_for("dashboard")))
    if request.method == "POST":
        if request.form.get('lemail') == '':
            flash("Email cannot be empty ." , "danger")
            return(redirect(url_for("login")))
        if request.form.get('lpassword') == "":
            flash("Password cannot be empty ." , "danger")
            return(redirect(url_for("login")))

        user = mongo.db.users.find_one({"email" :request.form.get('lemail')}) 
        if user:
            if bcrypt.check_password_hash(user["password"], request.form.get("lpassword")): 
                session['logged_in'] = True 
                session['email'] = user["email"]
                session['name'] = user['name'] 
                session['contact'] = user['contact']
                if request.form.get("remember") == "on":
                    session.permanent = True 
                print(session.permanent)
                return(redirect(url_for("dashboard")))
            else:
                flash("Incorrect Password , please try again ." , "danger")
                return(redirect(url_for("login"))) 
        else:
            flash("Email address not found ." , "danger")
            return(redirect(url_for("login")))  
    return(render_template("login.html"))  
@app.route("/logout/") 
def logout():

    session.clear()
    flash("You have been logged out ", "success")
    return(redirect(url_for("home")))
@app.route("/dashboard/")
@login_required
def dashboard():
    return(render_template('user.html'))

@app.route("/forgot_password" , methods = ["POST" , "GET"])
def forgot():
    if request.method == "POST" :
        entered_user = request.form.get('forgotemail') 
        print(entered_user)
        if entered_user == "":
            return(redirect(url_for("login")))
        user = mongo.db.users.find_one({"email" : entered_user})
        if user:
            token = random.randint(11111,99999) 
            link = url_for("reset" ,token = token , _external = True) 
            message = Mail(
            to_emails= entered_user,
            from_email='ogtechtest2@gmail.com',
            subject='Sending with Twilio SendGrid is Fun',
            html_content="<h1><a href =" + link  +   ">Click Here to reset password</a></h1>")
            print(link)
            print("hello")
            try:
                sg = SendGridAPIClient('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')
                
                response = sg.send(message)
                mongo.db.users.update_one({"email" : entered_user},{"$set": {"token": token }}) 
                print(response.status_code)
                print(response.body)
                print(response.headers)
                flash("We've sent you an email . Please check your inbox to continue " , "success")
                return(redirect(url_for("login")))
            except Exception as e:
                print("Exception : " , e)
                flash("Due to unknown reasons , the email could not be sent . Please try again . ", "warning")
                return(redirect(url_for("login")))            
            
        else:
            flash("This email address is not registered with us ." , "danger")
            return(redirect(url_for("login")))
        print(entered_user)
         
    return(render_template("forgot.html"))

@app.route("/resetpassword/<token>" , methods = ["POST","GET"])
def reset(token):
    user = mongo.db.users.find_one({"token" : int(token)}) 
    print(user)
    if request.method == "POST" :
        if user :
            reset_password = request.form.get('reset_password')
            reset_confirm_password = request.form.get('reset_confirm_password')
            if reset_password != reset_confirm_password:
                flash("Both the passwords should match" , "danger")
                return(redirect(url_for("reset"))) 
            mongo.db.users.update({"email" : user["email"]} ,  {"$set": {"password":  bcrypt.generate_password_hash(reset_password).decode("utf-8")}})
        
            flash("Your password has been updated . Please log in to continue !","success")
            mongo.db.users.update_one({"email" : user["email"]},{"$set": {"token": "none" }}) 
            return(redirect(url_for("login")))
    
    return(render_template('reset.html'))  
@app.route("/make_payment/" , methods = ["POST" , "GET"])
def make_payment():
    if request.method == "POST":
        amount = request.form.get('amount') 
        price = int(amount)*100 
        user = mongo.db.users.find_one({"email" : session['email']})
        print(user) 
        print(amount)
        return(render_template("pay.html",user = user,price = price))
@app.route("/pay" , methods = ["POST","GET"])
def app_charge():
    
    return(redirect("/make_payment/")) 

@app.route("/d" , methods = ["POST" , "GET"])
def d():
    return(render_template("d1.html"))

if __name__ == '__main__': 
    app.run(debug = True)  