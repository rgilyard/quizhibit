from cs50 import SQL

db = SQL("sqlite:///met.db")

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
    if args[1] != "All":
        # Assign deparment variable
        department = args[1]
        # Add onto the search string
        searchString += " AND department=?"
        # Append list of search arguments
        argList.append(department)
    # If category is specified
    if args[2] != "All":
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











test = searchWorks(0, "Asian Art", "Paintings", "Emperor")
print(test)
print()
test = searchWorks(0, "Asian Art", "Paintings")
print(test)
print()
test = searchWorks(0, "Asian Art", "all")
print(test)
print()
test = searchWorks(0, "all", "all", "Trees")
print(test)
print()
test = searchWorks(0, "all", "Paintings", "Trees")
print(test)
print()
