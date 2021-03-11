import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from datetime import datetime
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor, CKEditorField
from dotenv import load_dotenv
load_dotenv()


# Get the year
current_year = datetime.now().year
date = datetime.utcnow()


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
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'Post Title: {self.title}'


db.create_all()


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
    return render_template('index.html', year=current_year)


@app.route('/new_post')
def new_post():
    form = PostForm()
    return render_template('new_post.html', year=current_year, form=form)


@app.route('/about')
def about():
    return render_template('about.html', year=current_year)


@app.route('/contact')
def contact():
    return render_template('contact.html', year=current_year)


if __name__ == '__main__':
    app.run(debug=True)
