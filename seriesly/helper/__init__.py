from django.http import HttpResponseNotAllowed


def is_post(func):
    def need_post_func(*args, **kwargs):
        request = args[0]
        if request.method == "POST":
            return func(*args, **kwargs)
        else:
            return HttpResponseNotAllowed(["POST"])

    return need_post_func


def is_get(func):
    def need_get_func(*args, **kwargs):
        request = args[0]
        if request.method == "GET":
            return func(*args, **kwargs)
        else:
            return HttpResponseNotAllowed(["GET"])

    return need_get_func
