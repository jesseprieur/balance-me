import functools

from flask import g, redirect, request, url_for


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view
