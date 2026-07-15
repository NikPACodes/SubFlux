import secrets

def gen_ws_code()->str:
    """
    Генератор уникального Workspace кода.
    """
    return secrets.token_urlsafe(8)