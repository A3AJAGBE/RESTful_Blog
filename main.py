import os
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor, CKEditorField
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


# Posts Table
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'Post Title: {self.title}'


# db.create_all()


# Post Form
class PostForm(FlaskForm):
    title = StringField("Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Author Name", validators=[DataRequired()])
    img_url = StringField("Image URL", validators=[DataRequired(), URL()])
    # Add ckeditor editor field
    body = CKEditorField("Body", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


@app.route('/')
def index():
    all_posts = Posts.query.all()
    return render_template('index.html', year=current_year, blogs=all_posts)


@app.route('/blog/<int:blog_id>')
def blog(blog_id):
    detail_blog = Posts.query.filter_by(id=blog_id).first()
    return render_template('blog.html', year=current_year, blog=detail_blog)


@app.route('/new_post', methods=["GET", "POST"])
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        add_post = Posts(
            title=form.title.data,
            subtitle=form.subtitle.data,
            author=form.author.data,
            img_url=form.img_url.data,
            body=form.body.data,
            date=datetime.today().strftime("%B %d, %Y")
        )
        db.session.add(add_post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('new_post.html', year=current_year, form=form)


@app.route('/edit/<int:blog_id>', methods=["GET", "POST"])
def edit(blog_id):
    post = Posts.query.get(blog_id)
    edit_post = PostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_post.validate_on_submit():
        post.title = edit_post.title.data
        post.subtitle = edit_post.subtitle.data
        post.img_url = edit_post.img_url.data
        post.author = edit_post.author.data
        post.body = edit_post.body.data
        db.session.commit()
        return redirect(url_for("blog", blog_id=post.id))
    return render_template('new_post.html', form=edit_post, is_edit=True, year=current_year)


@app.route("/delete/<int:blog_id>")
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


if __name__ == '__main__':
    app.run(debug=True)
