from fastapi import Header, HTTPException, status, Cookie, Response, Request
from firebase_admin import auth, credentials, initialize_app, exceptions
from schema.exceptions import InvalidTokenError
from typing import Optional
import datetime
from utils.logger import get_logger
from models.user_models import UserId, LogoutResponse
from patterns.singleton import SingletonMeta
import base64
import json
from config.env import FIREBASE_JSON_BASE64
logger = get_logger(__name__)


class UserAuthenticator(metaclass=SingletonMeta):
    """To handle authenticating user requests and session tokens"""

    DEFAULT_EXPIRES_IN = 5  # In Days
    BYPASS_USER_AUTHENTICATOR = False

    user_verification_model = UserId

    def __init__(
        self,
    ) -> None:
        firebase_creds_json = base64.b64decode(FIREBASE_JSON_BASE64)
        firebase_creds_dict = json.loads(firebase_creds_json)
        cred = credentials.Certificate(firebase_creds_dict)
        try:
            initialize_app(cred)
        except ValueError as e:  # App is already initilazed
            pass

    def create_session_cookie(self, id_token: str, expires_in: Optional[int] = None) -> str | None:
        """Creates and adds session cookie based on id_token

        Args:
            id_token (str): jwt token of the user
            expires_in (Optional[int], optional): In days, when the session token should expire. Defaults to None.

        Raises:
            PermissionError: If id_token is invalid

        Returns:
            str | None: returns the set session cookie or None if BYPASS_USER_AUTHENTICATOR is True
        """
        if self.BYPASS_USER_AUTHENTICATOR:
            return None
        if expires_in:
            expires_in = datetime.timedelta(days=expires_in)
        else:
            expires_in = datetime.timedelta(days=self.DEFAULT_EXPIRES_IN)
        try:
            session_cookie = auth.create_session_cookie(
                id_token, expires_in=expires_in)

            return session_cookie
        except exceptions.FirebaseError as e:
            raise PermissionError(str(e))

    def decode_token(self, token_id: str):
        try:
            decoded_token = auth.verify_id_token(token_id)
            return decoded_token
        except:
            raise PermissionError('Invalid JWT token')

    def revoke_user_tokens(self, sub: str):
        try:
            # Revoke all refresh tokens for a specified user
            auth.revoke_refresh_tokens(sub)
        except exceptions.FirebaseError as e:
            raise PermissionError(str(e))

    def verify_user(self, session: str | None, request_user_id: str) -> bool:
        """Checks whether the user is valid

        Args:
            decoded_user (Dict): decoded access_token credentials authorization header
            request_user_id (str): user_id passed in the request of the route
        """
        if self.BYPASS_USER_AUTHENTICATOR:
            return True

        if session:
            decoded_claims = auth.verify_session_cookie(session)
            if decoded_claims['user_id'] != request_user_id:
                raise PermissionError("Incorrrect session token provided")
            else:
                return True
        elif not session and request_user_id:
            raise PermissionError("Incorrrect session token provided")

    def set_cookie(self, response: Response, session_cookie: str, expires_in: Optional[int] = None):
        if self.BYPASS_USER_AUTHENTICATOR:
            return True
        if expires_in:
            expires_in = datetime.datetime.utcnow() + datetime.timedelta(days=expires_in)
        else:
            expires_in = datetime.datetime.utcnow(
            ) + datetime.timedelta(days=self.DEFAULT_EXPIRES_IN)
        expires_in = expires_in.strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.set_cookie(
            key="session",
            value=session_cookie,
            secure=True,
            httponly=True,
            samesite='none',
            expires=expires_in
        )
        logger.debug("Session cookies set!")
        return True

    def verify_session_token(self, Authorization: str = Header(None)):
        if not Authorization or not Authorization.startswith("Bearer "):
            return None
        else:
            token = Authorization[6::]
            user = self.decode_token(token)
            return user

    async def logout(self, response: Response, session: str | None = Cookie(None)) -> LogoutResponse:
        if self.BYPASS_USER_AUTHENTICATOR or not session:
            return LogoutResponse(response='User Logout Successful')
        expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)

        response.set_cookie(
            key='session',
            value="",
            secure=True,
            httponly=True,
            samesite='none',
            expires=expires.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )

        return LogoutResponse(response='User Logout Successful')

    async def get_token(self, Authorization: str = Header(None)) -> str | None:
        """Retrieve token from Headers

        Args:
            Authorization (str, optional): FastAPI Authorization Header. Defaults to Header(None).

        Raises:
            InvalidTokenError: If token is invalid

        Returns:
            str | None: Return the JWT token
        """
        if not Authorization or not Authorization.startswith("Bearer "):
            if not self.BYPASS_USER_AUTHENTICATOR:
                raise InvalidTokenError("Token not provided")
            return None
        else:
            token = Authorization.split(" ")[1]
            return token

    async def get_verify_session_cookie(self, user_id: str, session: str = Cookie(None)) -> bool:
        """Verify session cookie for GET requests.
        Add this as a dependancy to any GET requests

        Args:
            user_id (str): user_id
            session (str, optional): session_cookie. Defaults to Cookie(None).

        Raises:
            HTTPException: 401
            HTTPException: 403

        Returns:
            bool: True if verified
        """
        if user_id == "anonymous": # User is anonymous
            return True
        if not session:
            logger.warning("Session cookie is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please sign in or create an account."
            )
        if not self.verify_user(session, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate user."
            )
        return True

    async def post_verify_session_cookie(self, request: Request, session: str = Cookie(None)) -> bool:
        """Verify session cookie for POST/DELETE/UPDATE requests.
        Add this as a dependancy as a parameter of the endpoint funtion.

        Args:
            request (Request): Request to verify
            session (str, optional): session_cookie. Defaults to Cookie(None).

        Raises:
            HTTPException: 401 Session cookie is missing
            HTTPException: 403 user not authenticated

        Returns:
            bool: True if verified
        """
        body = await request.json()
        user_id = self.user_verification_model(**body).user_id
        
        if user_id == "anonymous": # User is anonymous
            return True
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please sign in or create an account."
            )


        if not self.verify_user(session, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authenticated"
            )
        return True

    async def verify_session_for_upload(self, request: Request, session: str = Cookie(None)) -> bool:
        form_data = await request.form()
        user_id = form_data.get('user_id')

        if user_id == "anonymous":
            return True
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please sign in or create an account."
            )


        if not user_id or not self.verify_user(session, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authenticated"
            )
        return True
