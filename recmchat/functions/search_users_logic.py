from flask import request, flash, session
from functions.get_db_connection import get_db_connection
from functions.system_picture import system_picture

def search_users_logic():
    """
    Handles user search functionality by querying users based on the search query.
    Returns:
        - search_results: List of user search results for the current page.
        - page: Current page number for pagination.
    """

    # Get the current page number from the query parameters, default is 1
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of results per page
    offset = (page - 1) * per_page  # Calculate the offset for pagination

    # Determine if it's a POST request (form submission) or GET request (query string)
    if request.method == 'POST':
        query = request.form.get('search_query', '').strip()  # Get query from form
    else:
        query = request.args.get('q', '').strip()  # Get query from URL query string

    # If no query is provided, return an empty result set
    if not query:
        flash('Please enter a search query.', 'warning')
        return [], page, 1, None

    conn = get_db_connection()

    if not conn:
        flash('Database connection error!', 'danger')
        return [], page, 1, None

    search_results = []
    total_users = 0

    try:
        cursor = conn.cursor()
        current_user_id = session.get('user_id')

        # Fetch total user count for pagination (excluding the current user)
        cursor.execute(
            "SELECT COUNT(*) FROM users WHERE name LIKE %s AND id != %s",
            ('%' + query + '%', current_user_id)
        )
        total_users = cursor.fetchone()[0]

        # Fetch users for the current page
        cursor.execute(
            "SELECT id, name, profile_picture FROM users WHERE name LIKE %s AND id != %s ORDER BY id LIMIT %s OFFSET %s",
            ('%' + query + '%', current_user_id, per_page, offset)
        )
        results = cursor.fetchall()

        # Get the current user's following list
        cursor.execute(
            "SELECT followed_user_id FROM followers WHERE user_id = %s",
            (current_user_id,)
        )
        following_list = {row[0] for row in cursor.fetchall()}

        # Prepare search results
        search_results = [
            {
                'id': user[0],
                'name': user[1],
                'profile_picture': user[2].decode('utf-8') if user[2] else system_picture(),
                'is_following': user[0] in following_list
            }
            for user in results
        ]

        if not search_results:
            flash('No user found! 😒', 'info')

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')

    finally:
        conn.close()

    # Calculate total pages for pagination
    total_pages = (total_users + per_page - 1) // per_page

    # Return search results and current page
    return search_results, page, total_pages, query
