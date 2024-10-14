from flask import session, request, flash, redirect, url_for, render_template
from functions.get_db_connection import get_db_connection
from functions.system_picture import system_picture
import datetime

def chat_room(user_id, current_user_id, current_username):
    """
    Handles the chat room functionality between two users.

    Args:
        user_id (int): The ID of the user being messaged.
        current_user_id (int): The ID of the current user.
        current_username (str): The username of the current user.

    Returns:
        Rendered HTML template of the chat room with the chat history.
    """
    conn = get_db_connection()

    # Generate a unique room identifier based on user IDs
    room = f"{min(current_user_id, user_id)}__{max(current_user_id, user_id)}"

    if not conn:
        flash('Database connection error!', 'danger')
        return redirect(url_for('dashboard', username=session.get('username')))

    cursor = conn.cursor()
    cursor.execute("SELECT name, profile_picture FROM users WHERE id = %s", (user_id,))
    user_info = cursor.fetchone()

    # Process user information
    if user_info:
        processed_info = {
            'name': user_info[0],
            'profile_picture': user_info[1].decode('utf-8') if user_info[1] else system_picture()
        }

    try:
        # Fetch chat history between the two users
        cursor.execute(""" 
            SELECT sender_id, receiver_id, message, timestamp 
            FROM messages 
            WHERE (sender_id = %s AND receiver_id = %s) 
            OR (sender_id = %s AND receiver_id = %s) 
            ORDER BY timestamp 
        """, (current_user_id, user_id, user_id, current_user_id))

        chat_history = cursor.fetchall()
        enhanced_chat_history = enhance_chat_history(chat_history, cursor, current_user_id)

        return render_template('chat_room.html', chat_history=enhanced_chat_history, user_id=user_id, user_info=processed_info, current_username=current_username, target_username=user_info[0], room=room)

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('dashboard', username=session.get('username')))
    
    finally:
        cursor.close()
        conn.close()

def enhance_chat_history(chat_history, cursor, current_user_id):
    """
    Enhances the chat history with sender names.

    Args:
        chat_history (list): The raw chat history fetched from the database.
        cursor (cursor): The database cursor for executing queries.
        current_user_id (int): The ID of the current user.

    Returns:
        list: A list of dictionaries containing enhanced chat messages with sender names.
    """
    enhanced_chat_history = []
    for chat in chat_history:
        sender_id = chat[0]
        sender_name = "You" if sender_id == current_user_id else get_username(sender_id, cursor)
        enhanced_chat_history.append({
            'sender_name': sender_name,
            'message': chat[2],
            'timestamp': chat[3]
        })
    return enhanced_chat_history

def get_username(user_id, cursor):
    """
    Fetches the username of a user by their ID.

    Args:
        user_id (int): The ID of the user.
        cursor (cursor): The database cursor for executing queries.

    Returns:
        str: The username of the user.
    """
    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()[0]
