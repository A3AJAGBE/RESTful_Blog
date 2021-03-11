from flask import Flask, render_template
from datetime import datetime

# Get the year
current_year = datetime.now().year

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', year=current_year)


@app.route('/about')
def about():
    return render_template('about.html', year=current_year)


@app.route('/contact')
def contact():
    return render_template('contact.html', year=current_year)


if __name__ == '__main__':
    app.run(debug=True)
