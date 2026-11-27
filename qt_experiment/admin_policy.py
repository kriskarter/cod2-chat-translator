"""One-time migration of the isolated Qt preview startup UAC preference."""
ADMIN_POLICY_VERSION = 1
VERSION_KEY = "qt_admin_policy_version"
PREFERENCE_KEY = "qt_always_admin"


def admin_policy(config):
    """Return a copy; missing/old markers mean legacy automatic False."""
    result = dict(config)
    version = result.get(VERSION_KEY)
    if type(version) is not int or version < ADMIN_POLICY_VERSION:
        result[VERSION_KEY] = ADMIN_POLICY_VERSION
        result[PREFERENCE_KEY] = True
    elif type(result.get(PREFERENCE_KEY)) is not bool:
        result[PREFERENCE_KEY] = True
    return result


def persist_admin_policy(store, values):
    """Persist only the two Qt policy keys before any elevation request."""
    raw = store.load({})
    updated = admin_policy(raw)
    recovered = store.recovered
    if updated != raw:
        store.save(updated)
    merged = dict(values)
    merged.update({VERSION_KEY: updated[VERSION_KEY], PREFERENCE_KEY: updated[PREFERENCE_KEY]})
    return merged, recovered
