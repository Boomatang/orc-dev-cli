def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


def safe_string(string):
    # TODO checks need to be added to ensure there is no command injection done in the string
    return string
