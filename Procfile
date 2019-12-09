web: gunicorn application:app
heroku ps:scale web=1
heroku features:enable http-session-affinity