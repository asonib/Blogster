from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
import os
from wtforms import Form, TextAreaField, StringField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mysqldb import MySQL

app = Flask(__name__)
staticImgPath = os.path.join('static', 'img')

app.config['IMG_PATH'] = staticImgPath
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'blogster'
 
mysql = MySQL(app)
logo = os.path.join(app.config['IMG_PATH'], 'logo.png')

def authorization(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    logo = os.path.join(app.config['IMG_PATH'], 'logo.png')
    return render_template('home.html', logo=logo)


@app.route('/about')
def about():
    logo = os.path.join(app.config['IMG_PATH'], 'logo.png')
    return render_template('about.html', logo=logo)


@app.route('/articles')
def articles():
    logo = os.path.join(app.config['IMG_PATH'], 'logo.png')
    return render_template('articles.html', articles=[{
            'id': 1,
            'title':'Article One',
            'body':'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
            'author':'John Doe',
            'create_date':'04-25-2017'
        },
        {
            'id': 2,
            'title':'Article Two',
            'body':'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
            'author':'John Doe',
            'create_date':'04-25-2017'
        },
        {
            'id': 3,
            'title':'Article Three',
            'body':'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
            'author':'John Doe',
            'create_date':'04-25-2017'
        }], logo=logo)
    
@app.route('/article/<string:id>')
def article(id):
    return render_template('article.html', _id=id)

class RegisterForm(Form):
    name = StringField('Name', validators=[validators.input_required(), validators.Length(min=2, max=30)])
    email = StringField('Email', validators=[validators.input_required(), validators.Length(min=2, max=30)])
    username = StringField('Username', validators=[validators.input_required(), validators.Length(min=5, max=15)])
    password = PasswordField('Password', validators=[
        validators.input_required(), 
        validators.Length(min=5, max=50),
        validators.EqualTo('confirm', 'Passwords do not match!')
    ])
    confirm = PasswordField('Confirm Password', validators=[validators.input_required(), validators.Length(min=5, max=15)])

@app.route('/register', methods=['POST', 'GET'])
def register():
    logo = os.path.join(app.config['IMG_PATH'], 'logo.png')
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        mysql.connection.commit()
        cur.close()

        session['logged_in'] = True
        session['email'] = email

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html', form=form, logo=logo)

class LoginForm(Form):
    email = StringField('Email', validators=[validators.input_required(), validators.Length(min=2, max=30)])
    password = PasswordField('Password', validators=[
        validators.input_required(), 
        validators.Length(min=5, max=50)
    ])

@app.route('/login', methods=['POST', 'GET'])
def login():
    logo = os.path.join(app.config['IMG_PATH'], 'logo.png')
    form = LoginForm(request.form)
    if request.method == 'GET':
        return render_template('login.html', form=form, logo=logo)
    email = form.email.data
    sent_pwd = form.password.data

    print(email, sent_pwd)

    cur = mysql.connection.cursor()
    sql = "SELECT * FROM users WHERE email = %s"
    cur.execute(sql, (email,))

    result = cur.fetchone()
    if result != None:
        print(result)

        if sha256_crypt.verify(sent_pwd, result[4]):
            session['logged_in'] = True
            session['email'] = email
            print(session)
            flash('You are now logged in', 'success')
            return redirect('dashboard')
        else:
            flash('Incorrect Credentials', 'fail')
            return redirect(url_for('login'))
    else:
        flash('Email Does not exist', 'fail')
        return redirect(url_for('login'))

@app.route('/logout')
@authorization
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
@authorization
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['email']])
    articles = cur.fetchall()

    if result > 0:
        print(articles)
        return render_template('dashboard.html', articles=articles, logo=logo)
    else:
        return render_template('dashboard.html', logo=logo)

class ArticleForm(Form):
    title = StringField('Title', validators=[validators.input_required(), validators.Length(min=2, max=100)])
    body = TextAreaField('Body', validators=[validators.input_required(), validators.Length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST':
        title = form.title.data
        body = form.body.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title, author, body) VALUES(%s, %s, %s)", (title, session['email'], body))
        mysql.connection.commit()
        cur.close()

        flash('Article Added.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form, logo=logo)

if __name__ == '__main__':
    app.secret_key = 'buildv1.1'
    app.run(debug=True)