import math
from flask import Flask, render_template, request, session,redirect
from flask_sqlalchemy import SQLAlchemy
# This import is used to connect to our database
from datetime import datetime
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename

c=open('config.json', 'r')
params = json.load(c)
#     using the import json we have used json.load to load the params configuration from config.json file in the flask.py

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
# Whenever we use a session variable we need to make a secret key using the above method

app.config['UPLOAD_FOLDER'] = params['file_location']

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_pw"]
)
# This is the security settings of gmail's smtp server always use this as same
mail = Mail(app)
# We set an object for Mail with parameter app(name of our flask app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]
# This is the default syntax to connect to phpmyadmin
# here root is our username and pw is by default set to blank so no pw
# root:'<pw>'
# We have set the path of database in config.json
# These are the login details for xampp

db = SQLAlchemy(app)


# Now we give our database a name ie db

# Variables set in contact table of mysql:
# sno ,name ,email ,phone_num ,msg ,date

class Contact(db.Model):
    # Always put this name same to that of the table name in the database but always start with a capital letter
    # class contacts is made to set the variables as saved in database
    # NOTE: keep the names of the variables same as that in the database
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(20), nullable=False)

class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    subheading = db.Column(db.String(80), nullable=False)
    img_file = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    by = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
# Make the same number of classes as the number of tables you are using

# db.column sets the variable as a column in the table
# db.String or Integer sets the data type
# as Sno. is our primary key so primary_key=True
# Nullable =False for everyone ie no value can be left blank

@app.route("/")
def home():
    posts = Post.query.filter_by().all()
    # posts = Post.query.filter_by().all()[0:params['noofposts']]
    # posts = Post.query.filter_by().all()[0:5]
    # This is the hard code to show only first 5 blogs in our homepage
    last = math.ceil(len(posts)/int(params['noofposts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['noofposts']):(page-1)*int(params['noofposts'])+ int(params['noofposts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)

        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    return render_template('index.html', params=params,posts=posts, prev=prev, next=next)
# We passes params=params in each of the html pages so we can use the variables set in the config.json in jinja templating

@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/contact", methods=['GET', 'POST'])
# The GET method is set by default to every route it means that whenever we are opening an image or any html page then it GET method
# Now we also set it to POST method ir form will post whatever we write in the for into our database
def contact():
    if request.method == 'POST':
        # '''Add entry to the database'''

        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        # First add a name attribute to all the entry fields in the form in vs code
        # Here the left hand side are the variables defined by us
        # right hand side are the name attributes set in contact.html
        # we are taking the values from the html and giving them into our variables

        entry = Contact(name=name, phone_num=phone, msg=message, date=datetime.now(), email=email)
        # Now we are making an entry that means we are setting the values of our variables to the variables in the database

        db.session.add(entry)
        # We add an entry in our database use db object
        db.session.commit()
        # Commit means save
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail_user']],
                          # the recipients is always a list so write in square brackets
                          body="Name : "+name+"\n"+"Email : "+email+"\n"+"Phone Number : "+phone+"\n"+"Message : "+message
                          )
    #     This will send a message to your email account saying the above things
    #     also before it will send an email to your account you need to change settings of your account to enable less-secure apps

    #     Now our POST method is completed
    # ALWAYS ADD A FIRST ENTRY IN PHPMYADMIN BY YOURSELF SO THAT THE AUTO INCREMENT IN OUR SNO WORKS PERFECTLY

    return render_template('contact.html', params=params)
    # This satisfies the GET method

@app.route("/post/<string:slug>",methods=['GET'])
def blog_post(slug):
    post=Post.query.filter_by(slug=slug).first()
    return render_template('post.html',params=params,post=post)

@app.route("/dashboard",methods=["GET","POST"])
def dashboard():
    error=None
    if "user" in session and session['user']==params['admin_user']:
        posts = Post.query.all()
        return render_template("dashboard.html", params=params, posts=posts)
    # This code is for remember me ie when we login once it stays logged in until we press logout

    if request.method=="POST":
        username = request.form.get("uname")
        # Using the request.form.get we take the variables named uname and pass in signin.html and save them into our own variables
        password = request.form.get("pass")
        rememberme=request.form.get("remember")
        if username == params['admin_user']:
            if password == params['admin_pass']:
                if rememberme == 'checked':
                    # Using this we configured the remember me button
                    session['user'] = username
                    # This makes a session for our user so it can automatically detect if we were logged in before or not
                    # For this we need to make a secret key that is made above
                    posts = Post.query.all()
                    return render_template("dashboard.html", params=params, posts=posts)
                else:
                    posts = Post.query.all()
                    return render_template("dashboard.html", params=params, posts=posts)
            else:
                error = "Wrong login credentials!! Please try again"
        #         This means whenever the username or the pw is incorrect then error variable will contain a string with the above text
        else:
            error = "Wrong Login Credentials!! Please Try Again"

    return render_template("sign-in.html", params=params, error=error)
    # Finally if the code reaches at this point that means the username or the pw is incorrect and w will return the user the sign in page again and show a error

@app.route("/logout")
def logout():
    if "user" in session and session['user'] == params['admin_user']:
        session.pop('user')
        return redirect("/dashboard")
    else:
        return redirect("/dashboard")

@app.route("/edit/<string:sno>", methods=["GET","POST"])
def edit(sno):
    if "user" in session and session['user'] == params['admin_user']:
        if request.method=="POST":
            title = request.form.get('title')
            subheading = request.form.get('subheading')
            slug = request.form.get('slug')
            content = request.form.get('content')
            by = request.form.get('by')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno=='0':
                post = Post(title=title,subheading=subheading,slug=slug,content=content,by=by,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post=Post.query.filter_by(sno=sno).first()
                post.title = title
                post.subheading = subheading
                post.slug = slug
                post.content = content
                post.by = by
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect("/edit/"+sno)

    post=Post.query.filter_by(sno=sno).first()
    return render_template('edit.html',params=params,sno=sno,post=post)

@app.route("/upload", methods=["GET","POST"])
def upload():
    msg=None
    if "user" in session and session['user'] == params['admin_user']:
        if request.method=="POST":
            file= request.files['img_file']
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
            msg="Congrats! Your file has been uploaded"
    posts = Post.query.all()
    return render_template("dashboard.html",params=params,posts=posts,msg=msg)

@app.route("/delete-page/<string:sno>", methods=["GET","POST"])
def delete_page(sno):
    if "user" in session and session['user'] == params['admin_user']:
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")

@app.route("/delete/<string:sno>", methods=["GET","POST"])
def delete(sno):
    post = Post.query.filter_by(sno=sno).first()
    return render_template("delete.html",params=params,post=post)

app.run(debug=True)
c.close()
# iF ANY TIME THERE IS AN ERROR THAT
# NO MODULE NAMED MySQLdb
# THEN OPEN CMD THEN WRITE PIP INSTALL MYSQLCLIENT

# /* THE CONFIG.JSON IS USED TO SET SOME VARIABLES SO ANOTHER USER CAN EASILY CONFIGURE OUR CODE WITHOUT ANY DIFFICULTIES*/
