from flask import Flask, render_template, request, redirect, url_for, flash,session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt

app = Flask(__name__)

# Database configuration
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] =""
app.config['MYSQL_DB'] = 'student news'
app.secret_key = 'your_secret_key_here'



mysql = MySQL(app)

class RegisterForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self,field):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where email=%s",(field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')


class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")




# ---------------------------------------------end---------------------------------------
@app.route("/")
def home():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM list ORDER BY date DESC")
    posts = cur.fetchall()
    cur.close()

    return render_template("index.html", list=posts)


@app.route("/edit")
def even():
    return render_template("edit.html")

@app.route("/post")
def post():
    return render_template("post.html")

@app.route("/admin")
def admin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM list ORDER BY id DESC")  # Table name = news
    data = cur.fetchall()
    cur.close()
    return render_template("Admin.html", list=data)
#
#------------------------------------------------------------------------


@app.route("/delete/<int:news_id>")
def delete_news(news_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM list WHERE id = %s", (news_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("admin"))


# ------------------------------------------------------------------------------------------------

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/News/admin", methods=["GET", "POST"])
def add_news():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        date = request.form["date"]

        # Check if image exists in the request
        if "image" not in request.files:
            flash("No image file uploaded")
            return redirect(request.url)

        image_file = request.files["image"]

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
        else:
            filename = None

        # Save to database (4 columns = 4 values)
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO list (title, content, date, image)
            VALUES (%s, %s, %s, %s)
        """, (title, content, date, filename))
        mysql.connection.commit()
        cur.close()

        # return redirect("/list/admin")
        return redirect(url_for('admin'))

    return render_template("Admin.html")

#-------------------------------------------------------------------------------------------

@app.route("/News/student", methods=["GET", "POST"])
def add_student_news():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        date = request.form.get("date")

        # Handle image upload
        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
        else:
            filename = None

        # Insert into database
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO list (title, content, date, image)
            VALUES (%s, %s, %s, %s)
        """, (title, content, date, filename))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('post'))  # Go back to student page

    return render_template("post.html")



#------------------------------------------------------------------------------------------


# GET route to show edit form
@app.route('/edit_news/<int:id>')
def edit_news(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM list WHERE id = %s", (id,))
    news = cur.fetchone()
    cur.close()
    return render_template('edit.html', news=news)

# POST route to handle form submission
@app.route('/edit_news_post', methods=['POST'])
def edit_news_post():
    news_id = request.form['id']
    title = request.form['title']
    content = request.form['content']
    date = request.form['date']
    image = request.files.get('image')

    filename = None
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    cur = mysql.connection.cursor()

    if filename:
        # Update with image
        # Do not include database name with spaces; use table name only
        cur.execute("""
        UPDATE list
        SET title=%s, content=%s, date=%s, image=%s
        WHERE id=%s
        """, (title, content, date, filename, news_id))

    else:
        # Update without image
        cur.execute("""
            UPDATE list
            SET title=%s, content=%s, date=%s
            WHERE id=%s
        """, (title, content, date, news_id))

    mysql.connection.commit()
    cur.close()

    # flash("News updated successfully!")
    return redirect(url_for('admin'))# redirect to your admin/news list page

# --------------------------------login----------------------------------------------------------------

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        # remember = form.remember.data


        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        user = cursor.fetchone()
        cursor.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            session['user_id'] = user[0]
            return redirect(url_for('home'))
        else:
            flash("Login failed. Please check your email and password")
            return redirect(url_for('login'))

    return render_template('login.html',form=form)


# ------------------logout----------------------------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))



if __name__ == "__main__":
    app.run(debug=True)
