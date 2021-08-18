from cs50 import SQL

db = SQL("sqlite:///met.db")

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










department = "all"
category = "all"
keyword = ""
test = searchFavs(0, department, category, 2)
print(test)
print()
test = searchFavs(0, "all", "all", 1, "Trees")
print(test)
print()
"""test = searchFavs(0, "Asian Art", "Paintings", 1)
print(test)
print()
test = searchFavs(0, "Asian Art", "all", 1)
print(test)
print()
test = searchFavs(0, "all", "all", 1, "Trees")
print(test)
print()
test = searchFavs(0, "all", "Paintings", 1, "Trees")
print(test)
print()"""
