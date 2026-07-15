from slugify import slugify

def gen_slug(title: str)->str:
    """
    Формирование slug.
    """
    if not title or not title.strip():
        raise ValueError("Title не может быть пустым.")

    slug = slugify(title, lowercase=True, separator='-')

    if not slug:
        raise ValueError(f"Ошибка генерации Slug из Title: {title}")

    return slug