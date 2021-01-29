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

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles, logo=logo)
    else:
        return render_template('articles.html', msg="No Articles Found", logo=logo)

    
@app.route('/article/<string:i>')
@authorization
def article(i):

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id=%s", [i])

    data = cur.fetchone()

    return render_template('article.html', _id=i, article=data)

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
    flash('Logout Successful', 'success')
    return redirect('/')

@app.route('/dashboard')
@authorization
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['email']])
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles, logo=logo)
    else:
        return render_template('dashboard.html', logo=logo)

class ArticleForm(Form):
    title = StringField('Title', validators=[validators.input_required(), validators.Length(min=2, max=100)])
    body = TextAreaField('Body', validators=[validators.input_required(), validators.Length(min=30)])

@app.route('/add_article', methods=['GET', 'POST'])
@authorization
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

@app.route('/article/delete/<string:i>', methods=['POST', 'GET'])
@authorization
def del_article(i):
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM articles WHERE id=%s", [i])
    data = cur.fetchone()
    if data:
        print(data[2])
        if data[2] == session['email']:
            cur.execute("DELETE FROM articles WHERE id=%s", [i])
            mysql.connection.commit()
            cur.close()
            flash('Article Deleted', 'success')
            return redirect('/dashboard')
        else:
            flash('User Unauthorized, Article is not yours to delete!', 'danger')
            return redirect('/dashboard')
    else:
        flash('Article Not Found!', 'danger')
        return redirect('/dashboard')

@app.route('/article/edit/<string:i>', methods=['GET', 'POST'])
def edit_article(i):
    form = ArticleForm(request.form)
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM articles WHERE id=%s", [i])
        data = cur.fetchone()
        
        if data:
            if data[2] == session['email']:
                
                form.title.data = data[1]
                form.body.data = data[3]
                return render_template('edit.html', form=form, logo=logo)
            else:
                flash('Article Not your to Edit!', 'danger')
                return redirect('/dashboard')
        else:
            flash('Something went Wrong!', 'danger')
            return redirect('/dashboard')
    elif request.method == 'POST':
        
        title = form.title.data
        body = form.body.data

        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, i))
        mysql.connection.commit()
        cur.close()

        flash('Article Edited', 'success')
        return redirect(url_for('dashboard'))


@app.errorhandler(404) 
def not_found(e): 
  return render_template("404.html", logo=logo) 

if __name__ == '__main__':
    app.secret_key = 'buildv1.1'
    app.run(debug=True)