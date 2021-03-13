import os
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, PasswordField, validators
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor, CKEditorField
from flask_login import UserMixin, login_user, LoginManager, logout_user, current_user
from functools import wraps
from datetime import datetime
import smtplib
from dotenv import load_dotenv
load_dotenv()


# Get the year
current_year = datetime.now().year
date = datetime.utcnow()


# Email config
EMAIL = os.environ.get('GMAIL')
PASSWORD = os.environ.get('GMAIL_PASS')
RECEIVER_EMAIL = os.environ.get('YMAIL')


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

# Database Configs
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


# Users Table
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    posts = relationship("Posts", back_populates="author")


# db.create_all()


# Posts Table
class Posts(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("Users", back_populates="posts")


# db.create_all()


# Post Form
class PostForm(FlaskForm):
    title = StringField("Post Title", [validators.InputRequired(message="The title field cannot be empty.")])
    subtitle = StringField("Subtitle", [validators.InputRequired(message="The subtitle field cannot be empty.")])
    img_url = StringField("Image URL", [validators.URL(message="That's not a valid url.")])
    # Add ckeditor editor field
    body = CKEditorField("Body", [validators.InputRequired(message="The body cannot be empty.")])
    submit = SubmitField("Submit Post")


# Register Form
class RegisterForm(FlaskForm):
    name = StringField("Name", [validators.InputRequired(message="The name field cannot be empty.")])
    email = StringField("Email Address", [validators.Email(message="That's not a valid email address.")])
    password = PasswordField("Password", [validators.Length(min=8, message="Password must be at least 8 characters.")])
    submit = SubmitField("Create")


# login Form
class LoginForm(FlaskForm):
    email = StringField("Email Address", [validators.Email(message="That's not a valid email address.")])
    password = PasswordField("Password", [validators.Length(min=8, message="Password must be at least 8 characters.")])
    submit = SubmitField("Enter")


# admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 (administrator) then return 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    all_posts = Posts.query.all()
    return render_template('index.html', year=current_year, blogs=all_posts)


@app.route('/blog/<int:blog_id>')
def blog(blog_id):
    detail_blog = Posts.query.filter_by(id=blog_id).first()
    return render_template('blog.html', year=current_year, blog=detail_blog)


@app.route('/new_post', methods=["GET", "POST"])
@admin_only
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        add_post = Posts(
            title=form.title.data,
            subtitle=form.subtitle.data,
            img_url=form.img_url.data,
            body=form.body.data,
            author=current_user,
            date=datetime.today().strftime("%B %d, %Y")
        )
        db.session.add(add_post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('new_post.html', year=current_year, form=form)


@app.route('/edit/<int:blog_id>', methods=["GET", "POST"])
@admin_only
def edit(blog_id):
    post = Posts.query.get(blog_id)
    edit_post = PostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_post.validate_on_submit():
        post.title = edit_post.title.data
        post.subtitle = edit_post.subtitle.data
        post.img_url = edit_post.img_url.data
        post.body = edit_post.body.data
        db.session.commit()
        return redirect(url_for("blog", blog_id=post.id))
    return render_template('new_post.html', form=edit_post, is_edit=True, year=current_year)


@app.route("/delete/<int:blog_id>")
@admin_only
def delete(blog_id):
    delete_post = Posts.query.get(blog_id)
    db.session.delete(delete_post)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/about')
def about():
    return render_template('about.html', year=current_year)


@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        message_info = f"The following information was submitted: \n" \
                       f"Name: {name} \n" \
                       f"Email: {email} \n" \
                       f"Phone Number: {phone} \n" \
                       f"Message: {message}"

        with smtplib.SMTP("smtp.gmail.com") as conn:
            conn.starttls()
            conn.login(user=EMAIL, password=PASSWORD)
            conn.sendmail(from_addr=EMAIL,
                          to_addrs=RECEIVER_EMAIL,
                          msg=f"Subject:New Blog Message!!!\n\n{message_info}")
        return render_template('contact.html', year=current_year, sent=True, name=name)
    return render_template('contact.html', year=current_year, sent=False)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Make sure the email does not exist
        if Users.query.filter_by(email=email).first():
            flash("That email exists in the database, try again!!!")
        else:
            encrypt_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

            new_user = Users(
                name=name,
                email=email,
                password=encrypt_password,
            )
            db.session.add(new_user)
            db.session.commit()

            # Log in and authenticate user after adding details to database.
            login_user(new_user)
            flash("Registered successfully, you're now logged in.")
            return redirect(url_for('index'))
    return render_template('register.html', year=current_year, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form['email']
        password = request.form['password']

        # Find the user by email
        user = Users.query.filter_by(email=email).first()

        if not user:
            flash("Invalid email address, try again.")
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, try again.')
        else:
            login_user(user)
            flash('Logged in Successfully')
            return redirect(url_for('index'))

    return render_template('login.html', year=current_year, form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
