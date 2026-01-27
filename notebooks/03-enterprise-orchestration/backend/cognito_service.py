# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# DEMO CODE - For educational purposes only. See SECURITY.md before production use.

import boto3
import jwt
import requests
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError
from config import Config
import json

class CognitoService:
    def __init__(self):
        self.region = Config.AWS_REGION
        self.user_pool_id = Config.COGNITO_USER_POOL_ID
        self.client_id = Config.COGNITO_CLIENT_ID
        self.client_secret = None  # Not using client secret
        
        # Validate required configuration
        if not all([self.region, self.user_pool_id, self.client_id]):
            raise ValueError("Missing required Cognito configuration. Please check your .env file.")
        
        self.client = boto3.client('cognito-idp', region_name=self.region)
        self._jwks = None
    
    def _get_secret_hash(self, username):
        """Generate secret hash for Cognito client"""
        if not self.client_secret:
            return None
        
        message = username + self.client_id
        dig = hmac.new(
            str(self.client_secret).encode('utf-8'),
            msg=str(message).encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def sign_up(self, email, password, tenant_id, given_name, family_name):
        """Register a new user with tenant information"""
        try:
            secret_hash = self._get_secret_hash(email)
            
            user_attributes = [
                {'Name': 'email', 'Value': email},
                {'Name': 'given_name', 'Value': given_name},
                {'Name': 'family_name', 'Value': family_name},
                {'Name': 'custom:tenant_id', 'Value': tenant_id}
            ]
            
            kwargs = {
                'ClientId': self.client_id,
                'Username': email,
                'Password': password,
                'UserAttributes': user_attributes
            }
            
            if secret_hash:
                kwargs['SecretHash'] = secret_hash
            
            response = self.client.sign_up(**kwargs)
            
            return {
                'success': True,
                'user_sub': response['UserSub'],
                'message': 'User registered successfully. Please check your email for verification.'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            return {
                'success': False,
                'error_code': error_code,
                'message': error_message
            }
    
    def confirm_sign_up(self, email, confirmation_code):
        """Confirm user registration with verification code"""
        try:
            secret_hash = self._get_secret_hash(email)
            
            kwargs = {
                'ClientId': self.client_id,
                'Username': email,
                'ConfirmationCode': confirmation_code
            }
            
            if secret_hash:
                kwargs['SecretHash'] = secret_hash
            
            self.client.confirm_sign_up(**kwargs)
            
            return {'success': True, 'message': 'Email confirmed successfully'}
            
        except ClientError as e:
            return {
                'success': False,
                'message': e.response['Error']['Message']
            }
    
    def sign_in(self, email, password):
        """Authenticate user and return tokens"""
        try:
            secret_hash = self._get_secret_hash(email)
            
            kwargs = {
                'ClientId': self.client_id,
                'AuthFlow': 'USER_PASSWORD_AUTH',
                'AuthParameters': {
                    'USERNAME': email,
                    'PASSWORD': password
                }
            }
            
            if secret_hash:
                kwargs['AuthParameters']['SECRET_HASH'] = secret_hash
            
            response = self.client.initiate_auth(**kwargs)
            
            # Check if there's a challenge (like password change required)
            if 'ChallengeName' in response:
                challenge_name = response['ChallengeName']
                if challenge_name == 'NEW_PASSWORD_REQUIRED':
                    return {
                        'success': False,
                        'error_code': 'NEW_PASSWORD_REQUIRED',
                        'message': 'New password required. Please change your password.',
                        'session': response['Session']
                    }
                else:
                    return {
                        'success': False,
                        'error_code': challenge_name,
                        'message': f'Challenge required: {challenge_name}'
                    }
            
            # Extract tokens
            auth_result = response['AuthenticationResult']
            access_token = auth_result['AccessToken']
            id_token = auth_result['IdToken']
            refresh_token = auth_result['RefreshToken']
            
            # Decode ID token to get user info
            user_info = self.decode_token(id_token)
            
            return {
                'success': True,
                'access_token': access_token,
                'id_token': id_token,
                'refresh_token': refresh_token,
                'user_info': user_info
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'UserNotConfirmedException':
                return {
                    'success': False,
                    'error_code': error_code,
                    'message': 'Please confirm your email address first'
                }
            elif error_code == 'NotAuthorizedException':
                return {
                    'success': False,
                    'error_code': error_code,
                    'message': 'Invalid email or password'
                }
            else:
                return {
                    'success': False,
                    'error_code': error_code,
                    'message': e.response['Error']['Message']
                }
    
    def respond_to_new_password_challenge(self, session, username, new_password):
        """Respond to NEW_PASSWORD_REQUIRED challenge"""
        try:
            secret_hash = self._get_secret_hash(username)
            
            challenge_responses = {
                'USERNAME': username,
                'NEW_PASSWORD': new_password
            }
            
            if secret_hash:
                challenge_responses['SECRET_HASH'] = secret_hash
            
            response = self.client.respond_to_auth_challenge(
                ClientId=self.client_id,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=session,
                ChallengeResponses=challenge_responses
            )
            
            # Extract tokens after successful password change
            auth_result = response['AuthenticationResult']
            access_token = auth_result['AccessToken']
            id_token = auth_result['IdToken']
            refresh_token = auth_result['RefreshToken']
            
            # Decode ID token to get user info
            user_info = self.decode_token(id_token)
            
            return {
                'success': True,
                'access_token': access_token,
                'id_token': id_token,
                'refresh_token': refresh_token,
                'user_info': user_info
            }
            
        except ClientError as e:
            return {
                'success': False,
                'error_code': e.response['Error']['Code'],
                'message': e.response['Error']['Message']
            }
    
    def refresh_token(self, refresh_token, username):
        """Refresh access token using refresh token"""
        try:
            secret_hash = self._get_secret_hash(username)
            
            kwargs = {
                'ClientId': self.client_id,
                'AuthFlow': 'REFRESH_TOKEN_AUTH',
                'AuthParameters': {
                    'REFRESH_TOKEN': refresh_token
                }
            }
            
            if secret_hash:
                kwargs['AuthParameters']['SECRET_HASH'] = secret_hash
            
            response = self.client.initiate_auth(**kwargs)
            
            auth_result = response['AuthenticationResult']
            return {
                'success': True,
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken']
            }
            
        except ClientError as e:
            return {
                'success': False,
                'message': e.response['Error']['Message']
            }
    
    def get_jwks(self):
        """Get JSON Web Key Set for token verification"""
        if self._jwks is None:
            jwks_url = f'https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json'
            response = requests.get(jwks_url, timeout=30)
            response.raise_for_status()
            self._jwks = response.json()
        return self._jwks
    
    def decode_token(self, token, verify=False):
        """
        Decode JWT token and extract claims.
        
        WARNING: This demo code decodes tokens without signature verification.
        In production, always verify JWT signatures using JWKS from Cognito.
        See: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
        """
        try:
            if verify:
                # For production, implement proper JWT verification
                # This requires fetching and validating against JWKS
                jwks = self.get_jwks()
                # Implementation of JWT verification with JWKS would go here
                pass
            
            # DEMO ONLY: Decode without verification for local development
            # Production deployments MUST verify JWT signatures
            decoded = jwt.decode(
                token, 
                options={"verify_signature": False},
                algorithms=["RS256"]
            )
            return decoded
            
        except jwt.InvalidTokenError as e:
            return None
    
    def get_user_info(self, access_token):
        """Get user information using access token"""
        try:
            response = self.client.get_user(AccessToken=access_token)
            
            user_attributes = {}
            for attr in response['UserAttributes']:
                user_attributes[attr['Name']] = attr['Value']
            
            return {
                'success': True,
                'username': response['Username'],
                'attributes': user_attributes
            }
            
        except ClientError as e:
            return {
                'success': False,
                'message': e.response['Error']['Message']
            }
    
    def sign_out(self, access_token):
        """Sign out user globally"""
        try:
            self.client.global_sign_out(AccessToken=access_token)
            return {'success': True, 'message': 'Signed out successfully'}
            
        except ClientError as e:
            return {
                'success': False,
                'message': e.response['Error']['Message']
            }