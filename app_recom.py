from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pymysql
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_bcrypt import Bcrypt

import requests
import json



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:francy@localhost/fil_rouge2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)

#Définition du modèle utilisateur SQLAlchemy pour l'utilisateur, stockant un identifiant, un nom d'utilisateur unique, et un mot de passe (hashé)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Utilisation de 60 caractères pour le hachage bcrypt


# Définissez un formulaire d'inscription
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

#gestionnaire de connexion tilisée par Flask-Login pour charger un utilisateur à partir de l'identifiant de l'utilisateur stocké en session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Chargement des données des films et des embeddings BERT 
films_Bert = pd.read_csv('models/films_Bert.csv')
cosine_similarities = np.load('models/cosine_sim.npy')
#Définition de la fonction de recommandation
def get_recommendation(title):
    selected_movie_index = films_Bert.index[films_Bert['title'] == title].tolist()[0]
    num_recommendations = 10
    ten_max_index = np.argsort(cosine_similarities[selected_movie_index])[::-1][1:num_recommendations + 1]
    recommended_titles = films_Bert.iloc[ten_max_index]['title']
    return recommended_titles.tolist()

# definir les Routes pour les pages web 

# Page d'accueil :
@app.route('/')
def home_page():
    return render_template('home.html')


# # Page d'accueil :
# @app.route('/')
# def index():
#     return render_template('index.html')

# Route pour l'inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=form.username.data).first()

        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
        else:
            # Ajouter le nouvel utilisateur à la base de données
            hashed_password = generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    return render_template('login.html')

# Route for logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Route for account management
@app.route('/account')
@login_required
def account():
    recommendations = get_recommendation(current_user.username)
    return render_template('account.html', recommendations=recommendations)

# Route for handling form submission
@app.route('/recommendations', methods=['POST'])
@login_required
def recommendations():
    title = request.form['title']
    #recommendations = get_recommendation(title)
    response_api = requests.get(f"http://127.0.0.1:5001/api?title={title}")
    print(response_api)
    response_list = json.loads(response_api.text)
    #return render_template('recommendations.html', title=title, recommendations=recommendations)
    return render_template('recommendations.html', title=title, recommendations=response_list)

if __name__ == '__main__':
    # with app.app_context():
        # db.create_all()
    app.run(debug=True)
