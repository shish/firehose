
__version__ = "0.0.0"

def uid_to_name(uid):
    return uid.partition("(")[0].partition("<")[0].strip()


