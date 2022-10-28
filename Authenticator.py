import requests
from typing import Optional


class Authenticator:
    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 refresh_token: Optional[str],
                 auth_url: str,
                 access_token_url: str,
                 redirect_uri: str = "https://example.com/callback"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.access_token_url = access_token_url
        self.redirect_uri = redirect_uri
        self.refresh_token = refresh_token
        self.access_token = None
        
        self.get_access_token()

    def get_access_token(self) -> str:

        # Authenticate using Refresh Token if possible, otherwise prompt user to approve in browser
        if self.refresh_token is None:
            res = requests.get(self.auth_url,
                               params={"client_id": self.client_id,
                                       "redirect_uri": self.redirect_uri,
                                       "response_type": "code"},
                               allow_redirects=False)
            print(f"Visit this url to authorize and provide access code: {res.headers['Location']}")
            code = input("\nInput access code: ")
            grant_type = "authorization_code"
            code_type = "code"
        else:
            code = self.refresh_token
            grant_type = "refresh_token"
            code_type = "refresh_token"

        res = requests.post(self.access_token_url,
                            data={"grant_type": grant_type,
                                  "redirect_uri": self.redirect_uri,
                                  code_type: code},
                            auth=(self.client_id, self.client_secret))

        # Save access & refresh tokens
        self.refresh_token = res.json()['refresh_token']
        self.access_token = res.json()['access_token']
