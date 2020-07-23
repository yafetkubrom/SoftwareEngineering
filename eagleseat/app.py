""" Flask is a microframework to create web applications within python """

from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from classes import OrderAmount, User, Customer

import os
from dotenv import load_dotenv

# load .env
load_dotenv()
secret_key = os.getenv('SECRET_KEY')
database_file = os.getenv('DATABASE_FILE')
merchant_id = os.getenv('MERCHANT_ID')

print(secret_key)
print(database_file)
print(merchant_id)

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key # import secrets secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_file
db = SQLAlchemy(app)

from charge_card import charge
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
	menu_items = [
		MenuItem('Chipotle Crispers', 'Crispy coated fried chicken tenders coated in a sweet and spicy honey chipotle sauce.', 'static/img/burger.jpg', 5.99),
		MenuItem('Pizza Pie', 'Pepperoni, clean and simple', 'static/img/burger.jpg', 5.99),
		MenuItem('Angry Pizza Pie', 'Pepperoni Angry Peppers Mushroom Olives Chives', 'static/img/burger.jpg', 5.99)
	]
	orderAmount = OrderAmount()
	for item in menu_items:
		orderAmount.subTotal += item.price
	
	orderAmount.subTotal =(orderAmount.subTotal)
	print(orderAmount.subTotal)
	orderAmount.salesTax = (orderAmount.TAX * orderAmount.subTotal)
	orderAmount.total = (orderAmount.salesTax +  orderAmount.subTotal)
	orderAmount.subTotal = '{:0>2.2f}'.format(orderAmount.subTotal)
	orderAmount.salesTax = '{:0>2.2f}'.format(orderAmount.salesTax)
	orderAmount.total = '{:0>2.2f}'.format(orderAmount.total)
	return render_template("cart.html", menu_items=menu_items, orderAmount=orderAmount)

@app.route("/checkout", methods=["POST", "GET"])
def checkout():
	menu_items = [
		MenuItem('Chipotle Crispers', 'Crispy coated fried chicken tenders coated in a sweet and spicy honey chipotle sauce.', 'static/img/burger.jpg', 5.99),
		MenuItem('Pizza Pie', 'Pepperoni, clean and simple', 'static/img/burger.jpg', 5.99),
		MenuItem('Angry Pizza Pie', 'Pepperoni Angry Peppers Mushroom Olives Chives', 'static/img/burger.jpg', 5.99)
	]
	orderAmount=OrderAmount()
	for item in menu_items:
		orderAmount.subTotal += item.price
	orderAmount.total= '{:.2f}'.format((orderAmount.TAX * orderAmount.subTotal) + orderAmount.subTotal)

	customer = Customer("Jacob Murillo","1234","jacob@mail.com","dsds","000-000-000","riverside tx")
	customer.name = "Jacob Murillo"

	amount = float(orderAmount.total)
	
	if request.method == "POST":
		option = request.form['transaction']
		print(option)
		if option =="creditCard":
			card_number = request.form.get("cardNumber")
			expiration_date = request.form.get("expDate")
	
			print(card_number, expiration_date, amount)
			return redirect(url_for('index'))
		else:
			return redirect(url_for('index'))

	
	return render_template("checkout.html", menu_items=menu_items, orderAmount=orderAmount, customer=customer)


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
