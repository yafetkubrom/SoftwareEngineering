""" Flask is a microframework to create web applications within python """

from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'c3bc4f31ea3e2837690951d1ae7e8c63'	# import secrets secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
db = SQLAlchemy(app)

from classes import MenuItem, User, Order

""" route() tells flask what URL triggers this function """
@app.route("/")
def index():
	return redirect(url_for("deals"))

""" registration route """
""" GET request loads login/signup page, POST request adds new account to db"""
@app.route("/signup", methods=["GET", "POST"])
def register():
	if request.method == "GET":
		return render_template("signup.html")
	else:
		name = request.form.get("name")
		email = request.form.get("email")
		user = User.query.filter_by(email=email).first()
		if user:
			flash("That email is exist. Please choose another")
			return redirect(url_for('register'))
		password = sha256_crypt.encrypt(request.form.get("password"))
		phone = request.form.get("phone")

		user = User(name=name, email=email, password=password, phone=phone)
		db.session.add(user)
		db.session.commit()
		return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "GET":
		return render_template("login.html")
	else:
		email = request.form.get("email")
		password = request.form.get("password")

		user = User.query.filter_by(email=email).first()

		if user is not None:
			if sha256_crypt.verify(password, user.password):
				session['logged_in'] = True
				session['email'] = email
				return redirect(url_for('index'))
		else:
			flash("Wrong email and/or password. Try again")
			return redirect(url_for('login'))

@app.route("/logout")
def logout():
	session['logged_in'] = False
	session['email'] = None
	return redirect(url_for('index'))

@app.route("/deals")
def deals():
	# TODO: get deals

	return render_template("deals.html")

@app.route("/menu", methods=["GET"])
def menu():
	# TODO: Read items from somwehere
	menu_items = [
		MenuItem('Chipotle Crispers', 'Crispy coated fried chicken tenders coated in a sweet and spicy honey chipotle sauce.', 'static/img/garden-fresh-slate-compressed.jpg', 5.99),
		MenuItem('Pizza Pie', 'Pepperoni, clean and simple', 'static/img/pepperoni-slate-compressed.jpg', 5.99),
		MenuItem('Angry Pizza Pie', 'Pepperoni Angry Peppers Mushroom Olives Chives', 'static/img/garden-fresh-slate-compressed.jpg', 5.99),
		MenuItem('Smol Pizza Pie', 'Pepperoni but smol', 'static/img/pepperoni-slate-compressed.jpg', 5.99),
		MenuItem('Baked Potatoes', 'I like to eat potatoes but not french fries', 'static/img/pepperoni-slate-compressed.jpg', 5.99),
	]

	return render_template("menu.html", menu_items=menu_items)

@app.route("/cart")
def cart():
	# TODO: read cart data
	return render_template("cart.html")

@app.route("/aboutus")
def aboutus():
	return render_template("aboutus.html")

@app.route("/account", methods=["GET", "POST"])
def account():
	if session.get('logged_in') is not None:
		if request.method == 'GET':
			if not session['logged_in']:
				return redirect(url_for('index'))
			else:
				user = User.query.filter_by(email=session['email']).first()

				return render_template('account.html', user=user)
		else:
			if not session['logged_in']:
				return redirect(url_for('index'));
			else:
				user = User.query.filter_by(email=session['email']).first()

				if user is not None:
					# update email
					email = request.form.get('email')
					if user.email != email:
						# if email not already in system
						if User.query.filter_by(email=email).first() is not None:
							flash('That email already exists, please try another')
							return redirect(url_for('account'))
						else:
							user.email = email
							session['email'] = email

					# update password
					old_password = request.form.get('old-password');

					# if passwords are present
					if len(old_password) > 0:
						if sha256_crypt.verify(old_password, user.password):
							password = sha256_crypt.encrypt(request.form.get('new-password'))
							user.password = password
						else:
							flash('Incorrect password. Try again')
							return redirect(url_for('account'))

					# update phone and name
					phone = request.form.get('phone')
					name = request.form.get('name')

					user.phone = phone
					user.name = name

					# commit user to db
					db.session.commit()

			return redirect(url_for('index'))
	else:
		return redirect(url_for('index'))

if __name__ == '__main__':
	app.run()
