import os

class Config:
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'insurance_claims')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # AWS Cognito configuration
    COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
    COGNITO_CLIENT_ID = os.getenv('COGNITO_CLIENT_ID')
    COGNITO_CLIENT_SECRET = os.getenv('COGNITO_CLIENT_SECRET')
    
    # Bedrock Knowledge Base
    KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID')