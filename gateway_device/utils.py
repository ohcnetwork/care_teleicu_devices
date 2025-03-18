from ipaddress import IPv4Address, IPv6Address


def validate_endpoint_address(value: str) -> str:
    try:
        return str(IPv4Address(value))
    except ValueError:
        pass
    try:
        return str(IPv6Address(value))
    except ValueError:
        pass

    # If it's a string, validate hostname format
    if "://" in value:
        raise ValueError("URL schemes not allowed in hostname")

    if not all(c.isalnum() or c in "-_.:" for c in value):
        raise ValueError(
            "Hostname parts can only contain alphanumeric characters, hyphens and underscores"
        )

    return value
