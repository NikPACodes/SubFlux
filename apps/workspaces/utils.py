from slugify import slugify
import secrets

def gen_ws_code()->str:
    """
    Генератор уникального Workspace кода.
    """
    return secrets.token_urlsafe(8)

def gen_ws_slug(title: str)->str:
    """
    Формирование Workspace slug.
    """
    return slugify (title, lowercase=False, separator='-')