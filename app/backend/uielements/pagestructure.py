from nicegui import ui

from app.backend.uielements.header import build_header


def inner_page(path):
    """
    Decorator to define a page with a specific path.
    """
    def decorator(func):
        @ui.page(path)
        def wrapper():
            build_header()
            return func()
    return decorator

def inner_page_async(path):
    """
    Decorator to define a page with a specific path.
    """
    def decorator(func):
        @ui.page(path)
        async def wrapper():
            build_header()
            return await func()
    return decorator