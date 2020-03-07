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
GRAPHS_CHECKED = 0
NUM_CHOSEN = 0
HOVER_COLOR = color_rgb(76, 237, 78)
SELECTED_COLOR = color_rgb(31, 222, 34)
CHOSEN_COLOR = color_rgb(18, 173, 206)
PARENTS_COLOR = color_rgb(83, 116, 81)
CHILDREN_COLOR = color_rgb(206, 191, 18)
BUTTON_COLOR = color_rgb(210, 222, 31)
INSTRUCTION_TEXT = None
CHANGED = False
NUM_TIES = 0
NEXT_TEXT = None
REC_TEXT = None
BUTTONS = []

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
    return brute_force_subgraph_helper(excluded, included, edges, n)


# this version doesn't consider all possibilities, but is fast.
def naive_subgraph_helper(excluded, included, edges, n):
    if n == 0:
        subgraph = included.copy()
        return subgraph
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
    return naive_subgraph_helper(excluded, included, edges, n-1)


# this version considers every option, but is slow.
def brute_force_subgraph_helper(excluded, included, edges, n):
    global GRAPHS_CHECKED
    best_graphs = []
    if n == 0:
        GRAPHS_CHECKED += 1
        subgraph = included.copy()
        return [subgraph]
    max_weight = 0
    #best_graph = included
    excluded_copy = excluded.copy()
    included_copy = included.copy()
    while len(excluded_copy) > n-1:
        movie = excluded_copy[0]
        included_copy.append(movie)
        excluded_copy.remove(movie)
        best_graph_next_level = []
        best_graph_next_level += brute_force_subgraph_helper(excluded_copy, included_copy, edges, n-1)
        weight = subgraph_weight(best_graph_next_level[0], edges)
        if weight > max_weight:
            max_weight = weight
            best_graphs = best_graph_next_level.copy()
        elif weight == max_weight:
            best_graphs += best_graph_next_level
        #excluded_copy.append(movie)
        included_copy.remove(movie)
    #print(str(max_weight))
    return best_graphs


def tie_breaker(best_graphs, excluded, edges):
    if len(best_graphs) == 1:
        return best_graphs[0]
    else:
        print("number of equally good choices: " + str(len(best_graphs)))
        best_graph = None
        max_weight = 0
        # find best of bests
        for graph in best_graphs:
            # create new list of excluded movies
            excluded_copy = excluded.copy()
            for movie in graph:
                if movie in excluded:
                    excluded_copy.remove(movie)
            best_plus_one = tie_breaker(brute_force_subgraph_helper(excluded_copy, graph, edges, 1), excluded, edges)
            weight = subgraph_weight(best_plus_one, edges)
            if weight > max_weight:
                max_weight = weight
                best_graph = graph
        # choose the subgraph of highest weight
        return best_graph


# find the n best other movies to watch if you've watched the parents and want to watch the children
def find_best_subgraph_prev_tree(parents, children, n):
    # if n + len(parents) + len(children) > len(MOVIES.values()):  # edge case
        # return MOVIES.values()
    edges = []
    included = parents + children
    nodes = children.copy()
    prev_tree(nodes, parents, edges)  # fill nodes and edges with all parents of nodes and edges between those nodes
    for parent in parents:
        nodes.append(parent)
    most_nodes = len(nodes) - len(children) - len(parents)
    excluded = []
    if most_nodes < n:  # if most_nodes is less than n, include all parents plus n
        return nodes # due to this rule, the next 4 lines are actually never used
    else:
        for movie in nodes:
            if movie not in included:
                excluded.append(movie)
    for edge in EDGES:  # iterate through OTHER list so we don't mess up our iteration
        if MOVIES[edge.v2] in parents and edge in edges:
            edges.remove(edge)
    best_graphs = brute_force_subgraph_helper(excluded, included, edges, n)
    return tie_breaker(best_graphs, excluded, edges)


def prev_tree(nodes, parents, edges):
    for edge in EDGES:
        for movie in nodes:
            if MOVIES[edge.v2] == movie:
                if edge not in edges:
                    edges.append(edge)
                movie1 = MOVIES[edge.v1]
                # if we already added this one, we don't need to do it again
                # if we already watched this one, its prevs aren't relevant.
                if movie1 not in nodes and movie1 not in parents:
                    nodes.append(movie1)
                    prev_tree(nodes, parents, edges)


# computes and returns the weight of the subgraph
def subgraph_weight(subgraph, edges):
    weight = 0
    for edge in edges:
        if MOVIES[edge.v1] in subgraph and MOVIES[edge.v2] in subgraph:
            weight += edge.weight
    return weight


def watch_order(parents, subgraph):
    order = []
    for movie in MOVIES:
        if MOVIES[movie] in subgraph and not MOVIES[movie] in parents:
            order.append(movie)
    return order


# draws the window
def draw_window():
    # sort each movie by series
    series = {}
    for movie in MOVIES.values():
        if movie.series not in series:
            series[movie.series] = [movie]
        else:
            series[movie.series].append(movie)

    x_pos = 3
    # set position of each movie
    for movie_series in series:
        y_pos = 5
        for movie in series[movie_series]:
            point = Point(x_pos, y_pos)
            movie.set_point(point, height=8, width=14.5)
            y_pos = y_pos + 8*1.5
        x_pos = x_pos + 14.5*1.1
    '''x_pos = 5
    y_pos = 5
    # set position of each movie
    for movie in MOVIES.values():
        point = Point(x_pos, y_pos)
        movie.set_point(point, height=8, width=14)
        x_pos = x_pos + 10 * 1.5
        if x_pos > 160:
            y_pos = y_pos + 8 * 1.5
            x_pos = 5'''

    # draw window
    win = GraphWin(title="Recommender", width=WIDTH, height=HEIGHT, autoflush=False)
    win.setCoords(0, 180*HEIGHT/WIDTH, 180, 0)
    win.bind('<Motion>', motion)
    for movie in MOVIES.values():
        movie.draw(win)

    next_button = Rectangle(Point(80, 60), Point(90, 65))
    next_button.setFill(BUTTON_COLOR)
    next_text = Text(next_button.getCenter(), text="Next")
    next_button.draw(win)
    BUTTONS.append([next_button, next_text])
    next_text.draw(win)

    prev_button = Rectangle(Point(60, 60), Point(70, 65))
    prev_button.setFill(BUTTON_COLOR)
    prev_text = Text(prev_button.getCenter(), text="Back")
    BUTTONS.append([prev_button, prev_text])

    global INSTRUCTION_TEXT
    INSTRUCTION_TEXT = Text(Point(50, 70), text="Select the movies you have already seen.")
    INSTRUCTION_TEXT.setSize(20)
    INSTRUCTION_TEXT.draw(win)
    global REC_TEXT
    REC_TEXT = Text(Point(120, 50), text="")
    update()
    return win


# runs the main program
def run_program(win):
    global GRAPHS_CHECKED
    global NUM_TIES
    global REC_TEXT
    global CHANGED
    parents = []
    selected = parents
    children = []
    subgraph = []
    input_box = Entry(Point(INSTRUCTION_TEXT.getAnchor().getX() + 50, INSTRUCTION_TEXT.getAnchor().getY()), 10)
    input_box.setFill("white")
    input_box.setText("1")
    while True:
        p = win.getMouse()
        # Next Button
        if 80 < p.getX() < 90 and 60 < p.getY() < 65:
            # stage 1-> stage 2
            if INSTRUCTION_TEXT.getText() == "Select the movies you have already seen.":
                selected = children
                for movie in parents:
                    Movie.open.remove(movie)
                    movie.my_square.setFill("gray")
                INSTRUCTION_TEXT.setText("Select the movies you would like to see.")
                BUTTONS[1][0].draw(win) #draw the back button
                BUTTONS[1][1].draw(win)
            # stage 2-> stage 3
            elif len(Movie.open) > 0:
                if len(children) == 0:
                    INSTRUCTION_TEXT.setText("You must select at least 1 movie you would like to see.")
                else:
                    Movie.open.clear()
                    for movie in children:
                        movie.my_square.setFill(CHILDREN_COLOR)
                    INSTRUCTION_TEXT.setText("How many additional movies are you willing to watch?")
                    input_box.draw(win)
            #stage 3->stage 4
            elif not INSTRUCTION_TEXT.getText() == "Here are your recommendations!":
                global NUM_CHOSEN
                if not str.isdigit(input_box.getText()):
                    input_box.setText("")
                    INSTRUCTION_TEXT.setText("How many additional movies are you willing to watch?\nOnly numbers are allowed.")
                else:
                    if CHANGED or not NUM_CHOSEN == int(input_box.getText()):
                        CHANGED = False
                        NUM_CHOSEN = int(input_box.getText())
                        subgraph = find_best_subgraph_prev_tree(parents, children, NUM_CHOSEN)
                        order = watch_order(parents, subgraph)
                        #watched_string = "Already Watched:\n" + "\n".join(t.name for t in parents)
                        rec_string = "\nWatch Order:\n" + "\n\n".join(order)
                        REC_TEXT.setText(rec_string)
                        REC_TEXT.undraw()
                        REC_TEXT.draw(win)
                    for movie in MOVIES.values():
                        if movie not in parents and movie not in children:
                            if movie in subgraph:
                                movie.my_square.setFill(CHOSEN_COLOR)
                            else:
                                movie.my_square.setFill("white")
                    input_box.undraw()
                    INSTRUCTION_TEXT.setText("Here are your recommendations!")
                    print("graphs checked: " + str(GRAPHS_CHECKED))

                    BUTTONS[0][0].undraw()
                    BUTTONS[0][1].undraw()
                    #NEXT_TEXT.setText("Reset")
        #back button
        if 60 < p.getX() < 70 and 60 < p.getY() < 65:
            # stage 4-->stage 3
            if INSTRUCTION_TEXT.getText() == "Here are your recommendations!":
                GRAPHS_CHECKED = 0
                INSTRUCTION_TEXT.setText("How many additional movies are you willing to watch?")
                BUTTONS[0][0].draw(win)
                BUTTONS[0][1].draw(win)
                input_box.draw(win)
            # stage 3--> stage 2
            elif len(Movie.open) == 0:
                INSTRUCTION_TEXT.setText("Select the movies you would like to see.")
                input_box.undraw()
                selected = children
                for movie in MOVIES.values():
                    if movie not in parents:
                        Movie.open.append(movie)
                        if movie not in children:
                            movie.my_square.setFill("white")
                        else:
                            movie.my_square.setFill(SELECTED_COLOR)
            # stage 2--> stage 1 (disallowing repetition)
            elif len(children) > 0:
                INSTRUCTION_TEXT.setText("Select the movies you have already seen.")
                selected = parents
                for movie in MOVIES.values():
                    if movie not in Movie.open: Movie.open.append(movie)
                    if movie in children:
                        movie.selected = False
                        movie.my_square.setFill("white")
                    elif movie in parents:
                        movie.selected = True
                        movie.my_square.setFill(SELECTED_COLOR)
                children = []
                BUTTONS[1][0].undraw() #undraw the back button
                BUTTONS[1][1].undraw()
        for movie in Movie.open:
            if movie.p1.getX() < p.getX() < movie.p2.getX() and movie.p1.getY() < p.getY() < movie.p2.getY():
                CHANGED = True
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
    for button in BUTTONS:
        button = button[0]
        if button.p1.getX() < x < button.p2.getX() and button.p1.getY() < y < button.p2.getY():
            button.setFill(HOVER_COLOR)
        # if we are not hovering over this movie, reset the colors back to normal
        else:
            button.setFill(BUTTON_COLOR)


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
