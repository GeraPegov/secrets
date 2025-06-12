from fastapi import Request


def get_client_ip(request: Request) -> str:
    if 'x_forwarded_for' in request.headers:
        return request.headers['x_forwarded_for'].split(",")[0].strip()
    return request.client.host
