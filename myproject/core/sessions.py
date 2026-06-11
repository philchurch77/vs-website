from django.utils.crypto import get_random_string


def get_or_create_session_id(request, key):
    """Return the chat session id stored under ``key``, creating one if absent."""
    session_id = request.session.get(key)
    if not session_id:
        session_id = get_random_string(32)
        request.session[key] = session_id
    return session_id
