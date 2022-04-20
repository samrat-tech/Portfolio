from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
# from werkzeug.utils import secure_filename
from flask_mail import Mail
from datetime import datetime
import json
import os
import math



with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
# app.config['UPLOAD_FOLDER'] = params['upload_location']

# add this in json for file upload
# "upload_location": "C:\\Users\\MSI laptop\\Desktop\\flask\\static\\assets\\cv"

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)

mail = Mail(app)

local_server = True
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):

    SN= db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.VARCHAR(50), nullable=False)
    Phone = db.Column(db.VARCHAR(50), nullable=False)
    Msg = db.Column(db.String(80), nullable=False)
    Date = db.Column(db.DateTime(20), nullable=True)


class Projects(db.Model):

    SN= db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(80), nullable=False)
    Slug = db.Column(db.VARCHAR(50), nullable=False)
    Content = db.Column(db.VARCHAR(50), nullable=False)
    Tagline = db.Column(db.VARCHAR(50), nullable=False)
    Img_file = db.Column(db.VARCHAR(50), nullable=False)
    Demo_link = db.Column(db.VARCHAR(50), nullable=False)
    Date = db.Column(db.DateTime(20), nullable=True)


@app.route("/")
def home():
    projects = Projects.query.filter_by().all()
    last = math.ceil(len(projects) / int(params['no_of_projects']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    projects = projects[(page - 1) * int(params['no_of_projects']):(page - 1) * int(params['no_of_projects']) + int(params['no_of_projects'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    return render_template('index.html', params=params, projects=projects, prev=prev, next=next)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        msg = request.form.get('msg')

        entry = Contacts(Name = name, Email= email, Phone = phone, Msg = msg, Date = datetime.now())
        db.session.add(entry)
        db.session.commit()

        mail.send_message('New message from ' + name,
                          sender = email,
                          recipients = [params['gmail-user']],
                          body= 'Email id -' + email  + "\n" + 'Phone number: ' + phone + "\n" + msg
                          )

    return render_template('contact.html', params = params)


@app.route("/about")
def about():
    return render_template('about.html', params = params)


@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():

    if 'user' in session and session['user'] == params['admin_user']:
        projects = Projects.query.all()
        return render_template('dashboard.html', params=params, projects=projects)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            session['user'] = username
            projects = Projects.query.all()
            return render_template('dashboard.html', params=params, projects=projects)

    return render_template('login.html', params = params)


@app.route("/edit/<string:SN>", methods=['GET', 'POST'])
def edit(SN):

    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            tline = request.form.get('tline')
            img_file = request.form.get('img_file')
            demo_link = request.form.get('demo_link')

            if SN =='0':
                project = Projects(Title=title, Slug=slug, Content=content, Tagline=tline, Img_file=img_file, Demo_link=demo_link, Date=datetime.now())
                db.session.add(project)
                db.session.commit()
            else:
                project = Projects.query.filter_by(SN=SN).first()
                project.Title = title
                project.Slug = slug
                project.Content = content
                project.Tagline = tline
                project.Img_file = img_file
                project.Demo_link = demo_link
                project.date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+SN)
        project = Projects.query.filter_by(SN=SN).first()
        return render_template('edit.html', params=params, project=project, SN=SN)



@app.route("/project/<string:project_slug>", methods=['GET'])
def project_route(project_slug):
    project = Projects.query.filter_by(Slug=project_slug).first()
    return render_template('project.html', params = params, project=project)

@app.route("/project", methods=['GET'])
def project():
    projects = Projects.query.filter_by().all()[0:params['no_of_blog']]
    return render_template('all_projects.html', params = params, projects=projects)

# @app.route("/uploader" , methods=['GET', 'POST'])
# def uploader():
#     if "user" in session and session['user']==params['admin_user']:
#         if request.method=='POST':
#             f = request.files['file1']
#             f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
#             return "Uploaded successfully!"

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:SN>" , methods=['GET', 'POST'])
def delete(SN):
    if "user" in session and session['user']==params['admin_user']:
        project = Projects.query.filter_by(SN=SN).first()
        db.session.delete(project)
        db.session.commit()
    return redirect("/dashboard")


if __name__ == "__main__":
    app.debug = True
    app.run()
