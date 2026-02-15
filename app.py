from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import relationship
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fsdfhfvf76866547i458ru8y7f6g5'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/expenses.db')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# -------------------- MODELS --------------------

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    categories = relationship('Category', backref='user', lazy=True)
    expenses = relationship('Expense', backref='user', lazy=True)
    budgets = relationship('Budget', backref='user', lazy=True)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subcategories = relationship('SubCategory', backref='category', lazy=True)
    expenses = relationship('Expense', backref='category', lazy=True)
    budgets = relationship('Budget', backref='category', lazy=True)

class SubCategory(db.Model):
    __tablename__ = 'sub_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    expenses = relationship('Expense', backref='subcategory', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'))

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7))  # Format: YYYY-MM
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=True)

    __tablename__ = 'budget'

    # relationships provided via backrefs on related models

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- AUTH --------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# -------------------- EXPENSES --------------------

@app.route('/')
@login_required
def index():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)
    return render_template('index.html', expenses=expenses, total=total)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    subcategories = SubCategory.query.join(Category).filter(Category.user_id == current_user.id).all()

    if request.method == 'POST':
        subcat = request.form.get('subcategory') or None
        expense = Expense(
            amount=float(request.form['amount']),
            description=request.form.get('description'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d') if request.form.get('date') else datetime.utcnow(),
            user_id=current_user.id,
            category_id=int(request.form['category']) if request.form.get('category') else None,
            subcategory_id=int(subcat) if subcat else None
        )
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add_expense.html', categories=categories, subcategories=subcategories)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)

    if request.method == 'POST':
        expense.amount = float(request.form['amount'])
        expense.description = request.form.get('description')
        if request.form.get('date'):
            expense.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        if request.form.get('category'):
            expense.category_id = int(request.form.get('category'))
        subcat = request.form.get('subcategory') or None
        expense.subcategory_id = int(subcat) if subcat else None
        db.session.commit()
        return redirect(url_for('index'))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    subcategories = SubCategory.query.join(Category).filter(Category.user_id == current_user.id).all()
    return render_template('edit_expense.html', expense=expense, categories=categories, subcategories=subcategories)

@app.route('/delete/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('index'))

# -------------------- CATEGORIES --------------------

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    if request.method == 'POST':
        category = Category(name=request.form['name'], user_id=current_user.id)
        db.session.add(category)
        db.session.commit()
        return redirect(url_for('categories'))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories.html', categories=categories)



@app.route('/dashboard')
@login_required
def dashboard():

    # 1️⃣ Category breakdown
    category_data = db.session.query(
        Category.name,
        func.sum(Expense.amount)
    ).join(Expense, Expense.category_id == Category.id)\
     .filter(Expense.user_id == current_user.id)\
     .group_by(Category.name).all()

    category_labels = [c[0] for c in category_data]
    category_totals = [float(c[1]) for c in category_data]

    # 2️⃣ Monthly trend
    monthly_data = db.session.query(
        func.strftime('%Y-%m', Expense.date),
        func.sum(Expense.amount)
    ).filter(Expense.user_id == current_user.id)\
     .group_by(func.strftime('%Y-%m', Expense.date)).all()

    month_labels = [m[0] for m in monthly_data]
    month_totals = [float(m[1]) for m in monthly_data]

    # Budget alerts (server-side)
    alerts = []
    current_month = datetime.utcnow().strftime('%Y-%m')
    budgets = Budget.query.filter_by(user_id=current_user.id, month=current_month).all()

    for budget in budgets:
        q = db.session.query(func.sum(Expense.amount))\
            .filter(
                Expense.user_id == current_user.id,
                Expense.category_id == budget.category_id,
                func.strftime('%Y-%m', Expense.date) == current_month
            )
        if budget.subcategory_id:
            q = q.filter(Expense.subcategory_id == budget.subcategory_id)

        spent = q.scalar() or 0

        cat = Category.query.get(budget.category_id)
        label = cat.name if cat else f"Category {budget.category_id}"
        if budget.subcategory_id:
            sub = SubCategory.query.get(budget.subcategory_id)
            if sub:
                label = f"{label} / {sub.name}"

        if spent > budget.amount:
            alerts.append(f"⚠ Budget exceeded for {label}: spent {spent} > budget {budget.amount}")

    return render_template(
        "dashboard.html",
        category_labels=json.dumps(category_labels),
        category_totals=json.dumps(category_totals),
        month_labels=json.dumps(month_labels),
        month_totals=json.dumps(month_totals),
        alerts=alerts
    )

#---------MONTHLY REPORT-----------

@app.route('/monthly_report/<int:year>/<int:month>')
@login_required
def monthly_report(year, month):

    report_data = Expense.query.filter(
        Expense.user_id == current_user.id,
        func.strftime('%Y', Expense.date) == str(year),
        func.strftime('%m', Expense.date) == f"{month:02d}"
    ).all()

    total = sum(e.amount for e in report_data)

    return render_template(
        "monthly_report.html",
        expenses=report_data,
        total=total,
        year=year,
        month=month
    )

#-------Budget Route--------- 

@app.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    if request.method == 'POST':
        budget = Budget(
            amount=float(request.form['amount']),
            month=request.form['month'],
            user_id=current_user.id,
            category_id=request.form['category']
        )
        db.session.add(budget)
        db.session.commit()
        return redirect(url_for('budgets'))

    categories = Category.query.filter_by(user_id=current_user.id).all()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()

    return render_template("budgets.html", categories=categories, budgets=budgets)



# --------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # bind to 0.0.0.0 so the app is reachable from other devices on the LAN
    app.run(host='0.0.0.0', debug=True)
