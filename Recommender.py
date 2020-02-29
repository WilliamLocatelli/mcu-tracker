""" Creates a GUI which allows user to specify which films they have seen and which films they
would like to see, and gives them recommendations as to which movies they should watch in between.
"""
from MarvelTracker import Movie
from graphics import *
import csv

EDGES = []
MOVIES = {}
WIDTH = 1200
HEIGHT = 600

HOVER_COLOR = color_rgb(76, 237, 78)
SELECTED_COLOR = color_rgb(31, 222, 34)
CHOSEN_COLOR = color_rgb(18, 173, 206)
PARENTS_COLOR = color_rgb(18, 206, 18)
CHILDREN_COLOR = color_rgb(206, 191, 18)

# takes in a CSV file, outputs a tuple containing a list of movies and a list of edges
def import_weighted_from_csv(file="MCUphase1to3-weighted.csv"):
    # put all the rows of the csv file into a list
    csv_rows = []
    with open(file, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            csv_rows.append(row)
    title_list = csv_rows[0]
    # create movie objects
    all_movies = {}
    i = 1  # skip the title row
    movie_count = len(csv_rows)
    while i < movie_count:
        row = csv_rows[i]
        this_movie = Movie(row[0], series=row[1])
        this_movie.prevs_selected = True
        all_movies[row[0]] = this_movie
        i += 1
    # create edges
    all_edges = []
    i = 1  # skip the title row
    while i < movie_count:
        row = csv_rows[i]
        i2 = 2  # skip the series column
        while i2 < len(row):
            weight = row[i2]
            if len(weight) > 0 and weight != "0":
                # csv_rows[i] tells you what movies i comes from, so the edges need to
                # start at the movie it came from (found in the title list[i2] and end at i
                this_edge = WeightedEdge(title_list[i2], row[0], float(weight))
                all_edges.append(this_edge)
            i2 += 1
        i += 1

    global EDGES
    global MOVIES
    EDGES = all_edges
    MOVIES = all_movies


# find the n best other movies to watch if you've watched the parents and want to watch the children
def find_best_subgraph(parents, children, n):
    edges = EDGES.copy()
    # if the edge ends at a parent or starts at a child, don't include it
    for edge in EDGES: # iterate through OTHER list so we don't mess up our iteration
        if MOVIES[edge.v2] in parents:
            edges.remove(edge)
        elif MOVIES[edge.v1] in children:
            edges.remove(edge)
    included = parents + children
    excluded = []
    for movie in MOVIES.values():
        if movie not in included:
            excluded.append(movie)
    return subgraph_helper2(excluded, included, edges, n)


# this version works, but is sometimes wrong.
def subgraph_helper(excluded, included, edges, n):
    if n == 0: return included
    max_weight = 0
    max_movie = None
    for movie in excluded:
        included_copy = included.copy()
        included_copy.append(movie)
        weight = subgraph_weight(included_copy, edges)
        if weight > max_weight:
            max_weight = weight
            max_movie = movie
    excluded.remove(max_movie)
    included.append(max_movie)
    return subgraph_helper(excluded, included, edges, n-1)

# this version doesn't work at all.
def subgraph_helper2(excluded, included, edges, n):
    if n == 0: return included
    max_weight = 0
    best_graph = None
    for movie in excluded:
        included_copy = included.copy()
        included_copy.append(movie)
        excluded.remove(movie)
        best_graph_next_level = subgraph_helper2(excluded, included_copy, edges, n-1)
        weight = subgraph_weight(best_graph_next_level, edges)
        if weight > max_weight:
            max_weight = weight
            best_graph = best_graph_next_level
    print(str(max_weight))
    return best_graph


# computes and returns the weight of the subgraph
def subgraph_weight(subgraph, edges):
    weight = 0
    for edge in edges:
        if MOVIES[edge.v1] in subgraph and MOVIES[edge.v2] in subgraph:
            weight += edge.weight
    return weight

# draws the window
def draw_window():
    # sort each movie by series
    series = {}
    for movie in MOVIES.values():
        if movie.series not in series:
            series[movie.series] = [movie]
        else:
            series[movie.series].append(movie)

    x_pos = 5
    # set position of each movie
    for movie_series in series:
        y_pos = 5
        for movie in series[movie_series]:
            point = Point(x_pos, y_pos)
            movie.set_point(point, height=8, width=14)
            y_pos = y_pos + 8*1.5
        x_pos = x_pos + 10*1.5

    # draw window
    win = GraphWin(title="Recommender", width=WIDTH, height=HEIGHT, autoflush=False)
    win.setCoords(0, 180*HEIGHT/WIDTH, 180, 0)
    win.bind('<Motion>', motion)
    for movie in MOVIES.values():
        movie.draw(win)
    next_button = Rectangle(Point(180, 0), Point(175, 5))
    next_button.setFill("red")
    next_button.draw(win)
    update()
    return win

# runs the main program
def run_program(win):
    parents = []
    selected = parents
    children = []
    input_box = Entry(Point(WIDTH/8, HEIGHT/8), 10)
    input_box.setText("1")
    while True:
        p = win.getMouse()
        if p.getX() > 175 and p.getY() < 5:
            if selected == parents:
                selected = children
                for movie in Movie.open:
                    if movie in parents:
                        Movie.open.remove(movie)
                        movie.my_square.setFill("gray")
            elif len(Movie.open) > 0:
                Movie.open.clear()
                input_box.draw(win)
                update()
            else:
                subgraph = find_best_subgraph(parents, children, int(input_box.getText()))
                input_box.undraw()
                for movie in MOVIES.values():
                    if movie in subgraph:
                        if movie in parents:
                            movie.my_square.setFill(PARENTS_COLOR)
                        elif movie in children:
                            movie.my_square.setFill(CHILDREN_COLOR)
                        else:
                            movie.my_square.setFill(CHOSEN_COLOR)
                    else:
                        movie.my_square.setFill("gray")
        for movie in Movie.open:
            if movie.p1.getX() < p.getX() < movie.p2.getX() and movie.p1.getY() < p.getY() < movie.p2.getY():
                if not movie.selected:
                    selected.append(movie)
                    movie.selected = True
                    movie.my_square.setFill(SELECTED_COLOR)
                else:
                    movie.my_square.setFill(HOVER_COLOR)
                    selected.remove(movie)
                    movie.selected = False


# tracks motion
def motion(event):
    x = 180*event.x/WIDTH
    y = 180*event.y/WIDTH
    # if we hover over an open movie, show which movies will be unlocked if we watch this movie.
    for movie in Movie.open:
        if movie.p1.getX() < x < movie.p2.getX() and movie.p1.getY() < y < movie.p2.getY():
            movie.my_square.setFill(HOVER_COLOR)
        # if we are not hovering over this movie, reset the colors back to normal
        else:
            if movie.selected:
                movie.my_square.setFill(SELECTED_COLOR)
            else:
                movie.my_square.setFill("white")


# class for edges of graph
class WeightedEdge:

    def __init__(self, v1, v2, weight):
        self.v1 = v1
        self.v2 = v2
        self.weight = weight


if __name__ == '__main__':
    import_weighted_from_csv()
    win = draw_window()
    run_program(win)
