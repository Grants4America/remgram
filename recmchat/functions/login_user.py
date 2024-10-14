from flask import request, url_for, redirect, session, make_response, flash
from functions.get_db_connection import get_db_connection
from bcrypt import checkpw

def login_user():
    """
    Handles user login by verifying the provided username and password.

    This function retrieves the username and password from the login form, 
    checks them against the database, and establishes a session if the 
    credentials are valid. It also sets a login cookie.

    Returns:
        Response: A redirect response to the user's dashboard if login is successful, 
                  or to the index page with an error message if unsuccessful.
    """
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()

    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
                # User credentials are valid
                session.update({'username': username, 'name': user[1], 'user_id': user[0]})
                response = make_response(redirect(url_for('dashboard', username=username)))
                response.set_cookie('logged_in', 'true', max_age=60*60*24)  # 1-day cookie
                return response

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        flash('Database connection error!', 'danger')

    flash('Invalid username or password! 😒', 'danger')
    return redirect(url_for('index'))
