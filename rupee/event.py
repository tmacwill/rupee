_registry = {}

def publish(event, *args, **kwargs):
    fns = _registry.get(event, [])
    for fn in fns:
        fn(*args, **kwargs)

def subscribe(event):
    def wrap(f):
        add_subscriber(event, f)
        return f
    return wrap

def add_subscriber(event, fn):
    _registry.setdefault(event, [])
    _registry[event].append(fn)
