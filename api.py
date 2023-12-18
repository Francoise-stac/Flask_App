from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import numpy as np
import pandas as pd

app = Flask(__name__)


# Chargement des données des films et des embeddings BERT 
films_Bert = pd.read_csv('models/films_Bert.csv')
cosine_similarities = np.load('models/cosine_sim.npy')

# Définition de la fonction de recommandation
def get_recommendation(title):
    if not films_Bert.empty:
        selected_movie_index_list = films_Bert.index[films_Bert['title'] == title].tolist()
        if selected_movie_index_list:
            selected_movie_index = selected_movie_index_list[0]
            num_recommendations = 10
            ten_max_index = np.argsort(cosine_similarities[selected_movie_index])[::-1][1:num_recommendations + 1]
            recommended_titles = films_Bert.iloc[ten_max_index]['title']
            recommendations = recommended_titles.tolist()
            
            if recommendations:
                return jsonify(recommendations)
    
    # Gérer le cas où la liste est vide, l'élément n'est pas présent, ou les recommandations sont vides
    return jsonify([])

# Route d'accueil
@app.route('/')
def home():
    return "Welcome to the Movie Recommendation API!"

# Endpoint API
@app.route('/api', methods=['GET'])
def api():
    title = request.args.get('title')
    print(title)
    if title:
        # print(get_recommendation(title))
        return get_recommendation(title)
    
    else:
        return jsonify({'error': 'Missing parameter "title" in the request'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001)


