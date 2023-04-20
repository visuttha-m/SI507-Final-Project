#########################################
##### Name: Visuttha Manthamkarn    #####
##### Uniqname: visuttha            #####
#########################################

from flask import Flask, render_template, request
import plotly.io as pio
from GameRecommendation import *

app = Flask(__name__)

if os.path.isfile('SteamGames.json') == False:

    if os.path.isfile('Appid.json'):
        AppID = ReadJSON('Appid.json')
    else:
        AppID = GatSteamAppID()
        WriteJSON('AppID.json',AppID)
    if os.path.isfile('GameDetails.json'):
        GameDetails = ReadJSON('GameDetails.json')
    else:
        GameDetails = GetSteamGameDetails(AppID)
        WriteJSON('GameDetails.json',GameDetails)
    
    WriteSteamGamesCSV('SteamGames.csv',GameDetails)
    CSVtoJson('GameDetails.csv', 'SteamGames.json')
    
GameList = ReadSteamGamesJSON('SteamGames.json')
recommendations = []

@app.route('/')
def index():
    '''Renders the index.html template, which is the main page of the web application.

    Parameters  
    ----------
    None
    Returns
    -------
    string
        The rendered HTML for the index.html template.
    '''
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    '''Handles the user's preferences submitted from the index.html form, calculates game recommendations,
    and renders the recommendations.html template with the recommendations.

    Parameters  
    ----------
    None
    Returns
    -------
    string
        The rendered HTML for the recommendations.html template.
    '''

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
    
    user_edge = list(game_graph.edges.values())[-1]
    fig = VisualizeGameGraph(user_edge)
    graph_filename = os.path.join('static', 'graph.html')
    pio.write_html(fig, file=graph_filename, auto_open=False)

    return render_template('recommendations.html', recommendations=recommendations, user=UserPreferences, graph_filename=graph_filename)

@app.route('/game/<string:game_name>')
def game_description(game_name):
    '''Renders the game_description.html template for a specific game, based on the game_name provided.
    
    Parameters  
    ----------
    game_name: string
        The name of the game for which to display the description.
    Returns
    -------
    string
        The rendered HTML for the game_description.html template.
    '''

    global recommendations

    for game,_ in recommendations:
        if game.Name == game_name:
            break
    
    return render_template('game_description.html', game=game)

if __name__ == '__main__':
    app.run(debug=True)