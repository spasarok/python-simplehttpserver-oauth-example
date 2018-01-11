import sys, os, socket, webbrowser, re
from requests_oauthlib import OAuth1Session

def create_oauth_session(key, secret, callback_uri):
    return OAuth1Session(key, client_secret=secret, callback_uri=callback_uri)

def get_request_token(oauth_session):
    request_token_url = 'http://www.tumblr.com/oauth/request_token'
    oauth_session.fetch_request_token(request_token_url)

def get_user_permission(oauth_session):
    authorization_base_url = 'http://www.tumblr.com/oauth/authorize'
    authorization_url = oauth_session.authorization_url(authorization_base_url)
    webbrowser.open(authorization_url)

def get_access_token(oauth_session, user_redirect_url_with_auth):
    access_token_url = 'http://www.tumblr.com/oauth/access_token'
    oauth_session.parse_authorization_response(user_redirect_url_with_auth)
    oauth_session.fetch_access_token(access_token_url)

def create_socket(host, port):
    http_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Streaming socket
    http_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    http_socket.bind((host, port))
    http_socket.listen(1)
    print 'Serving HTTP on port %s ...' % port
    return http_socket

def handle_socket_requests(oauth_session, http_socket, user_redirect_url):
    token_requested = False
    user_permission_requested = False
    http_response = ''
    while True:
        client_connection, client_address = http_socket.accept()
        request = client_connection.recv(1024)

        if not token_requested:
            token_requested = True
            get_request_token(oauth_session)
        elif not user_permission_requested:
            user_permission_requested = True
            get_user_permission(oauth_session)
        else:
            success_response = re.match('GET(.*oauth_token=.*&oauth_verifier=.*)HTTP/1.1', request)
            if success_response:
                get_access_token(oauth_session, user_redirect_url + success_response.group(1).strip())
                print(user_redirect_url + success_response.group(1).strip())
                print(oauth_session.get('http://api.tumblr.com/v2/user/dashboard'))

        client_connection.sendall('HTTP/1.1 200 OK\n\nHello World!')
        client_connection.close()

def main():
    key, secret, user_redirect_url = os.environ['tumbleswap_key'], os.environ['tumbleswap_secret'], 'http://localhost:8888'
    oauth_session = create_oauth_session(key, secret, user_redirect_url)
    handle_socket_requests(oauth_session, create_socket('', 8888), user_redirect_url)
    print(oauth_session.get('http://api.tumblr.com/v2/user/dashboard'))

main()
