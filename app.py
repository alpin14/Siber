from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('You have successfully logged in.', 'success')
            return redirect(url_for('index')) 
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/index')
@login_required  
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)

@app.route('/add', methods=['POST'])
@login_required
def add_student():
    name = request.form['name']
    age = request.form['age']
    grade = request.form['grade']

    if not name or not age or not grade:
        flash('All fields are required', 'warning')
        return redirect(url_for('index'))

    new_student = Student(name=name, age=int(age), grade=grade)
    db.session.add(new_student)
    db.session.commit()
    flash('Student added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<id>')
@login_required
def delete_student(id):
    # Rentan terhadap SQL Injection karena menggunakan query mentah
    db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        grade = request.form['grade']

        if not name or not age or not grade:
            flash('All fields are required', 'warning')
            return redirect(url_for('edit_student', id=id))

        # Rentan terhadap SQL Injection karena menggunakan query mentah
        db.session.execute(text(f"UPDATE student SET name='{name}', age={age}, grade='{grade}' WHERE id={id}"))
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', student=student)

# Handle unauthorized access
@login_manager.unauthorized_handler
def unauthorized():
    flash("Access Denied! Please log in first.", 'danger')
    return redirect(url_for('login'))  # Ensure users are redirected to login

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create a default admin user
        if not User.query.filter_by(email='admin@example.com').first():
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin = User(email='admin@example.com', password=hashed_password)
            db.session.add(admin)
            db.session.commit()
    app.run(host='0.0.0.0', port=5000, debug=True)
