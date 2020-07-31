import json

""" Flask is a microframework to create web applications within python """

from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from flask_mail import Mail, Message


import os
import os.path
from dotenv import load_dotenv
import random

# load .env if exists
if os.path.exists('.env'):
    load_dotenv()
else:
    # load .env.example if no .env is present
    print('.env file not found, using example file...')
    load_dotenv(dotenv_path='.env.example')

secret_key = os.getenv('SECRET_KEY')
database_file = os.getenv('DATABASE_FILE')
#database_file = "restaurant.db"
merchant_id = os.getenv('MERCHANT_ID')

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key # import secrets secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_file
db = SQLAlchemy(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_USERNAME'] = 'eagle.eats.2020@gmail.com'
app.config['MAIL_PASSWORD'] = 'Password!!'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

from charge_card import charge
from classes import MenuItemDb, User, Order, OrderAmount, Customer
db.create_all()
menu_items = MenuItemDb.query.all()

# randomly pick 4 deal items
deal_items = []
while len(deal_items) < 2:
	# get random item from menu_items
	deal_item = random.choice(menu_items)

	# add deal_item if it is not already in deal_items
	if deal_item not in deal_items:
		deal_items.append(deal_item)

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

		msg = Message('EagleEats', sender='eagle.eats.2020@gmail.com', recipients=[email])
		msg.body="Thank you for registering with EagleEats"
		msg.html=render_template("reg_email.html")
		mail.send(msg)
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
				init_cart()
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
	return render_template("menu.html", menu_items=deal_items)

@app.route("/menu", methods=["GET"])
def menu():
	# TODO: Read items from somwehere

	menu_items_filtered = []
	unique_names = []
	for item in menu_items:
		if item.name not in unique_names:
			menu_items_filtered.append(item)
			unique_names.append(item.name)
	
	return render_template("menu.html", menu_items=menu_items_filtered)



@app.route("/checkout", methods=["POST", "GET"])
def checkout():
	
	orderAmount = OrderAmount()
	cart_item =access_cart()
	for item in cart_item:
		orderAmount.subTotal += item.price
	
	orderAmount.total= '{:.2f}'.format((orderAmount.TAX * orderAmount.subTotal) + orderAmount.subTotal)

	user = User.query.filter_by(email=session['email']).first()

	amount = float(orderAmount.total)
	
	if request.method == "POST":
		option = request.form['transaction']
		print(option)
		if option =="creditCard":
			card_number = request.form.get("cardNumber")
			expiration_date = request.form.get("expDate")
	
			charge(card_number,expiration_date, amount, merchant_id)
			return redirect(url_for('index'))
		else:
			return redirect(url_for('index'))

	empty_cart()

	
	return render_template("checkout.html", cart_item=cart_item, orderAmount=orderAmount, customer=user)

# FIXME TODO XXX: TEMPORARY ROUTES FOR HELPING DEVELOPMENT
@app.route("/cart/json")
def cart_json():
	return session['cart']

@app.route("/cart/empty")
def empty_cart_route():
	empty_cart()
	return redirect(url_for('cart_json'))
# FIXME TODO XXX

def build_option_string(option, value):
	# Use `No` instead of `None` in option string
	# e.g. None Pickles -> No Pickles
	if value == 'None':
		return 'No ' + option
	else:
		return value.capitalize() + ' ' + option.capitalize()

@app.route("/cart", methods=["GET", "POST"])
def cart():
	if request.method == "POST":
		id = request.form.get('id')

		options = []
		for field in request.form:
			# already grabbed ID, so skip it
			if field == 'id':
				continue

			field_value = request.form.get(field)

			# if field is a size, then value is added to ID to get
			# the 'real' ID of the menu item
			if field == 'size':
				# calculate 'real' ID of size item
				if field_value == 'small':
					id = str(int(id) + 0)
				elif field_value == 'medium':
					id = str(int(id) + 1)
				elif field_value == 'large':
					id = str(int(id) + 2)
				elif field_value == 'giant':
					id = str(int(id) + 3)
			else:
				# everything else is an option string
				# NOTE: only add modifications (e.g. not 'Regular')
				if field_value != 'regular':
					options.append(build_option_string(field, field_value))

		add_to_cart(id, options)
		# return to menu
		return redirect(url_for('menu'))
	else:
		orderAmount = OrderAmount()
		cart_item =access_cart()
		user = User.query.filter_by(email=session['email']).first()
		for item in cart_item:
			orderAmount.subTotal += item.price
			
		orderAmount.subTotal =(orderAmount.subTotal)
		orderAmount.salesTax = (orderAmount.TAX * orderAmount.subTotal)
		orderAmount.total = (orderAmount.salesTax +  orderAmount.subTotal)
		orderAmount.subTotal = '{:0>2.2f}'.format(orderAmount.subTotal)
		orderAmount.salesTax = '{:0>2.2f}'.format(orderAmount.salesTax)
		orderAmount.total = '{:0>2.2f}'.format(orderAmount.total)
		return render_template("cart.html", cart_item = cart_item ,orderAmount=orderAmount, user=user)

def init_cart():
	# json boilerplate
	session['cart'] = '{"items":[]}'

def add_to_cart(id, options):
	item = {
		"id": id,
		"options": options
	}

	cart = json.loads(session['cart'])

	cart['items'].append(item)


	session['cart'] = json.dumps(cart)

def remove_from_cart(pos):
	if 0 < pos < len(cart['items']):
		cart = json.loads(session['cart'])

		del cart['items'][pos]

		session['cart'] = json.dumps(cart)

def empty_cart():
	cart = json.loads(session['cart'])

	while len(cart['items']) > 0:
		del cart['items'][0]

	session['cart'] = json.dumps(cart)

	return session['cart']

def access_cart():
	cart = json.loads(session['cart'])
	cart_item = []
	for item in cart['items']:
		cart_item.append(menu_items[int(item['id']) -1 ])
	return cart_item

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
