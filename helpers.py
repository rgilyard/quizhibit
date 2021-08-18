from cs50 import SQL
from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///met.db")

# Searches list works for favorites, returns list true or false if favorites exist (in order of list, not favs)
def compFavs(userId, works):
    # Make list to record whether a picture is favorited
    isFav = []
    # Get list of favorites of user
    favorites = db.execute("SELECT * FROM favorites WHERE username=?;", userId)
    # Compare display to favorites so favorited pictures will have the red heart
    matchFound = False # True when match is found
    for item in works:
        for favorite in favorites:
            if item["objectId"] == favorite["objectId"]:
                matchFound = True
                isFav.append(True)
        if matchFound == False:
            isFav.append(False)
        matchFound = False
    # return list of favorites to be displayed on page
    return isFav


# Arguments should be in order of difficulty (0 for all),
# department (default all), category (default all),
# then keyword (keyword optional)
def searchWorks(*args):
    # Assign difficulty variable
    difficulty = args[0]
    # Start beginning of search string
    searchString = " percentCorrect>=?"
    # Start list of search arguments
    argList = []
    argList.append(difficulty)

    # If department is specified
    if args[1] != "all":
        # Assign deparment variable
        department = args[1]
        # Add onto the search string
        searchString += " AND department=?"
        # Append list of search arguments
        argList.append(department)
    # If category is specified
    if args[2] != "all":
        # Assign category variable
        category = args[2]
        # Add onto the search string
        searchString += " AND classification=?"
        # Append list of search arguments
        argList.append(category)
    # If there is a keyword search
    if len(args) > 3 and args[3] != "":
        # Assign keyword to variable
        keyword = "%" + args[3] + "%"
        # Finish search string
        searchString = "SELECT * FROM works WHERE" + searchString + " AND title LIKE? OR" +\
                       searchString + " AND artist LIKE?;"
        argList.append(keyword)
        # Search database and return list
        rows = db.execute(searchString, *argList, *argList)
        return rows

    # Finish search string
    searchString = "SELECT * FROM works WHERE" + searchString + ";"
    # Search database and return list
    rows = db.execute(searchString, *argList)
    return rows


# Arguments should be in order of difficulty (0 for all),
# department (default all), category (default all), user_id,
# then keyword (keyword optional)
def searchFavs(*args):
    # Assign difficulty variable
    difficulty = args[0]
    # Start beginning of search string
    searchString = " percentCorrect>=?"
    # Start list of search arguments
    argList = []
    argList.append(difficulty)

    # If department is specified
    if args[1] != "all":
        # Assign deparment variable
        department = args[1]
        # Add onto the search string
        searchString += " AND department=?"
        # Append list of search arguments
        argList.append(department)
    # If category is specified
    if args[2] != "all":
        # Assign category variable
        category = args[2]
        # Add onto the search string
        searchString += " AND classification=?"
        # Append list of search arguments
        argList.append(category)
    # If there is a keyword search
    if len(args) > 4 and args[4] != "":
        # Assign keyword to variable
        keyword = "%" + args[4] + "%"
        # Add favorites search stuff
        searchString += " AND objectId IN(SELECT objectId FROM favorites WHERE username=?)"
        # Finish search string
        searchString = "SELECT * FROM works WHERE" + searchString + " AND title LIKE? OR" +\
                       searchString + " AND artist LIKE?;"
        # Append user_id and keyword to argument list
        argList.append(args[3])
        argList.append(keyword)
        # Search database and return list
        rows = db.execute(searchString, *argList, *argList)
        return rows

    # Add favorites search stuff
    searchString += " AND objectId IN(SELECT objectId FROM favorites WHERE username=?)"
    argList.append(args[3])
    # Finish search string
    searchString = "SELECT * FROM works WHERE" + searchString + ";"
    # Search database and return list
    rows = db.execute(searchString, *argList)
    return rows


#________________________________________________________________________________
# Taken from CS50 finance
# Log in decorator
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function
# End CS50 Code
#_________________________________________________________________________________