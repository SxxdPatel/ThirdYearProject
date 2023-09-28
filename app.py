
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



def get_recommendations(df, property_id, feature_column_names, num_similar=10):
    
    for feature_name in feature_column_names:
        df[feature_name] = df[feature_name].astype(str)

    df['Combined_Features'] = df[feature_column_names].apply(lambda row: ' '.join(row), axis=1)

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['Combined_Features'])

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    property_indices = df['Property ID'].values
    property_index = -1
    for i, prop_id in enumerate(property_indices):
        if prop_id == property_id:
            property_index = i
            break

    if property_index == -1:
        return None  
    
    property_similarity_scores = cosine_sim[property_index]

    similarity_df = pd.DataFrame({
        'Property ID': df['Property ID'],
        'Similarity': property_similarity_scores,
        'City': df['City'],
        'BHK': df['BHK'],
        'Size': df['Size'],
        'Rent': df['Rent'],
        'Bathroom': df['Bathroom'],
        'Image Link': df['Image Link'],
        'Posted On':df['Posted On'],  
    })

    similarity_df = similarity_df[similarity_df['Property ID'] != property_id]

    top_similar_properties = similarity_df.sort_values(by='Similarity', ascending=False).head(num_similar)
    
    return top_similar_properties








# import csv

# csv_file_path = 'user_interactions.csv'

# def write_interaction_to_csv(user_id, property_id, interaction_type):
#     try:
#         fieldnames = ['userId', 'propertyId', 'interactionType']

#         with open(csv_file_path, mode='a', newline='') as csv_file:
#             writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

#             if csv_file.tell() == 0:
#                 writer.writeheader()

#             writer.writerow({'userId': user_id, 'propertyId': property_id, 'interactionType': interaction_type})

#         return "Interaction saved successfully to CSV"

#     except Exception as e:
#         return f"Error: {str(e)}", 500








from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random
import sqlite3

app = Flask(__name__)
app.secret_key = 'y$7c@9^H5#2aP!zQ'  

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

df = pd.read_csv('House_Rent_Dataset.csv')

@app.route('/')
def index():
    cities = df['City'].unique()

    city_properties = {}

    for city in cities:
        city_df = df[df['City'] == city]
        random_properties = city_df.sample(n=5) 
        city_properties[city] = random_properties

    return render_template('index.html', city_properties=city_properties)



@app.route('/more-properties', methods=['GET'])
def more_properties():
    selected_city = request.args.get('city')

    more_properties = df[df['City'] == selected_city]

    return render_template('more_properties.html', city=selected_city, more_properties=more_properties)



# @app.route('/interactions/<int:user_id>/<int:property_id>/<interaction_type>', methods=['POST'])
# def user_interaction(user_id, property_id, interaction_type):
#     try:
#         if interaction_type == "favorite":
#             result = write_interaction_to_csv(user_id, property_id, interaction_type)

#             return result

#     except Exception as e:
#         return f"Error: {str(e)}", 500





@app.route('/property/<int:property_id>')
def property_details(property_id):
    try:
        user_id = session.get('user_id')

        property = df[df['Property ID'] == property_id].iloc[0]

        feature_names = ['BHK', 'Rent', 'Size', 'City', 'Bathroom']  
        num_similar_properties = 5  
        recommended_properties = get_recommendations(df, property_id, feature_names, num_similar_properties)
        print(recommended_properties)

        return render_template(
            'property_details.html',
            property=property,
            user_id=user_id,
            recommended_properties=recommended_properties
        )
    except Exception as e:
        return f"Error: {str(e)}"



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        
        return redirect('/login')
    
    return render_template('signup.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return 'Invalid login credentials'
    
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return 'Welcome to the dashboard!'
    else:
        return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')


@app.before_request
def check_session():
    if request.endpoint not in ['login', 'signup'] and 'user_id' not in session:
        return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)


