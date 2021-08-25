import json, urllib.request, random, math, os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import mkdtemp
from helpers import compFavs, login_required, searchWorks, searchFavs

# Configure application
app = Flask(__name__)

# https://collectionapi.metmuseum.org/public/collection/v1/objects/[objectID]
# ^This url to search for a artwork manually
#__________________________________________________________________________________________________________________________
# These lines copied from cs50's finance problem set distro code

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#  Read the secret key from config variables
secret_key_value = os.environ.get('SECRET_KEY', None)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///met.db")

# End cs50 code
#__________________________________________________________________________________________________________________________

# Seed random number
random.seed()

@app.route("/", methods=["GET", "POST"])
def index():
    # If reloading the page because a user favorited a picure
    if request.form.get("favorite") == 'true':
        # Get data from results page to re-render template
        pictures = eval(request.form.get("pictures"))
        quizAverage = float(request.form.get("quizAverage"))
        name = request.form.get("name")

        # Get objectId of new favorite picture
        picture = request.form.get("newFav")
        # Add picture to favorites
        db.execute("INSERT INTO favorites (username, objectId) VALUES (?, ?);", session["user_id"], picture)
        # Increment numFavs for picture
        numFavsList = db.execute("SELECT numFavs FROM works WHERE objectId=?;", picture)
        numFavs = numFavsList[0]["numFavs"]
        numFavs += 1
        db.execute("UPDATE works SET numFavs=? WHERE objectId=?;", numFavs, picture)

        # Get bool list of when a picture is favorited
        isFav = compFavs(session["user_id"], pictures)

        # Reload results page
        return render_template("index.html", pictures=pictures, name=name, quizAverage=quizAverage, isFav=isFav)

    # If reloading the page because a user UNfavorited a picure
    if request.form.get("unFavorite") == 'true':
        # Get data from results page to re-render template
        pictures = eval(request.form.get("pictures"))
        quizAverage = float(request.form.get("quizAverage"))
        name = request.form.get("name")

        # Get objectId of picture to un-favorite
        picture = request.form.get("unFav")
        # Delete picture from favorites
        db.execute("DELETE FROM favorites WHERE username=? AND objectId=?;", session["user_id"], picture)
        # Decrement numFavs for picture
        numFavsList = db.execute("SELECT numFavs FROM works WHERE objectId=?;", picture)
        numFavs = numFavsList[0]["numFavs"]
        numFavs -= 1
        db.execute("UPDATE works SET numFavs=? WHERE objectId=?;", numFavs, picture)

        # Get bool list of when a picture is favorited
        isFav = compFavs(session["user_id"], pictures)

        # Reload results page
        return render_template("index.html", pictures=pictures, name=name, quizAverage=quizAverage, isFav=isFav)

    # Pick six random pictures for homepage
    rows = db.execute("SELECT * FROM works;")
    pictures = random.sample(rows, 6)

    # If user is signed in
    if "user_id" in session:
        # Get user name
        nameList = db.execute("SELECT username FROM users WHERE id=?;", session["user_id"])
        name = nameList[0]["username"]

        # Get bool list of when a picture is favorited
        isFav = compFavs(session["user_id"], pictures)

        # Get quiz records for user
        quizAverageList = db.execute("SELECT numGuessed, numCorrect FROM users WHERE id=?;", session["user_id"])
        # If they have taken the quiz
        if quizAverageList[0]["numGuessed"] != 0:
            # Calculate user's average quiz score
            quizAverage = float(quizAverageList[0]["numCorrect"] * 100) / quizAverageList[0]["numGuessed"]
            # Format quiz average
            quizAverage = round(quizAverage, 2)
            # Display quiz score on homepage
            return render_template("index.html", pictures=pictures, name=name, quizAverage=quizAverage, isFav=isFav)

        return render_template("index.html", pictures=pictures, name=name, quizAverage=0.0, isFav=isFav)

    return render_template("index.html", pictures=pictures)

# Sets up quiz pictures and scrambles answers, sends through to quiz template
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        if request.form.get("favoriteQuiz") == 'true':
            # Get user's favorites
            rows = db.execute("SELECT * FROM works WHERE objectID IN(SELECT objectId FROM favorites WHERE username=?);", session["user_id"])
            # width percentage of pictures is dictated by gridSize
            gridSize = int(request.form.get("gridSize"))
            width = 100 / gridSize
            # number of matches is dictated by gridSize
            numMatches = gridSize * gridSize

            # Number of rows so we can make there are enough to fit gridSize
            numRows = len(rows)
            # If there are not enough matches to populate the quiz grid
            if numRows < numMatches:
                # Warn user that their criteria were too strict
                alert = "Not enough artworks match your criteria to generate a quiz of that size. Please choose different settings."
                # Get departments to pass to settings
                departments = db.execute("SELECT department FROM works GROUP BY department;")
                # Get classifications to pass to settings
                categories = db.execute("SELECT classification FROM works GROUP BY classification;")
                return render_template("settings.html", alert=alert, departments=departments, categories=categories)
            else:
                # Copy random matches to list
                matches = random.sample(rows, numMatches)

            # Copy then shuffle matcheslist so we can have pictures display in a difference order than the answers
            mixes = matches.copy()
            random.shuffle(matches)
            return render_template("quiz.html", matches=matches, mixes=mixes, numMatches=numMatches, width=width)


        # Get data from quiz settings form
        department = request.form.get("department")
        category = request.form.get("category")
        difficulty = float(request.form.get("difficulty"))
        gridSize = int(request.form.get("gridSize"))

        # width percentage of pictures is dictated by gridSize
        width = 100 / gridSize
        # number of matches is dictated by gridSize
        numMatches = gridSize * gridSize

        # Find works that fit criteria
        rows = searchWorks(difficulty, department, category)

        # Number of rows so we can make there are enough to fit gridSize
        numRows = len(rows)
        # If there are not enough matches to populate the quiz grid
        if numRows < numMatches:
            # Warn user that their criteria were too strict
            alert = "Not enough artworks match your criteria to generate a quiz of that size. Please choose different settings."

            # Get departments to pass to settings
            departments = db.execute("SELECT department FROM works GROUP BY department;")
            # Get classifications to pass to settings
            categories = db.execute("SELECT classification FROM works GROUP BY classification;")
            return render_template("settings.html", alert=alert, departments=departments, categories=categories)
        else:
            # Copy random matches to list
            matches = random.sample(rows, numMatches)

        # Copy then shuffle matcheslist so we can have pictures display in a difference order than the answers
        mixes = matches.copy()
        random.shuffle(matches)
        return render_template("quiz.html", matches=matches, mixes=mixes, numMatches=numMatches, width=width)

    else:
        # Get departments to pass to settings
        departments = db.execute("SELECT department FROM works GROUP BY department;")
        # Get classifications to pass to settings
        categories = db.execute("SELECT classification FROM works GROUP BY classification;")
        return render_template("settings.html", departments=departments, categories=categories)


@app.route("/results", methods=["POST"])
def results():
    # If reloading the page because a user favorited a picure
    if request.form.get("favorite") == 'true':
        # Get data from results page to re-render template
        keyRows = eval(request.form.get("keyRows"))
        answerRows = eval(request.form.get("answerRows"))
        results = eval(request.form.get("results"))
        width = float(request.form.get("width"))
        numMatches = int(request.form.get("numMatches"))
        numCorrect = request.form.get("numCorrect")
        quizPercentCorrect = request.form.get("quizPercentCorrect")

        # Get objectId of new favorite picture
        picture = request.form.get("newFav")
        # Add picture to favorites
        db.execute("INSERT INTO favorites (username, objectId) VALUES (?, ?);", session["user_id"], picture)
        # Increment numFavs for picture
        numFavsList = db.execute("SELECT numFavs FROM works WHERE objectId=?;", picture)
        numFavs = numFavsList[0]["numFavs"]
        numFavs += 1
        db.execute("UPDATE works SET numFavs=? WHERE objectId=?;", numFavs, picture)

        # Get bool list of when a picture is favorited
        isFav = compFavs(session["user_id"], keyRows)

        # Reload results page
        return render_template("results.html", keyRows=keyRows, answerRows=answerRows, results=results,
                           width=width, numMatches=numMatches, numCorrect=numCorrect,
                           quizPercentCorrect=quizPercentCorrect, isFav=isFav)

    # If reloading the page because a user UNfavorited a picure
    if request.form.get("unFavorite") == 'true':
        # Get data from results page to re-render template
        keyRows = eval(request.form.get("keyRows"))
        answerRows = eval(request.form.get("answerRows"))
        results = eval(request.form.get("results"))
        width = float(request.form.get("width"))
        numMatches = int(request.form.get("numMatches"))
        numCorrect = request.form.get("numCorrect")
        quizPercentCorrect = request.form.get("quizPercentCorrect")

        # Get objectId of picture to un-favorite
        picture = request.form.get("unFav")
        # Delete picture from favorites
        db.execute("DELETE FROM favorites WHERE username=? AND objectId=?;", session["user_id"], picture)
        # Decrement numFavs for picture
        numFavsList = db.execute("SELECT numFavs FROM works WHERE objectId=?;", picture)
        numFavs = numFavsList[0]["numFavs"]
        numFavs -= 1
        db.execute("UPDATE works SET numFavs=? WHERE objectId=?;", numFavs, picture)

        # Get bool list of when a picture is favorited
        isFav = compFavs(session["user_id"], keyRows)

        # Reload results page
        return render_template("results.html", keyRows=keyRows, answerRows=answerRows, results=results,
                           width=width, numMatches=numMatches, numCorrect=numCorrect,
                           quizPercentCorrect=quizPercentCorrect, isFav=isFav)


    # Get number of matches and width of cells from quiz page
    numMatches = int(request.form.get("numMatches"))
    width = float(request.form.get("width"))

    # Keep track of number of correct questions to pass to results page
    numCorrect = 0;

    # Create lists to hold pictures and answers
    pictures = []
    answers = []

    # Make list for results (whether user guessed correctly)
    results = []

    # Iterate through the matches to get answers from quiz page
    for i in range(numMatches):
        # Create picture name to get value
        pictureName = "picture" + str(i)
        # Get the picture value from the quiz page
        picture = request.form.get(pictureName)
        # And add it to the picture list
        pictures.append(picture)

        # Create answer name to get value
        answerName = "answer" + str(i)
        # Get the answer value from the quiz page
        answer = request.form.get(answerName)
        # And add it to the answer list
        answers.append(answer)

        # If answer was correct
        if answer == picture:
            # Get previous number of guesses and correct guesses, adjust
            guessesList = db.execute("SELECT guesses FROM works WHERE objectId=?;", picture)
            guesses = int(guessesList[0]["guesses"]) + 1
            correctList = db.execute("SELECT correct FROM works WHERE objectId=?;", picture)
            correct = int(correctList[0]["correct"]) + 1
            newPercentCorrect = correct / guesses
            # Reduce difficulty in works table
            db.execute("UPDATE works SET guesses=?, correct=?, percentCorrect=? WHERE objectId=?;",
                       guesses, correct, newPercentCorrect, picture)

            # If user is signed in
            if "user_id" in session:
                # Increment number of guesses and correct answers in user profile
                userNumGuessedList = db.execute("SELECT numGuessed FROM users WHERE id=?;", session["user_id"])
                userNumGuessed = int(userNumGuessedList[0]["numGuessed"]) + 1
                userNumCorrectList = db.execute("SELECT numCorrect FROM users WHERE id=?;", session["user_id"])
                userNumCorrect = int(userNumCorrectList[0]["numCorrect"]) + 1
                db.execute("UPDATE users SET numGuessed=?, numCorrect=? WHERE id=?;", userNumGuessed, userNumCorrect, session["user_id"])

            # Add a green entry to the results list for correct answer
            results.append("#C2DFA9")
            numCorrect += 1

        # If answer was incorrect
        else:
            # Get previous number of guesses and correct guesses, adjust guesses
            guessesList = db.execute("SELECT guesses FROM works WHERE objectId=?;", picture)
            guesses = int(guessesList[0]["guesses"]) + 1
            correctList = db.execute("SELECT correct FROM works WHERE objectId=?;", picture)
            correct = int(correctList[0]["correct"])
            newPercentCorrect = correct / guesses
            # Increase difficulty in works table
            db.execute("UPDATE works SET guesses=?, correct=?, percentCorrect=? WHERE objectId=?;",
                       guesses, correct, newPercentCorrect, picture)

            # If user is signed in
            if "user_id" in session:
                # Increment number of guesses and correct answers in user profile
                userNumGuessedList = db.execute("SELECT numGuessed FROM users WHERE id=?;", session["user_id"])
                userNumGuessed = int(userNumGuessedList[0]["numGuessed"]) + 1
                db.execute("UPDATE users SET numGuessed=? WHERE id=?;", userNumGuessed, session["user_id"])

            # Add a red entry to the results list for an incorrect answer
            results.append("#D68686")

    # Get percent correct to pass to the results page
    quizPercentCorrect = (numCorrect / numMatches) * 100
    quizPercentCorrect = round(quizPercentCorrect, 2)

    # Get artwork info from works table (again) so it can be displayed
    # There are two lists to keep the order of incorrect answers
    keyRows = []
    answerRows = []
    # Also, SQLite returns a list of dicts, so we'll strip the list and add it to our own
    for i in range(numMatches):
        # Get info for pictures(questions, keys)
        keyDictList = db.execute("SELECT objectId, title, artist, image FROM works WHERE objectId=?;", pictures[i])
        # Get the dict from the list
        keyDict = keyDictList[0]
        # Add to our list
        keyRows.append(keyDict)

        # Get info for answers(titles, artists)
        answerDictList = db.execute("SELECT objectId, title, artist FROM works WHERE objectId=?;", answers[i])
        # Get the dict from the list
        answerDict = answerDictList[0]
        # Add to our list
        answerRows.append(answerDict)

    # If user is signed in
    if "user_id" in session:
        # Get bool list of when a picture is favorited
        isFav = compFavs(session["user_id"], keyRows)

        return render_template("results.html", keyRows=keyRows, answerRows=answerRows, results=results,
                           width=width, numMatches=numMatches, numCorrect=numCorrect,
                           quizPercentCorrect=quizPercentCorrect, isFav=isFav)

    else:
        return render_template("results.html", keyRows=keyRows, answerRows=answerRows, results=results,
                           width=width, numMatches=numMatches, numCorrect=numCorrect,
                           quizPercentCorrect=quizPercentCorrect)


@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    if request.method == "POST":
        # If user is logged in
        if "user_id" in session:
            # If reloading the page because a user favorited a picure
            if request.form.get("favorite") == 'true':
                # Get data from results page to re-render template
                departments = request.form.get("departments")
                categories = request.form.get("categories")
                display = eval(request.form.get("display"))
                pictures = eval(request.form.get("pictures"))
                numPics = int(request.form.get("numPics"))
                currPage = int(request.form.get("currPage"))
                pages = int(request.form.get("pages"))
                firstPic = int(request.form.get("firstPic"))
                picRange = int(request.form.get("picRange"))
                displayNum = int(request.form.get("displayNum"))

                # Get objectId of new favorite picture
                picture = request.form.get("newFav")
                # Add picture to favorites
                db.execute("INSERT INTO favorites (username, objectId) VALUES (?, ?);", session["user_id"], picture)
                # Increment numFavs for picture
                numFavsList = db.execute("SELECT numFavs FROM works WHERE objectId=?;", picture)
                numFavs = numFavsList[0]["numFavs"]
                numFavs += 1
                db.execute("UPDATE works SET numFavs=? WHERE objectId=?;", numFavs, picture)

                # Get bool list of when a picture is favorited
                isFav = compFavs(session["user_id"], display)

                # Reload results page
                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                        pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                        picRange=picRange, displayNum=displayNum, isFav=isFav)

            # If reloading the page because a user UNfavorited a picure
            if request.form.get("unFavorite") == 'true':
                # Get data from results page to re-render template
                departments = request.form.get("departments")
                categories = request.form.get("categories")
                display = eval(request.form.get("display"))
                pictures = eval(request.form.get("pictures"))
                numPics = int(request.form.get("numPics"))
                currPage = int(request.form.get("currPage"))
                pages = int(request.form.get("pages"))
                firstPic = int(request.form.get("firstPic"))
                picRange = int(request.form.get("picRange"))
                displayNum = int(request.form.get("displayNum"))

                # Get objectId of picture to un-favorite
                picture = request.form.get("unFav")
                # Delete picture from favorites
                db.execute("DELETE FROM favorites WHERE username=? AND objectId=?;", session["user_id"], picture)
                # Decrement numFavs for picture
                numFavsList = db.execute("SELECT numFavs FROM works WHERE objectId=?;", picture)
                numFavs = numFavsList[0]["numFavs"]
                numFavs -= 1
                db.execute("UPDATE works SET numFavs=? WHERE objectId=?;", numFavs, picture)

                # Get bool list of when a picture is favorited
                isFav = compFavs(session["user_id"], display)

                # Reload results page
                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                        pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                        picRange=picRange, displayNum=displayNum, isFav=isFav)

        # Set page to display 20 results (atm)
        picRange = 20
        displayNum = 20
        firstPic = 0
        # Get departments to pass to settings
        departments = db.execute("SELECT department FROM works GROUP BY department;")
        # Get classifications to pass to settings
        categories = db.execute("SELECT classification FROM works GROUP BY classification;")
        # Get page and picture information from last database search
        pictures = request.form.get("pictures")
        numPics = int(request.form.get("numPics"))
        currPage = int(request.form.get("currPage"))
        pages = int(request.form.get("pages"))

        # Create list for pictures to be displayed on page
        display = []
        # Convert string to list of dicts
        pictures = eval(pictures)


        # If first pagination button selected
        if request.form.get("first") == 'true':
            # Make sure range doesn't go about total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # If user is logged in
            if "user_id" in session:
                # Get bool list of when a picture is favorited
                isFav = compFavs(session["user_id"], display)

                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)
            else:
                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum)

        # If previous is selected
        elif request.form.get("previous") == 'true':
            # Move back one page
            currPage = currPage - 1
            # Calculate first image index
            firstPic = (currPage - 2) * 20 + 20
            # Calculate last image range
            picRange = (currPage - 1) * 20 + 20
            # Make sure range doesn't go about total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # If user is logged in
            if "user_id" in session:
                # Get bool list of when a picture is favorited
                isFav = compFavs(session["user_id"], display)

                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)
            else:
                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum)

        # If next is selected
        elif request.form.get("next") == 'true':
            # Move forward one page
            currPage = currPage + 1
            # Calculate first image index
            firstPic = (currPage - 2) * 20 + 20
            # Calculate last image range
            picRange = (currPage - 1) * 20 + 20
            # Make sure range doesn't go about total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # If user is logged in
            if "user_id" in session:
                # Get bool list of when a picture is favorited
                isFav = compFavs(session["user_id"], display)

                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)
            else:
                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum)

        # If last is selected
        elif request.form.get("last") == 'true':
            # Set current page to last page
            currPage = pages
            # Calculate index of first image
            firstPic = (currPage - 2) * 20 + 20
            # Calculate last image range
            picRange = (currPage - 1) * 20 + 20
            # Make sure range doesn't go above total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # If user is logged in
            if "user_id" in session:
                # Get bool list of when a picture is favorited
                isFav = compFavs(session["user_id"], display)

                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)
            else:
                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum)

        elif request.form.get("goto") == 'true':
            # Set current page
            currPage = int(request.form.get("gotoPage"))
            # Calculate index of first image
            firstPic = (currPage - 2) * 20 + 20
            # Calculate last image range
            picRange = (currPage - 1) * 20 + 20
            # Make sure range doesn't go above total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # If user is logged in
            if "user_id" in session:
                # Get bool list of when a picture is favorited
                isFav = compFavs(session["user_id"], display)

                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)
            else:
                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum)

        # If search was requested
        else:
            # Difficulty is 0, keyword is empty for all searches unless other specified
            difficulty = 0
            keyword = ""
            # Get data from quiz settings form
            department = request.form.get("department")
            category = request.form.get("category")
            keyword = request.form.get("keyword")

            # Find works that fit criteria
            pictures = searchWorks(difficulty, department, category, keyword)

            # Calculate number of results
            numPics = len(pictures)
            # Make sure range doesn't go about total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Calculate number of pages
            pages = int(numPics / 20) + 1

            # Make dict to hold items to be displayed
            display = []
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # If user is logged in
            if "user_id" in session:
                # Get bool list of when a picture is favorited
                isFav = compFavs(session["user_id"], display)

                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                        pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                        picRange=picRange, displayNum=displayNum, isFav=isFav)
            else:
                return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                        pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                        picRange=picRange, displayNum=displayNum)

    else:
        # Set page to display 20 results (atm)
        displayNum = 20
        picRange = 20
        firstPic = 0
        # Get departments to pass to settings
        departments = db.execute("SELECT department FROM works GROUP BY department;")
        # Get classifications to pass to settings
        categories = db.execute("SELECT classification FROM works GROUP BY classification;")
        # Get start with all artworks to display
        pictures = db.execute("SELECT * FROM works ORDER BY numFavs DESC;")
        # Calculate number of results
        numPics = len(pictures)
        # Make sure range doesn't go about total number of pictures
        if numPics < picRange:
            displayNum = 20 + numPics - picRange
        # Calculate number of pages
        pages = int(numPics / 20) + 1

        # Make dict to hold items to be displayed
        display = []
        # Select pictures to be displayed on page
        for picture in pictures[firstPic:picRange]:
                display.append(picture)

        # If user is logged in
        if "user_id" in session:
            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

        else:
            return render_template("gallery.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum)


@app.route("/favorites", methods=["GET", "POST"])
@login_required
def favorites():
    if request.method == "POST":
        # If reloading the page because a user favorited a picure
        if request.form.get("favorite") == 'true':
            # Get data from results page to re-render template
            departments = request.form.get("departments")
            categories = request.form.get("categories")
            display = eval(request.form.get("display"))
            pictures = eval(request.form.get("pictures"))
            numPics = int(request.form.get("numPics"))
            currPage = int(request.form.get("currPage"))
            pages = int(request.form.get("pages"))
            firstPic = int(request.form.get("firstPic"))
            picRange = int(request.form.get("picRange"))
            displayNum = int(request.form.get("displayNum"))

            # Get objectId of new favorite picture
            picture = request.form.get("newFav")
            # Add picture to favorites
            db.execute("INSERT INTO favorites (username, objectId) VALUES (?, ?);", session["user_id"], picture)
            # Increment numFavs for picture
            numFavsList = db.execute("SELECT numFavs FROM works WHERE objectId=?;", picture)
            numFavs = numFavsList[0]["numFavs"]
            numFavs += 1
            db.execute("UPDATE works SET numFavs=? WHERE objectId=?;", numFavs, picture)

            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            # Reload results page
            return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

        # If reloading the page because a user UNfavorited a picure
        if request.form.get("unFavorite") == 'true':
            # Get data from results page to re-render template
            departments = request.form.get("departments")
            categories = request.form.get("categories")
            display = eval(request.form.get("display"))
            pictures = eval(request.form.get("pictures"))
            numPics = int(request.form.get("numPics"))
            currPage = int(request.form.get("currPage"))
            pages = int(request.form.get("pages"))
            firstPic = int(request.form.get("firstPic"))
            picRange = int(request.form.get("picRange"))
            displayNum = int(request.form.get("displayNum"))

            # Get objectId of picture to un-favorite
            picture = request.form.get("unFav")
            # Delete picture from favorites
            db.execute("DELETE FROM favorites WHERE username=? AND objectId=?;", session["user_id"], picture)
            # Decrement numFavs for picture
            numFavsList = db.execute("SELECT numFavs FROM works WHERE objectId=?;", picture)
            numFavs = numFavsList[0]["numFavs"]
            numFavs -= 1
            db.execute("UPDATE works SET numFavs=? WHERE objectId=?;", numFavs, picture)

            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            # Reload results page
            return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

        # Set page to display 20 results (atm)
        picRange = 20
        displayNum = 20
        firstPic = 0
        # Get departments to pass to settings
        departments = db.execute("SELECT department FROM works GROUP BY department;")
        # Get classifications to pass to settings
        categories = db.execute("SELECT classification FROM works GROUP BY classification;")
        # Get page and picture information from last database search
        pictures = request.form.get("pictures")
        numPics = int(request.form.get("numPics"))
        currPage = int(request.form.get("currPage"))
        pages = int(request.form.get("pages"))

        # Create list for pictures to be displayed on page
        display = []
        # Convert string to list of dicts
        pictures = eval(pictures)


        # If first pagination button selected
        if request.form.get("first") == 'true':
            # Make sure range doesn't go about total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            # Reload results page
            return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

        # If previous is selected
        elif request.form.get("previous") == 'true':
            # Move back one page
            currPage = currPage - 1
            # Calculate first image index
            firstPic = (currPage - 2) * 20 + 20
            # Calculate last image range
            picRange = (currPage - 1) * 20 + 20
            # Make sure range doesn't go about total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            # Reload results page
            return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

        # If next is selected
        elif request.form.get("next") == 'true':
            # Move forward one page
            currPage = currPage + 1
            # Calculate first image index
            firstPic = (currPage - 2) * 20 + 20
            # Calculate last image range
            picRange = (currPage - 1) * 20 + 20
            # Make sure range doesn't go about total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            # Reload results page
            return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

        # If last is selected
        elif request.form.get("last") == 'true':
            # Set current page to last page
            currPage = pages
            # Calculate index of first image
            firstPic = (currPage - 2) * 20 + 20
            # Calculate last image range
            picRange = (currPage - 1) * 20 + 20
            # Make sure range doesn't go above total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            # Reload results page
            return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

        elif request.form.get("goto") == 'true':
            # Set current page
            currPage = int(request.form.get("gotoPage"))
            # Calculate index of first image
            firstPic = (currPage - 2) * 20 + 20
            # Calculate last image range
            picRange = (currPage - 1) * 20 + 20
            # Make sure range doesn't go above total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            # Reload results page
            return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=currPage, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

        # If search was requested
        else:
            # Keyword is empty for all searches unless other specified
            keyword = ""
            # Get data from quiz settings form
            department = request.form.get("department")
            category = request.form.get("category")
            keyword = request.form.get("keyword")

            pictures = searchFavs(0, department, category, session["user_id"], keyword)

            # Calculate number of results
            numPics = len(pictures)
            # Make sure range doesn't go about total number of pictures
            if numPics < picRange:
                displayNum = 20 + numPics - picRange
            # Calculate number of pages
            pages = int(numPics / 20) + 1

            # Make dict to hold items to be displayed
            display = []
            # Select pictures to be displayed on page
            for picture in pictures[firstPic:picRange]:
                display.append(picture)

            # Get bool list of when a picture is favorited
            isFav = compFavs(session["user_id"], display)

            # Reload results page
            return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                    pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                    picRange=picRange, displayNum=displayNum, isFav=isFav)

    else:
        # Set page to display 20 results (atm)
        displayNum = 20
        picRange = 20
        firstPic = 0
        # Get list of favorites of user
        pictures = db.execute("SELECT * FROM works WHERE objectId IN (SELECT objectId FROM favorites WHERE username=?);", session["user_id"])
        # Get departments to pass to settings
        departments = db.execute("SELECT department FROM works GROUP BY department;")
        # Get classifications to pass to settings
        categories = db.execute("SELECT classification FROM works GROUP BY classification;")
        # Calculate number of results
        numPics = len(pictures)
        # Make sure range doesn't go about total number of pictures
        if numPics < picRange:
            displayNum = 20 + numPics - picRange
        # Calculate number of pages
        pages = int(numPics / 20) + 1

        # Make dict to hold items to be displayed
        display = []
        # Select pictures to be displayed on page
        for picture in pictures[firstPic:picRange]:
                display.append(picture)

        # Get bool list of when a picture is favorited
        isFav = compFavs(session["user_id"], display)

        # Reload results page
        return render_template("favorites.html", departments=departments, categories=categories, display=display,
                                pictures=pictures, numPics=numPics, currPage=1, pages=pages, firstPic=firstPic,
                                picRange=picRange, displayNum=displayNum, isFav=isFav)


@app.route("/aboutme", methods=["GET", "POST"])
def aboutme():
    return render_template("aboutme.html")


#__________________________________________________________________________________________________________________________
# These lines based on cs50's finance problem
@app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            # Alert user of missing username
            alert = "must provide username"
            return render_template("register.html", alert=alert)

        # Ensure username was is unique
        rows = db.execute("SELECT * FROM users WHERE username =?;", request.form.get("username"))
        if len(rows) > 0:
            # Alert user of missing username
            alert = "username taken"
            return render_template("register.html", alert=alert)

        # Ensure password was submitted
        elif not request.form.get("password"):
            # Alert user of missing password
            alert = "must provide password"
            return render_template("register.html", alert=alert)

        # Ensure password was matches confirmation
        elif request.form.get("confirmation") != request.form.get("password"):
            # Alert user of mistyped password
            alert = "password did not match confirmation"
            return render_template("register.html", alert=alert)

        # Insert name and hashed password into database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", request.form.get("username"),
                   generate_password_hash(request.form.get("password")))

        # Success message
        alert = "Registration successful"

        # Redirect user to log in page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            # Alert user of missing username
            alert = "must provide username"
            return render_template("login.html", alert=alert)

        # Ensure password was submitted
        elif not request.form.get("password"):
            # Alert user of missing password
            alert = "must provide password"
            return render_template("login.html", alert=alert)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            # Alert user of missing password
            alert = "invalid username and/or password"
            return render_template("login.html", alert=alert)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    loggedIn = False

    # Redirect user to login form
    return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# End cs50 code
#__________________________________________________________________________________________________________________________
