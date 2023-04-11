from flask import Flask, render_template, request
from GameRecommendation import *

app = Flask(__name__)

if os.path.isfile('GameDetails.csv') == False:

    if os.path.isfile('Appid.json'):
        AppID = ReadJSON('Appid.json')
    else:
        AppID = GatSteamAppID()
        WriteJSON('AppID.json',AppID)
    if os.path.isfile('correctedGameDetails_full.json'):
        GameDetails = ReadJSON('correctedGameDetails_full.json')
    else:
        GameDetails = GetSteamGameDetails(AppID)
        WriteJSON('GameDetails.json',GameDetails)
    
    WriteGameDetailsCSV('GameDetails.csv',GameDetails)

GameList = ReadGameDetailsCSV('GameDetails.csv')
recommendations = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    
    UserPreferences = User(
        UserID = request.form.get('name'),
        Genres = request.form.get('genres'),
        Free = request.form.get('free') == 'True',
        Categories = request.form.get('categories'),
        Platform = request.form.get('platform'),
        ReleaseYear = int(request.form.get('release_date')),
        )
    
    game_graph = Graph()

    FilteredGameList = FilterGamesByPreferences(GameList, UserPreferences)
    Recommendations = []

    for game in FilteredGameList:
        game_graph.add_node(game)
        Recommendations.append(game.Recommendations)
    if len(Recommendations) != 0:
        MaxRecommendation = max(Recommendations)
    else:
        MaxRecommendation = 1

    game_graph.add_node(UserPreferences)

    user_vertex = [vertex for vertex in game_graph.nodes if vertex.node == UserPreferences][0]
    for game_vertex in game_graph.nodes:
        if game_vertex.node != UserPreferences:
            similarity = ComputeSimilarity(UserPreferences, game_vertex.node) 
            score = similarity + (game_vertex.node.Rating / 100.0) + 3*(game_vertex.node.Recommendations /  MaxRecommendation)
            game_graph.add_edge(user_vertex, game_vertex,similarity, score)

    global recommendations 
    recommendations = game_graph.get_recommendations(user_vertex, k=5)
    
    return render_template('recommendations.html', recommendations=recommendations, user=user_vertex)

@app.route('/game/<string:game_name>')
def game_description(game_name):
    global recommendations

    for game,_ in recommendations:
        if game.Name == game_name:
            break
    
    return render_template('game_description.html', game=game)

if __name__ == '__main__':
    app.run(debug=True)