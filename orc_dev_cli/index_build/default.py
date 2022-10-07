build = {
    "configuration": {
        "remote": "git@github.com:integr8ly/integreatly-operator.git",
        "local": None,
        "tag_marker": "rhoam-v",
        "image_site": "quay.io",
        "org": None,
        "operator": "managed-api-service",
        "temporary": {"reuse": False, "location": None},
    },
    "chain": {
        "start": "latest",
        "service_affecting": "existing",
        "pre_release": None,
    },
    "current": {},
    "latest": {"branch": "master", "service_affecting": False, "include": True},
    "new": {
        "branch": None,
        "location": "local",
        "include": True,
        "checkout": False,
        "ensure_branch": True,
        "service_affecting": True,
    },
}

required = {
    "configuration": ["local", "org"],
    "new": ["branch"],
}
