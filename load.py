import urllib.request, json, csv, time
from cs50 import SQL

# Load Met art information from CSV file to SQL table

# Create database object? Or connect to database (not sure how this works)
db = SQL("sqlite:///met.db")

print()
print("Creating database...")

# If works table exists, drop
db.execute("DROP TABLE IF EXISTS works;")
# Create new table works
db.execute("CREATE TABLE IF NOT EXISTS works (objectId INT PRIMARY KEY, title TEXT, artist TEXT,"
           "classification TEXT, department INT, image TEXT, guesses INT DEFAULT 4, correct INT DEFAULT 3,"
           "percentCorrect NUMERIC DEFAULT 0.75, numFavs INT DEFAULT 0);")

# If users table exists, drop
db.execute("DROP TABLE IF EXISTS users;")
# Create new users table
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT NOT NULL, hash TEXT NOT NULL,"
           "numGuessed INT DEFAULT 0, numCorrect INT DEFAULT 0, PRIMARY KEY(id));")

# If favorites table exists, drop
db.execute("DROP TABLE IF EXISTS favorites;")
# Create new users table
db.execute("CREATE TABLE IF NOT EXISTS favorites (id INTEGER, username TEXT, objectId INT, PRIMARY KEY(id));")


# Open Met csv file
with open("openaccess/MetObjects.csv") as file:
    reader = csv.DictReader(file)

    totalCount = 0
    highlight = 0

    print()
    print("Populating database...")
    print("Metropolitan Museum API limits requests to 80 per second, so I had to add a pause")
    print("after every request to load them all in one go. This will take a couple of minutes.")

    # Iterate over cvs file, copy values to SQL table (This takes a minute)
    for row in reader:
        #Keep count of total csv file rows
        totalCount += 1
        # Only add artworks that are part of the public domain and in the permanent collection
        if (row["Is Highlight"] == "True"
            and row["Is Public Domain"] == "True"
            and len(row["Title"]) > 0
            and len(row["Artist Display Name"]) > 0
            and len(row["Classification"]) > 2):

            # Get json of artwork data via API (to get artwork image)
            with urllib.request.urlopen("https://collectionapi.metmuseum.org/public/collection/v1/objects/"
                                        + str(row["Object ID"])) as url:
                # Decode the json
                data = json.loads(url.read().decode())

                # If there is an image for the work
                if (len(data["primaryImage"]) > 0):

                    # Make artist info more presentable
                    artist = row["Artist Display Name"]
                    if "|" in artist:
                        artist = artist.replace("|", "; ")

                    db.execute("INSERT INTO works (objectId, title, artist, classification, department, image)"
                               "VALUES (?, ?, ?, ?, ?, ?);", row["Object ID"], row["Title"], artist,
                               row["Classification"], row["Department"], data["primaryImage"])

                    # Keep track of rows added to database
                    highlight += 1
                    time.sleep(.02)

    print(totalCount, end='')
    print(" Entries Scanned")
    print(highlight, end='')
    print(" Entries Added")
    file.close()


# Narrow classification categories
categories = ["Furniture",
              "Silver",
              "Glass",
              "Ceramics",
              "Metalwork",
              "Paintings",
              "Sculpture",
              "Drawings",
              "Textiles",
              "Jewelry",
              "Weaponry",
              "Costumes",
              "Calligraphy",
              "Screens",
              "Woodwork",
              "Enamels",
              "Natural Substances",
              "Vases",
              "Photographs",
              "Prints",
              "Books",
              "Frames",
              "Codices and Manuscripts",
              "Installations",
              "Musical Instruments"]

print()
print("Consolidating categories...")

# Sometimes department names serve as better categories than the more specific classifications
db.execute("UPDATE works SET classification='Arms and Armor' WHERE department='Arms and Armor';")
db.execute("UPDATE works SET classification='Musical Instruments' WHERE department='Musical Instruments';")
db.execute("UPDATE works SET classification='Codices and Manuscripts' WHERE classification LIKE '%Codices%'"
           "OR classification LIKE '%Manuscripts%';")
db.execute("UPDATE works SET classification='Photographs' WHERE classification LIKE '%Negatives%';")

# Works that have key words as part of a classification, get that word as their entire classification
for category in categories:
    db.execute("UPDATE works SET classification=? WHERE classification LIKE '%' || ? || '%';", category, category)


# Categories with few than 16 items are labeled other
rows = db.execute("SELECT COUNT(objectId), classification FROM works GROUP BY classification;")
for row in rows:
    if row["COUNT(objectId)"] < 16:
        db.execute("UPDATE works SET classification='Other' WHERE classification=?;", row["classification"])

# Print out categories
checks = db.execute("SELECT COUNT(objectId), classification FROM works GROUP BY classification;")
for check in checks:
    print(check)


print()
print("Done!")