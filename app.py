from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session 
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
import random
import threading
import time


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', uuid.uuid4().hex)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

def create_user_directory():
    user_id = session.get("user_id")  
    user_directory = os.path.join("static", "uploads", str(user_id))
    os.makedirs(user_directory, exist_ok=True)
    return user_directory

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Function to delete the file after a delay
def delete_image_after_delay(image_path, delay=5):
    time.sleep(delay)
    if os.path.exists(image_path):
        os.remove(image_path)

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/landing')
def landing():
    return render_template('landing_screen.html')

@app.route('/random_generator')
def random_generator():
    return render_template('randomgenerator.html')


@app.route('/proceed_signup', methods=['POST'])
def proceed_signup():
    username = request.form['username']
    password = request.form['password']
    
    user = User.query.filter_by(username=username).first()
    if user:
        flash('Username is already taken. Please choose another one', 'error')
        return redirect(url_for('signup'))
    
    new_user = User(username=username, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    
    flash('Signup successful! Please log in', 'signup_success')
    return redirect(url_for('login'))


@app.route('/proceed_login', methods=['POST'])
def proceed_login():
    username = request.form['username']
    entered_password = request.form['password']
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password, entered_password):
        session["user_id"] = user.id
        print(user)
        create_user_directory()

        flash('Login successful!', 'login_success')
        return redirect(url_for('landing'))  
    else:
        flash('Invalid username or password. Please try again!!', 'error')
        return redirect(url_for('login'))
    
    
@app.route("/upload_images", methods=["POST"])
def upload_images():
    # Ensure user directory exists
    user_directory = create_user_directory()
    
    # Save each uploaded file in the user’s directory
    uploaded_files = request.files.getlist("images")
    for file in uploaded_files:
        if file:
            file_path = os.path.join(user_directory, file.filename)
            file.save(file_path)
    
    return jsonify({"success": True, "message": "Images uploaded successfully!"})


@app.route("/get_random_image")
def get_random_image():
    user_id = session.get("user_id")
    user_id = str(user_id)
    user_directory = os.path.join("static", "uploads", str(user_id))
    
    if os.path.exists(user_directory):
        images = [img for img in os.listdir(user_directory) if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        
        if images:
            random_image = random.choice(images)
            image_path = os.path.join(user_directory, random_image)
            image_url = f"/static/uploads/{user_id}/{random_image}"
            
            # Start a separate thread to delete the image after a short delay
            threading.Thread(target=delete_image_after_delay, args=(image_path,)).start()
            
            return jsonify({"image_url": image_url})
        else:
            # No images left, signal to redirect to the landing page
            return jsonify({"done": True})
    
    return jsonify({"error": "No images found."}), 404

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    user_directory = os.path.join("static", "uploads", str(user_id))
    
    # Remove the user's directory if it exists
    if os.path.exists(user_directory):
        for file in os.listdir(user_directory):
            file_path = os.path.join(user_directory, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        os.rmdir(user_directory)
    
    # Clear the session
    session.clear()
    
    # Redirect to the landing screen or login page
    return redirect(url_for("login"))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
