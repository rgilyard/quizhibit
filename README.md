# Quizhibit

***

**This is my first web app and it is currently in active development. It's been deployed on Heroku for practice, but it's very buggy on there. 
The Metropolitan Museum API may change at anytime. Many feautres are still in progress.**

Quizhibit is an art quiz app, gallery browser, and search tool for the featured pieces in the Metropolitan Museum of Art. Registered users can
favorite pieces they like, quiz themselves on their favorites, and keep track of their average quiz score.


## Getting Started

A demo of the app can be viewed [here](quizhibit.herokuapp.com), although you will run into problems when signed into an account. 
Please do not use any personal information for the site, it is ***not*** secure. 
Your account may be deleted at any time, as I drop and reload the database regularly.

I believe the dependencies can be installed with:
```
pip install -r requirements.txt
```

Then, the app can be run from the project directory with:
```
flask run
```

## Files

### load.py

load.py will delete all databases and reload them. 
```
python load.py
```
It populates the databases from the Met API's csv and the API. Because the API limits requests to 80 per second, I had to add pauses in the program
and it takes several minutes to complete.

load.py also consolidates some of the sparser categories and reformats some of the data to be more readable and presentable.


### met.db 

The works table holds the artwork information, links to the images, and data on how often they've been guessed correctly in the quiz.
The users table holds usernames, hashed passwords, user id's, and quiz records. The favorites tables keeps track of the artwork id's and
user id's.

#### helpers.py
