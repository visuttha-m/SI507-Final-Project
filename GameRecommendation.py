import csv
import json
import requests
import os
import time
from dateutil import parser
from bs4 import BeautifulSoup

class Game():
    '''
    Class Attributes
    ----------------
    None
    Instance Attributes
    -------------------
    GameID: string
        The game's ID.
    Name: string
        The game's name.
    Genres: string
        The game's genres, separated by commas.
    Free: bool
        Whether the game is free or not.
    Price: string
        The game's price
    Platform: string
        The platform(s) the game is available on (windows/mac/linux), separated by commas.
    Categories: string
        The game's categories, separated by commas.
    Description: string
        A detailed description of the game.
    Recommendations: int
        The number of recommendations the game has received.
    Rating: int
        The game's rating out of 100.
    ReleaseDate: string
        The game's release date
    Image: string
        The URL of the game's header image on Steam.
    '''
    def __init__(self, 
                GameID= None,
                Name= None,
                Genres= None,
                Free= None,
                Price= None,
                Platform= None,
                Categories= None,
                Description= None,
                Recommendations= 0,
                Rating= None,
                ReleaseDate= None
                ):
        self.GameID = GameID
        self.Name = Name
        self.Genres = Genres
        self.Free = True if Free == "TRUE" else False
        self.Price = Price
        self.Platform = Platform
        self.Categories = Categories
        self.Description = Description
        self.Recommendations = int(Recommendations) if Recommendations.isnumeric() else 0
        self.Rating = int(Rating) if Rating.isnumeric() else 0
        self.ReleaseDate = ReleaseDate
        self.Image = f"https://cdn.akamai.steamstatic.com/steam/apps/{self.GameID}/header.jpg"
    
class User:
    '''
    Class Attributes
    ----------------
    None
    Instance Attributes
    -------------------
    UserID: string
        The user's name.
    Genres: string
        The user's preferred genres, separated by commas.            
    Free: bool
        Whether the user prefers free games or not.
    Categories: string
        The user's preferred categories, separated by commas.
    Platform: string
        The user's preferred platform (windows/mac/linux).
    ReleaseYear: string
        The user's preferred release year.
    '''
    def __init__(self, 
                 UserID=None,
                 Genres=None,
                 Free=None,
                 Categories=None,
                 Platform=None,
                 ReleaseYear=None):
        self.UserID = UserID
        self.Genres = Genres
        self.Free = Free
        self.Categories = Categories
        self.Platform = Platform
        self.ReleaseYear = ReleaseYear

class Vertex:
    '''A class that represents a vertex in a graph.

    Class Attributes
    ----------------
    None
    Instance Attributes
    -------------------
    node: Game or User
        The game or user object that this vertex represents.
    name: string
        The name of the vertex (same as node).
    '''
    def __init__(self, node):
        self.node = node
        self.name = str(node)

class Graph:
    '''A class that represents a graph.

    Class Attributes
    ----------------
    None
    Instance Attributes
    -------------------
    node: list
        A list of Vertex objects representing the nodes in the graph.
    edges: dict
        A dictionary of edges in the graph. Each key is the name of a vertex
        and the corresponding value is a list of tuples. Each tuple contains
        a vertex and the weight of the edge connecting it to the key vertex.
    '''
    def __init__(self):
        self.nodes = []
        self.edges = {}

    def add_node(self, node):
        '''
        Parameters  
        ----------
        node:

        Returns
        -------
        None
        '''
        vertex = Vertex(node)
        self.nodes.append(vertex)
        self.edges[vertex.name] = []

    def add_edge(self, node1, node2, similarity, score):
        '''
        Parameters  
        ----------
        node1:

        node2:

        similarity:

        score:

        Returns
        -------
        None
        '''
        if similarity >= 0.5:  # only add edges for games with high similarity
            self.edges[node1.name].append((node2, score))
            self.edges[node2.name].append((node1, score))

    def get_recommendations(self, user_vertex, k=5):
        '''
        Parameters  
        ----------
        user_vertex:

        k:

        Returns
        -------
        list

        '''
        sorted_edges = sorted(self.edges[user_vertex.name], key=lambda x: x[1], reverse=True)
        top_k = [(edge[0].node, edge[1]) for edge in sorted_edges[:k]]
        return top_k

def ComputeSimilarity(node1, node2):
    '''Computes the similarity score between two games based on their genres 
    and categories.
    
    Parameters  
    ----------
    node1: Game or User
        The first Game or User object.
    node2: Game or User
        The second Game or User object.
    Returns
    -------
    float
        The similarity score between the two node.
    '''
    # Calculate genre similarity
    genres1 = set([genres.lower().strip() for genres in node1.Genres.split(',')])
    genres2 = set([genres.lower().strip() for genres in node2.Genres.split(',')])
    genre_similarity = len(genres1.intersection(genres2)) / len(genres1.union(genres2))

    # Calculate categories similarity
    categories1 = set([category.lower().strip() for category in node1.Categories.split(',')])
    categories2 = set([category.lower().strip() for category in node2.Categories.split(',')])
    categories_similarity = len(categories1.intersection(categories2)) / len(categories1.union(categories2))

    # Combine similarities using weights (you can adjust the weights to change their importance)
    total_similarity = (
          0.7 * genre_similarity
        + 0.3 * categories_similarity
    )

    return total_similarity

def GatSteamAppID():
    '''Retrieves a list of AppIDs for all application on Steam.

    Parameters  
    ----------
    None
    Returns
    -------
    list
        A list of dictionaries, where each dictionary represents an application
        and contains the keys 'appid' (the application's ID) and 'name
    '''
    url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/?key=8359C2E269BEB7677433D94B572C812A&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        AppID = json.loads(response.content)['applist']['apps']
        AppID.sort(key=lambda x: x['appid'])
    else:
        print('Failed to retrieve data')
        AppID = []
    return AppID

def GetSteamGameDetails(AppID):
    '''Retrieves details for each game on Steam based on its AppIDs.

    Parameters  
    ----------
    AppID: dict
         A list of dictionaries containing the AppIDs for each application on Steam.
    Returns
    -------
    list
        A list of dictionaries containing details for each game on Steam.
    '''
    GameDetails = []
    max_retries = 5
    base_delay = 5 

    exclude_words = {'demo', 'dlc', 'vr', 'soundtrack', 'ost', 'bundle', 'episode', 
                     'mod', 'skin', 'theme', 'trailer', 'movie', 'book', 'comic'}

    for app in AppID:
        id = app['appid']
        name = app['name']

        if exclude_words.intersection(set(name.lower().split())):
            continue

        url = f"http://store.steampowered.com/api/appdetails?appids={id}"
        retries = 0
        success = False

        while retries < max_retries and not success:
            response = requests.get(url)

            if response.status_code == 200:
                AppDetails = json.loads(response.content)[f'{id}']
                if AppDetails['success'] and AppDetails['data']['type'] == 'game':
                    GameDetails.append(AppDetails['data'])
                success = True
            elif response.status_code == 429:
                print(f"Rate limited. Retrying in {base_delay * (2 ** retries)} seconds...")
                time.sleep(base_delay * (2 ** retries))
                retries += 1
            else:
                print(f"Failed to retrieve data. Response status code: {response.status_code}")
                retries += 1

    return GameDetails

def WriteJSON(filename, data):
    '''Writes data to a JSON file.

    Parameters  
    ----------
    filename: string
        The name of the JSON file to write to.
    data: list
        The data to write to the file.
    Returns
    -------
    None 
    '''
    DataJSON = json.dumps(data, indent = 4)
    with open(filename,'w') as f:
        f.write(DataJSON)

def ReadJSON(filename):
    ''' Reads a JSON file and returns its contents as a dictionary.

    Parameters  
    ----------
    filename: string
        The name of the JSON file to read.
    Returns
    -------
    dict
        The contents of the JSON file as a dictionary.
    '''
    with open(filename,'r') as f:
        DataJSON = json.load(f)
    return DataJSON

def GetRating(game):
    '''Retrieves the Metacritic score for a game using web scraping.

    Parameters  
    ----------
    game: string
        The name of the game to retrieve the score for.
    Returns
    -------
    float
        The Metacritic score for the game, or None if it cannot be retrieved.
    '''
    game_name_encoded = requests.utils.quote(game)
    url = f"https://www.metacritic.com/search/game/{game_name_encoded}/results"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0"}
    response = requests.get(url, headers=headers)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    result = soup.find('li', class_='result')
    if result is None:
        return None

    title_link = result.find('h3', class_='product_title').find('a', href=True)
    if title_link is None:
        return None

    link = title_link['href']
    response = requests.get(f"https://www.metacritic.com{link}", headers=headers)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    metascore = soup.find('div', class_='metascore_w')

    if metascore is None:
        return None

    rating = int(metascore.text)

    return rating

def WriteGameDetailsCSV(filename, data):
    '''Writes the Steam game details to a CSV file.

    Parameters  
    ----------
    filename: string
        The name of the CSV file to write to.
    data: list
        A list of dictionaries containing the game details.
    Returns
    -------
    None
    '''
    with open(filename, 'w', newline='') as f:
        fieldnames = [
            'GameID',
            'Name',
            'Genres',
            'Free',
            'Price',
            'Platform',
            'Categories',
            'Description',
            'Recommendations',
            'Rating',
            'ReleaseDate',
            ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for game in data:
            rating = game.get('metacritic', {}).get('score', None)
            if not rating:
                rating = GetRating(game.get('name', None))
                if not rating:
                    continue
            print(game.get('name', None))
            writer.writerow(
                {
                    'GameID':           game.get('steam_appid', None),
                    'Name':             game.get('name', None),
                    'Genres':           ', '.join([genre['description'] for genre in game.get('genres', [])]),
                    'Free':             game.get('is_free', None),
                    'Price':            game.get('price_overview', {}).get('final_formatted', None),
                    'Platform':         ', '.join(game.get('platforms', {}).keys()),
                    'Categories':       ', '.join([category['description'] for category in game.get('categories', [])]),
                    'Description':      game.get('detailed_description', None),
                    'Recommendations':  game.get('recommendations', {}).get('total', None),
                    'Rating':           rating,
                    'ReleaseDate':      game.get('release_date', {}).get('date', None),
                }
            )

def ReadGameDetailsCSV(filename):
    '''Reads a CSV file containing game details and returns a list of Game objects.

    Parameters  
    ----------
    filename: string
        The name of the CSV file to read.
    Returns
    -------
    list
        A list of Game objects.
    '''    
    games = []
    with open(filename, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            game = Game(
                GameID= row['GameID'],
                Name= row['Name'],
                Genres= row['Genres'],
                Free= row['Free'],
                Price= row['Price'],
                Platform= row['Platform'],
                Categories= row['Categories'],
                Description= row['Description'],
                Recommendations= row['Recommendations'],
                Rating= row['Rating'],
                ReleaseDate= row['ReleaseDate']
            )
            games.append(game)
    return games

def AskUserPreferences():
    '''Asks the user for their game preferences and returns a User object 
    containing their preferences.

    Parameters  
    ----------
    None
    Returns
    -------
    User
        A User object containing the user's preferences.
    '''
    user = input("Enter your name: ")
    genres = input("Enter your preferred genres (separated by commas): ").strip()
    free = input("Do you prefer free games? (Yes/No): ").strip().lower() == "yes"
    categories = input("Enter your preferred categories (separated by commas): ").strip()
    platform = input("Enter your preferred platform (windows/mac/linux): ").strip().lower()
    release_year = int(input("Enter your preferred release year: ").strip())

    return User(
        UserID=user,
        Genres=genres,
        Free=free,
        Categories=categories,
        Platform=platform,
        ReleaseYear=release_year,
    )

def FilterGamesByPreferences(game_list, user_preferences):
    '''Filters games based on user preferences.

    Parameters  
    ----------
    game_list: list
        A list of Game objects to filter.
    user_preferences: User
        A User object representing the user's preferences.
    Returns
    -------
    list
        A filtered list of Game objects.
    '''
    filtered_games = []
    for game in game_list:
        if game.Free == user_preferences.Free and user_preferences.Platform in game.Platform:
            try:
                release_year = parser.parse(game.ReleaseDate).year
                if release_year == user_preferences.ReleaseYear:
                    filtered_games.append(game)
            except:
                pass

    return filtered_games

if __name__ == '__main__':
    
    if os.path.isfile('GameDetails.csv') == False:

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
        
        WriteGameDetailsCSV('GameDetails.csv',GameDetails)
    
    GameList = ReadGameDetailsCSV('GameDetails.csv')

    while True:

        UserPreferences = AskUserPreferences()

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
                game_graph.add_edge(user_vertex, game_vertex, similarity, score)

        recommendations = game_graph.get_recommendations(user_vertex, k=5)

        print(f"Top 5 recommended games for {UserPreferences.UserID}:")
        for idx, (game, score) in enumerate(recommendations):
            print(f"{idx + 1}. {game.Name} (Score: {score:.2f})")
            soup = BeautifulSoup(game.Description, "html.parser")
            print(soup.get_text(separator='\n'))
            print()