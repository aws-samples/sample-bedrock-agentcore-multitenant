"""
AWS resource management utilities for multi-tenant samples.
Handles resource creation and reuse across notebook executions.
"""

import boto3
import json
import time
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth


class CognitoManager:
    """Manage Cognito User Pools and users"""

    def __init__(self, region: str):
        self.client = boto3.client("cognito-idp", region_name=region)
        self.region = region

    def get_or_create_user_pool(self, pool_name: str, **kwargs):
        """Get existing user pool or create new one"""
        # Check if pool exists
        try:
            pools = self.client.list_user_pools(MaxResults=60)
            for pool in pools.get("UserPools", []):
                if pool["Name"] == pool_name:
                    pool_id = pool["Id"]
                    print(f"✓ Found existing user pool: {pool_id}")

                    # Get app client
                    clients = self.client.list_user_pool_clients(
                        UserPoolId=pool_id, MaxResults=60
                    )

                    if clients.get("UserPoolClients"):
                        client_id = clients["UserPoolClients"][0]["ClientId"]
                    else:
                        # Create app client
                        client_response = self.client.create_user_pool_client(
                            UserPoolId=pool_id,
                            ClientName=f"{pool_name}-client",
                            ExplicitAuthFlows=[
                                "ALLOW_USER_PASSWORD_AUTH",
                                "ALLOW_REFRESH_TOKEN_AUTH",
                            ],
                        )
                        client_id = client_response["UserPoolClient"]["ClientId"]

                    return {
                        "user_pool_id": pool_id,
                        "client_id": client_id,
                        "discovery_url": f"https://cognito-idp.{self.region}.amazonaws.com/{pool_id}/.well-known/openid-configuration",
                    }
        except ClientError as e:
            print(f"Error checking pools: {e}")

        # Create new pool
        print(f"Creating new user pool: {pool_name}")

        schema = kwargs.get("schema", [])
        auto_verified = kwargs.get("auto_verified_attributes", ["email"])

        response = self.client.create_user_pool(
            PoolName=pool_name,
            Schema=schema,
            AutoVerifiedAttributes=auto_verified,
            Policies={
                "PasswordPolicy": {
                    "MinimumLength": 8,
                    "RequireUppercase": True,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": True,
                }
            },
        )

        pool_id = response["UserPool"]["Id"]

        # Create app client
        client_response = self.client.create_user_pool_client(
            UserPoolId=pool_id,
            ClientName=f"{pool_name}-client",
            ExplicitAuthFlows=["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"],
        )

        client_id = client_response["UserPoolClient"]["ClientId"]

        print(f"✓ Created user pool: {pool_id}")

        return {
            "user_pool_id": pool_id,
            "client_id": client_id,
            "discovery_url": f"https://cognito-idp.{self.region}.amazonaws.com/{pool_id}/.well-known/openid-configuration",
        }

    def get_or_create_user(
        self, user_pool_id: str, username: str, password: str, attributes: list
    ):
        """Get existing user or create new one. Returns dict with 'sub' key."""
        try:
            # Check if user exists
            user_response = self.client.admin_get_user(UserPoolId=user_pool_id, Username=username)
            print(f"  ↻ User exists: {username}")
            # Extract sub from existing user
            sub = None
            for attr in user_response.get('UserAttributes', []):
                if attr['Name'] == 'sub':
                    sub = attr['Value']
                    break
            return {'sub': sub, 'username': username}
        except self.client.exceptions.UserNotFoundException:
            pass

        # Create user
        self.client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=attributes,
            MessageAction="SUPPRESS",
            TemporaryPassword=password,
        )

        # Set permanent password
        self.client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True,
        )

        # Get the created user's sub
        user_response = self.client.admin_get_user(UserPoolId=user_pool_id, Username=username)
        sub = None
        for attr in user_response.get('UserAttributes', []):
            if attr['Name'] == 'sub':
                sub = attr['Value']
                break

        print(f"  ✓ Created user: {username}")
        return {'sub': sub, 'username': username}


class S3Manager:
    """Manage S3 buckets"""

    def __init__(self, region: str):
        self.client = boto3.client("s3", region_name=region)
        self.region = region

    def get_or_create_bucket(self, bucket_name: str):
        """Get existing bucket or create new one"""
        try:
            self.client.head_bucket(Bucket=bucket_name)
            print(f"✓ Found existing bucket: {bucket_name}")
            return bucket_name
        except ClientError:
            pass

        # Create bucket
        print(f"Creating bucket: {bucket_name}")

        if self.region == "us-east-1":
            self.client.create_bucket(Bucket=bucket_name)
        else:
            self.client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self.region},
            )

        print(f"✓ Created bucket: {bucket_name}")
        return bucket_name


class IAMManager:
    """Manage IAM roles and policies"""

    def __init__(self):
        self.client = boto3.client("iam")

    def get_or_create_role(
        self, role_name: str, assume_role_policy: dict, policies: dict = None
    ):
        """Get existing role or create new one"""
        try:
            response = self.client.get_role(RoleName=role_name)
            role_arn = response["Role"]["Arn"]
            print(f"✓ Found existing role: {role_arn}")

            # Update policies if provided
            if policies:
                for policy_name, policy_doc in policies.items():
                    self.client.put_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(policy_doc),
                    )

            return role_arn
        except self.client.exceptions.NoSuchEntityException:
            pass

        # Create role
        print(f"Creating role: {role_name}")

        response = self.client.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )

        role_arn = response["Role"]["Arn"]

        # Attach policies
        if policies:
            for policy_name, policy_doc in policies.items():
                self.client.put_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_doc),
                )

        print(f"✓ Created role: {role_arn}")

        return role_arn


class OpenSearchServerlessManager:
    """Manage OpenSearch Serverless collections"""

    def __init__(self, region: str):
        self.client = boto3.client("opensearchserverless", region_name=region)
        self.region = region
        self.sts_client = boto3.client("sts")
        self.account_id = self.sts_client.get_caller_identity()["Account"]

    def get_or_create_collection(self, collection_name: str, kb_role_arn: str):
        """Create new collection with all required policies (always creates new)"""
        
        # Check if collection exists and delete it along with policies
        try:
            collections = self.client.list_collections(
                collectionFilters={"name": collection_name}
            )
            if collections.get("collectionSummaries"):
                collection_id = collections["collectionSummaries"][0]["id"]
                print(f"  Found existing collection, deleting...")
                self.client.delete_collection(id=collection_id)
                
                # Delete associated policies
                print(f"  Deleting associated policies...")
                policies_to_check = self.client.list_security_policies(type='encryption')
                for policy in policies_to_check.get('securityPolicySummaries', []):
                    try:
                        policy_detail = self.client.get_security_policy(
                            name=policy['name'], type='encryption'
                        )
                        policy_doc = json.loads(policy_detail['securityPolicyDetail']['policy'])
                        for rule in policy_doc.get('Rules', []):
                            if f"collection/{collection_name}" in rule.get('Resource', []):
                                self.client.delete_security_policy(name=policy['name'], type='encryption')
                                print(f"    Deleted encryption policy: {policy['name']}")
                                break
                    except:
                        pass
                
                policies_to_check = self.client.list_security_policies(type='network')
                for policy in policies_to_check.get('securityPolicySummaries', []):
                    try:
                        policy_detail = self.client.get_security_policy(
                            name=policy['name'], type='network'
                        )
                        policy_doc = json.loads(policy_detail['securityPolicyDetail']['policy'])
                        for rule_set in policy_doc:
                            for rule in rule_set.get('Rules', []):
                                if f"collection/{collection_name}" in rule.get('Resource', []):
                                    self.client.delete_security_policy(name=policy['name'], type='network')
                                    print(f"    Deleted network policy: {policy['name']}")
                                    break
                    except:
                        pass
                
                print(f"  Waiting for deletion...")
                time.sleep(30)
        except Exception as e:
            pass
        
        # Create new collection
        print(f"Creating OpenSearch Serverless collection: {collection_name}")
        
        # Get current principal
        sts = boto3.client("sts")
        caller_identity = sts.get_caller_identity()
        current_principal = caller_identity["Arn"]
        account_id = caller_identity["Account"]
        
        # Convert assumed-role ARN to role ARN if needed
        if ":assumed-role/" in current_principal:
            # Extract role name from assumed-role ARN
            # Format: arn:aws:sts::account:assumed-role/role-name/session-name
            role_name = current_principal.split("/")[-2]
            current_principal = f"arn:aws:iam::{account_id}:role/{role_name}"
            print(f"  Converted assumed-role to role ARN: {current_principal}")
        
        # Generate unique policy names
        timestamp = int(time.time())
        policy_prefix = f"kb-{timestamp}"
        
        # Step 1: Create encryption policy
        encryption_policy = {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"],
                }
            ],
            "AWSOwnedKey": True,
        }

        try:
            self.client.create_security_policy(
                name=f"{policy_prefix}-enc",
                type="encryption",
                policy=json.dumps(encryption_policy),
            )
            print(f"  ✓ Created encryption policy")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConflictException":
                print(f"  ↻ Encryption policy exists")
            else:
                raise

        # Step 2: Create network policy
        network_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"],
                    }
                ],
                "AllowFromPublic": True,
            }
        ]

        try:
            self.client.create_security_policy(
                name=f"{policy_prefix}-net",
                type="network",
                policy=json.dumps(network_policy),
            )
            print(f"  ✓ Created network policy")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConflictException":
                print(f"  ↻ Network policy exists")
            else:
                raise

        # Step 3: Create data access policy
        data_access_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:DeleteCollectionItems",
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems",
                        ],
                    },
                    {
                        "ResourceType": "index",
                        "Resource": [f"index/{collection_name}/*"],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument",
                        ],
                    },
                ],
                "Principal": [kb_role_arn, current_principal],
            }
        ]

        try:
            self.client.create_access_policy(
                name=f"{policy_prefix}-acc",
                type="data",
                policy=json.dumps(data_access_policy),
            )
            print(f"  ✓ Created data access policy")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConflictException":
                print(f"  ↻ Data access policy exists")
            else:
                raise

        # Wait for policies to propagate
        print("  Waiting for policies to propagate...")
        time.sleep(15)

        # Step 4: Create collection
        collection_response = self.client.create_collection(
            name=collection_name,
            type="VECTORSEARCH",
            description="Collection for Bedrock Knowledge Base",
        )

        collection_id = collection_response["createCollectionDetail"]["id"]
        collection_arn = collection_response["createCollectionDetail"]["arn"]
        print(f"  ✓ Created collection: {collection_arn}")

        # Step 5: Wait for collection to be active
        print("  Waiting for collection to be active...")
        max_wait = 300
        wait_interval = 15
        elapsed = 0

        while elapsed < max_wait:
            response = self.client.batch_get_collection(ids=[collection_id])
            status = response["collectionDetails"][0]["status"]

            if status == "ACTIVE":
                collection_endpoint = response["collectionDetails"][0][
                    "collectionEndpoint"
                ]
                print(f"  ✓ Collection is ACTIVE")
                break
            elif status == "FAILED":
                raise Exception("Collection creation failed")

            time.sleep(wait_interval)
            elapsed += wait_interval

        if elapsed >= max_wait:
            raise TimeoutError("Collection did not become active")

        return {
            "collection_id": collection_id,
            "collection_arn": collection_arn,
            "collection_endpoint": collection_endpoint,
            "collection_name": collection_name,
        }


        # Generate unique policy names
        timestamp = int(time.time())
        policy_prefix = f"kb-{timestamp}"

        # Step 1: Create encryption policy
        encryption_policy = {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource": [f"collection/{collection_name}"],
                }
            ],
            "AWSOwnedKey": True,
        }

        try:
            self.client.create_security_policy(
                name=f"{policy_prefix}-enc",
                type="encryption",
                policy=json.dumps(encryption_policy),
            )
            print(f"  ✓ Created encryption policy")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConflictException":
                print(f"  ↻ Encryption policy exists")
            else:
                raise

        # Step 2: Create network policy
        network_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"],
                    }
                ],
                "AllowFromPublic": True,
            }
        ]

        try:
            self.client.create_security_policy(
                name=f"{policy_prefix}-net",
                type="network",
                policy=json.dumps(network_policy),
            )
            print(f"  ✓ Created network policy")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConflictException":
                print(f"  ↻ Network policy exists")
            else:
                raise

        # Step 3: Create data access policy
        caller_identity = self.sts_client.get_caller_identity()
        current_principal = caller_identity["Arn"]

        # Convert assumed-role ARN to role ARN if needed
        if ":assumed-role/" in current_principal:
            role_name = current_principal.split("/")[-2]
            current_principal = f"arn:aws:iam::{self.account_id}:role/{role_name}"

        data_access_policy = [
            {
                "Rules": [
                    {
                        "ResourceType": "collection",
                        "Resource": [f"collection/{collection_name}"],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:DeleteCollectionItems",
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems",
                        ],
                    },
                    {
                        "ResourceType": "index",
                        "Resource": [f"index/{collection_name}/*"],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument",
                        ],
                    },
                ],
                "Principal": [kb_role_arn, current_principal],
            }
        ]

        policy_name = f"{policy_prefix}-acc"
        try:
            self.client.create_access_policy(
                name=policy_name, type="data", policy=json.dumps(data_access_policy)
            )
            print(f"  ✓ Created data access policy")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConflictException":
                print(f"  ↻ Data access policy exists, updating...")
                # Get current policy version
                try:
                    current_policy = self.client.get_access_policy(
                        name=policy_name, type="data"
                    )
                    policy_version = current_policy["accessPolicyDetail"][
                        "policyVersion"
                    ]

                    # Update policy
                    self.client.update_access_policy(
                        name=policy_name,
                        type="data",
                        policyVersion=policy_version,
                        policy=json.dumps(data_access_policy),
                    )
                    print(f"  ✓ Updated data access policy with current principal")
                except Exception as update_error:
                    print(f"  ⚠ Could not update policy: {update_error}")
            else:
                raise

        # Wait for policies to propagate
        print("  Waiting for policies to propagate...")
        time.sleep(15)

        # Step 4: Create collection
        collection_response = self.client.create_collection(
            name=collection_name,
            type="VECTORSEARCH",
            description="Collection for Bedrock Knowledge Base",
        )

        collection_id = collection_response["createCollectionDetail"]["id"]
        collection_arn = collection_response["createCollectionDetail"]["arn"]
        print(f"  ✓ Created collection: {collection_arn}")

        # Step 5: Wait for collection to be active
        print("  Waiting for collection to be active...")
        max_wait = 300
        wait_interval = 15
        elapsed = 0

        while elapsed < max_wait:
            response = self.client.batch_get_collection(ids=[collection_id])
            status = response["collectionDetails"][0]["status"]

            if status == "ACTIVE":
                collection_endpoint = response["collectionDetails"][0][
                    "collectionEndpoint"
                ]
                print(f"  ✓ Collection is ACTIVE")
                break
            elif status == "FAILED":
                raise Exception("Collection creation failed")

            time.sleep(wait_interval)
            elapsed += wait_interval

        if elapsed >= max_wait:
            raise TimeoutError("Collection did not become active")

        return {
            "collection_id": collection_id,
            "collection_arn": collection_arn,
            "collection_endpoint": collection_endpoint,
            "collection_name": collection_name,
        }

    def create_vector_index(
        self, collection_endpoint: str, index_name: str = "bedrock-kb-index"
    ):
        """Create vector index in OpenSearch Serverless collection"""

        session = boto3.Session()
        credentials = session.get_credentials()

        # Set up OpenSearch client
        auth = AWSV4SignerAuth(credentials, self.region, "aoss")
        host = collection_endpoint.replace("https://", "")

        os_client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300,
            pool_maxsize=20,
        )

        # Wait for data access policy to propagate AND endpoint to be ready
        print("  Waiting for data access policy propagation and endpoint readiness...")
        time.sleep(60)  # Increased from 20 to 60 seconds
        
        # Test connection (optional, just for verification)
        print("  Testing OpenSearch connection...")
        try:
            info = os_client.info()
            print(f"  ✓ Connected to OpenSearch: {info.get('version', {}).get('number', 'unknown')}")
        except Exception as e:
            print(f"  ⚠ Connection test failed (this is OK, will retry during index creation): {type(e).__name__}")
            print("  Waiting 30s more for endpoint to be ready...")
            time.sleep(30)

        # Create index with retry logic
        max_retries = 5
        retry_delay = 20

        for attempt in range(max_retries):
            try:
                # Refresh credentials and client
                credentials = session.get_credentials()
                auth = AWSV4SignerAuth(credentials, self.region, "aoss")
                os_client = OpenSearch(
                    hosts=[{"host": host, "port": 443}],
                    http_auth=auth,
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=RequestsHttpConnection,
                    timeout=300,
                    pool_maxsize=20,
                )
                
                # Try to create index
                break  # Exit retry loop to proceed to index creation
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠ Attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    print(f"  ⚠ All connection attempts failed, proceeding anyway...")

        # Define index with proper mappings for Bedrock KB
        index_body = {
            "settings": {
                "index.knn": True,
                "number_of_shards": 2,
                "knn.algo_param.ef_search": 512,
            },
            "mappings": {
                "properties": {
                    "bedrock-knowledge-base-default-vector": {
                        "type": "knn_vector",
                        "dimension": 1024,  # Titan Embed Text v2
                        "method": {
                            "name": "hnsw",
                            "engine": "faiss",
                            "parameters": {"ef_construction": 512, "m": 16},
                        },
                    },
                    "AMAZON_BEDROCK_TEXT_CHUNK": {"type": "text"},
                    "AMAZON_BEDROCK_METADATA": {"type": "text", "index": False},
                }
            },
        }

        # Create index with retry
        for attempt in range(max_retries):
            try:
                os_client.indices.create(index=index_name, body=index_body)
                print(f"  ✓ Created vector index: {index_name}")
                break
            except Exception as e:
                error_msg = str(e).lower()
                if "resource_already_exists_exception" in error_msg:
                    print(f"  ↻ Index already exists: {index_name}")
                    break
                elif "authenticationexception" in error_msg or "401" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"  ⚠ Authentication failed, retrying...")
                        time.sleep(retry_delay)
                        # Refresh credentials
                        credentials = session.get_credentials()
                        auth = AWSV4SignerAuth(credentials, self.region, "aoss")
                        os_client = OpenSearch(
                            hosts=[{"host": host, "port": 443}],
                            http_auth=auth,
                            use_ssl=True,
                            verify_certs=True,
                            connection_class=RequestsHttpConnection,
                            timeout=300,
                            pool_maxsize=20,
                        )
                    else:
                        raise
                else:
                    raise

        # Wait for index to be ready
        time.sleep(10)

        return index_name


class PostgreSQLManager:
    """Manage PostgreSQL database with RLS for multi-tenant applications"""

    def __init__(self, host: str, database: str, user: str, password: str):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.RealDictCursor = RealDictCursor

    def connect(self):
        """Connect to PostgreSQL database"""
        import psycopg2

        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            self.conn.autocommit = False
            print(f"✓ Connected to PostgreSQL: {self.host}/{self.database}")
            return self.conn
        except Exception as e:
            print(f"✗ Failed to connect to PostgreSQL: {e}")
            raise

    def create_schema_with_rls(self):
        """Create database schema with Row-Level Security"""
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            # Create tenants table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    tier VARCHAR(50) DEFAULT 'regular',
                    status VARCHAR(50) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create user-tenant mapping
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_tenants (
                    user_sub VARCHAR(255) PRIMARY KEY,
                    tenant_id VARCHAR(255) REFERENCES tenants(tenant_id),
                    email VARCHAR(255) NOT NULL,
                    username VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create claims table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS claims (
                    claim_id SERIAL PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    claim_number VARCHAR(100) NOT NULL UNIQUE,
                    customer_name VARCHAR(255),
                    claim_amount DECIMAL(10, 2),
                    claim_date DATE,
                    status VARCHAR(50),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Enable RLS on claims table
            cur.execute("ALTER TABLE claims ENABLE ROW LEVEL SECURITY")

            # Drop existing policy if exists
            cur.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON claims")

            # Create RLS policy
            cur.execute(
                """
                CREATE POLICY tenant_isolation_policy ON claims
                USING (tenant_id = current_setting('app.current_tenant_id', TRUE))
            """
            )

        self.conn.commit()
        print("✓ Database schema created with Row-Level Security")

    def insert_sample_data(self, tenants_data: dict):
        """Insert sample data for tenants"""
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            # Insert tenants
            for tenant_id, tenant_info in tenants_data.items():
                cur.execute(
                    """
                    INSERT INTO tenants (tenant_id, name, tier)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tenant_id) DO UPDATE
                    SET name = EXCLUDED.name, tier = EXCLUDED.tier
                """,
                    (
                        tenant_id,
                        tenant_info["name"],
                        tenant_info.get("tier", "regular"),
                    ),
                )

                # Insert claims
                for claim in tenant_info.get("claims", []):
                    cur.execute(
                        """
                        INSERT INTO claims (tenant_id, claim_number, customer_name, claim_amount, claim_date, status, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (claim_number) DO NOTHING
                    """,
                        (
                            tenant_id,
                            claim["claim_number"],
                            claim["customer_name"],
                            claim["claim_amount"],
                            claim["claim_date"],
                            claim["status"],
                            claim.get("description", ""),
                        ),
                    )

        self.conn.commit()
        print(f"✓ Sample data inserted for {len(tenants_data)} tenants")

    def map_user_to_tenant(
        self, user_sub: str, tenant_id: str, email: str, username: str = None
    ):
        """Map a Cognito user to a tenant"""
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_tenants (user_sub, tenant_id, email, username)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_sub) DO UPDATE
                SET tenant_id = EXCLUDED.tenant_id, email = EXCLUDED.email, username = EXCLUDED.username
            """,
                (user_sub, tenant_id, email, username),
            )

        self.conn.commit()

    def get_tenant_for_user(self, user_sub: str) -> str:
        """Get tenant_id for a user"""
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT tenant_id FROM user_tenants WHERE user_sub = %s
            """,
                (user_sub,),
            )
            result = cur.fetchone()
            return result[0] if result else None

    def query_with_rls(self, tenant_id: str, query: str, params: tuple = None):
        """Execute a query with RLS context"""
        if not self.conn:
            self.connect()

        with self.conn.cursor(cursor_factory=self.RealDictCursor) as cur:
            # Set tenant context for RLS
            cur.execute("SET app.current_tenant_id = %s", (tenant_id,))

            # Execute query
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)

            return cur.fetchall()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")


class KnowledgeBaseManager:
    """Manage Bedrock Knowledge Bases with OpenSearch Serverless"""

    def __init__(self, region: str):
        self.client = boto3.client("bedrock-agent", region_name=region)
        self.region = region

    def get_or_create_knowledge_base(
        self, kb_name: str, kb_role_arn: str, collection_arn: str, index_name: str
    ):
        """Create new KB (delete existing if found)"""

        # Check if KB exists and delete it properly
        try:
            kbs = self.client.list_knowledge_bases()
            for kb in kbs.get("knowledgeBaseSummaries", []):
                if kb["name"] == kb_name:
                    kb_id = kb["knowledgeBaseId"]
                    print(f"  Found existing Knowledge Base, deleting...")
                    
                    # Step 1: Update data sources to RETAIN policy, then delete
                    try:
                        ds_list = self.client.list_data_sources(knowledgeBaseId=kb_id)
                        for ds in ds_list.get("dataSourceSummaries", []):
                            ds_id = ds["dataSourceId"]
                            print(f"    Updating data source to RETAIN policy: {ds_id}")
                            
                            # Get current data source config
                            try:
                                ds_detail = self.client.get_data_source(
                                    knowledgeBaseId=kb_id,
                                    dataSourceId=ds_id
                                )
                                
                                # Update to RETAIN
                                self.client.update_data_source(
                                    knowledgeBaseId=kb_id,
                                    dataSourceId=ds_id,
                                    name=ds_detail['dataSource']['name'],
                                    dataSourceConfiguration=ds_detail['dataSource']['dataSourceConfiguration'],
                                    dataDeletionPolicy='RETAIN'
                                )
                                print(f"      ✓ Updated to RETAIN policy")
                                time.sleep(5)
                            except ClientError as e:
                                print(f"      ⚠ Could not update policy: {e}")
                            
                            # Now delete
                            try:
                                self.client.delete_data_source(
                                    knowledgeBaseId=kb_id,
                                    dataSourceId=ds_id
                                )
                                print(f"    ✓ Deleted data source: {ds_id}")
                            except ClientError as e:
                                print(f"      ⚠ Delete failed: {e}")
                        
                        if ds_list.get("dataSourceSummaries"):
                            print(f"    Waiting for data sources to be deleted...")
                            time.sleep(20)
                            
                    except ClientError as e:
                        print(f"    ⚠ Error handling data sources: {e}")
                    
                    # Step 2: Delete the Knowledge Base
                    try:
                        self.client.delete_knowledge_base(knowledgeBaseId=kb_id)
                        print(f"  Deleting Knowledge Base...")
                    except ClientError as e:
                        print(f"    ⚠ Delete KB request failed: {e}")
                    
                    # Step 3: Wait for deletion
                    print(f"  Waiting for KB deletion...")
                    max_wait = 120
                    wait_interval = 10
                    elapsed = 0
                    
                    while elapsed < max_wait:
                        try:
                            kb_detail = self.client.get_knowledge_base(knowledgeBaseId=kb_id)
                            status = kb_detail['knowledgeBase']['status']
                            
                            if status == 'DELETING':
                                print(f"    Status: {status}...")
                                time.sleep(wait_interval)
                                elapsed += wait_interval
                            elif status in ['DELETE_UNSUCCESSFUL', 'FAILED']:
                                print(f"  ⚠ KB stuck in {status} state")
                                print(f"  Attempting force cleanup...")
                                
                                # Try one more time with longer wait
                                time.sleep(30)
                                try:
                                    self.client.get_knowledge_base(knowledgeBaseId=kb_id)
                                    # Still exists, give up and let user know
                                    print(f"  ✗ Cannot auto-delete KB. Please delete manually:")
                                    print(f"     1. Go to Bedrock console")
                                    print(f"     2. Delete Knowledge Base: {kb_name}")
                                    print(f"     3. Re-run this cell")
                                    raise Exception(f"Manual cleanup required for KB: {kb_name}")
                                except ClientError as e:
                                    if e.response['Error']['Code'] == 'ResourceNotFoundException':
                                        print(f"  ✓ KB eventually deleted")
                                        break
                                    raise
                            else:
                                print(f"    Unexpected status: {status}")
                                break
                                
                        except ClientError as e:
                            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                                print(f"  ✓ KB deleted successfully")
                                break
                            else:
                                raise
                    
                    # Extra propagation wait
                    print(f"  Waiting for AWS propagation...")
                    time.sleep(10)
                    break
                    
        except ClientError as e:
            if 'ResourceNotFoundException' not in str(e):
                raise

        # Create new KB
        print(f"\nCreating Knowledge Base: {kb_name}")
        
        max_retries = 3
        retry_delay = 15

        for attempt in range(max_retries):
            try:
                response = self.client.create_knowledge_base(
                    name=kb_name,
                    roleArn=kb_role_arn,
                    knowledgeBaseConfiguration={
                        "type": "VECTOR",
                        "vectorKnowledgeBaseConfiguration": {
                            "embeddingModelArn": f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                        },
                    },
                    storageConfiguration={
                        "type": "OPENSEARCH_SERVERLESS",
                        "opensearchServerlessConfiguration": {
                            "collectionArn": collection_arn,
                            "vectorIndexName": index_name,
                            "fieldMapping": {
                                "vectorField": "bedrock-knowledge-base-default-vector",
                                "textField": "AMAZON_BEDROCK_TEXT_CHUNK",
                                "metadataField": "AMAZON_BEDROCK_METADATA",
                            },
                        },
                    },
                )

                kb_id = response["knowledgeBase"]["knowledgeBaseId"]
                print(f"✓ Created Knowledge Base: {kb_id}")
                return kb_id

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_msg = str(e)
                
                if error_code == 'ConflictException':
                    if attempt < max_retries - 1:
                        print(f"  ⚠ KB name conflict (attempt {attempt + 1}/{max_retries})")
                        print(f"  Waiting {retry_delay}s for deletion to propagate...")
                        time.sleep(retry_delay)
                    else:
                        print(f"\n  ✗ KB name still in use after {max_retries} attempts")
                        print(f"  Please manually delete KB '{kb_name}' from console:")
                        print(f"     https://console.aws.amazon.com/bedrock/home?region={self.region}#/knowledge-bases")
                        raise Exception(f"Manual cleanup required: {kb_name}")
                elif "no such index" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"  ⚠ Index not visible yet (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        raise Exception(f"Index not found after {max_retries} attempts")
                else:
                    raise

    def create_data_source(self, kb_id: str, bucket_name: str):
        """Create S3 data source for Knowledge Base"""

        # Check if data source exists
        try:
            ds_list = self.client.list_data_sources(knowledgeBaseId=kb_id)
            if ds_list.get("dataSourceSummaries"):
                ds_id = ds_list["dataSourceSummaries"][0]["dataSourceId"]
                print(f"✓ Found existing data source: {ds_id}")
                return ds_id
        except ClientError:
            pass

        # Create data source
        print(f"Creating data source for bucket: {bucket_name}")

        response = self.client.create_data_source(
            knowledgeBaseId=kb_id,
            name=f"s3-datasource-{int(time.time())}",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {"bucketArn": f"arn:aws:s3:::{bucket_name}"},
            },
        )

        ds_id = response["dataSource"]["dataSourceId"]
        print(f"✓ Created data source: {ds_id}")
        return ds_id

    def sync_data_source(self, kb_id: str, data_source_id: str):
        """Start ingestion job and wait for completion"""

        # Wait for Knowledge Base to be ACTIVE before starting ingestion
        print("Checking Knowledge Base status...")
        max_wait = 300
        wait_interval = 10
        elapsed = 0
        
        while elapsed < max_wait:
            kb_detail = self.client.get_knowledge_base(knowledgeBaseId=kb_id)
            kb_status = kb_detail["knowledgeBase"]["status"]
            
            if kb_status == "ACTIVE":
                print(f"  ✓ Knowledge Base is ACTIVE")
                break
            elif kb_status in ["FAILED", "DELETE_UNSUCCESSFUL"]:
                raise Exception(f"Knowledge Base is in {kb_status} state")
            else:
                print(f"  Status: {kb_status}, waiting...")
                time.sleep(wait_interval)
                elapsed += wait_interval
        
        if elapsed >= max_wait:
            raise TimeoutError("Knowledge Base did not become ACTIVE in time")

        print("Starting ingestion job...")

        response = self.client.start_ingestion_job(
            knowledgeBaseId=kb_id, dataSourceId=data_source_id
        )

        job_id = response["ingestionJob"]["ingestionJobId"]

        # Wait for completion
        while True:
            status_response = self.client.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                ingestionJobId=job_id,
            )
            status = status_response["ingestionJob"]["status"]
            print(f"  Status: {status}")

            if status in ["COMPLETE", "FAILED"]:
                break
            time.sleep(10)

        if status == "COMPLETE":
            stats = status_response["ingestionJob"].get("statistics", {})
            docs_scanned = stats.get("numberOfDocumentsScanned", 0)
            docs_indexed = stats.get("numberOfNewDocumentsIndexed", 0)
            docs_failed = stats.get("numberOfDocumentsFailed", 0)
            print(f"  Ingestion job complete - Scanned: {docs_scanned}, Indexed: {docs_indexed}, Failed: {docs_failed}")

            print(f"✓ Ingestion complete - Scanned: {docs_scanned}, Indexed: {docs_indexed}, Failed: {docs_failed}")
            return True
        else:
            raise Exception(f"Ingestion failed: {status}")


def cleanup_orphaned_opensearch_policies(region: str, prefix: str = "kb-"):
    """
    Cleanup orphaned OpenSearch Serverless policies that don't have associated collections.
    
    This is useful when collections are deleted but their policies remain.
    
    Args:
        region: AWS region
        prefix: Policy name prefix to match (default: "kb-")
    """
    print("\n" + "=" * 60)
    print("CLEANUP: Orphaned OpenSearch Serverless Policies")
    print("=" * 60)
    
    try:
        oss_client = boto3.client("opensearchserverless", region_name=region)
        
        # Get all existing collection names
        existing_collections = set()
        try:
            collections = oss_client.list_collections()
            for col in collections.get("collectionSummaries", []):
                existing_collections.add(col["name"])
        except Exception as e:
            print(f"⚠ Could not list collections: {e}")
        
        deleted_count = 0
        
        # Cleanup encryption and network policies
        for policy_type in ['encryption', 'network']:
            try:
                policies = oss_client.list_security_policies(type=policy_type)
                for policy in policies.get('securityPolicySummaries', []):
                    policy_name = policy['name']
                    if policy_name.startswith(prefix):
                        # Check if this policy has an associated collection
                        try:
                            policy_detail = oss_client.get_security_policy(
                                name=policy_name, type=policy_type
                            )
                            policy_doc = json.loads(policy_detail['securityPolicyDetail']['policy'])
                            
                            # Extract collection name from policy
                            has_active_collection = False
                            if isinstance(policy_doc, dict) and 'Rules' in policy_doc:
                                for rule in policy_doc['Rules']:
                                    for resource in rule.get('Resource', []):
                                        if resource.startswith('collection/'):
                                            col_name = resource.replace('collection/', '')
                                            if col_name in existing_collections:
                                                has_active_collection = True
                                                break
                            
                            if not has_active_collection:
                                oss_client.delete_security_policy(name=policy_name, type=policy_type)
                                print(f"  Deleted orphaned {policy_type} policy: {policy_name}")
                                deleted_count += 1
                        except Exception as e:
                            # If we can't parse, try to delete anyway
                            try:
                                oss_client.delete_security_policy(name=policy_name, type=policy_type)
                                print(f"  Deleted {policy_type} policy: {policy_name}")
                                deleted_count += 1
                            except:
                                pass
            except Exception as e:
                print(f"⚠ Error processing {policy_type} policies: {e}")
        
        # Cleanup data access policies
        try:
            policies = oss_client.list_access_policies(type='data')
            for policy in policies.get('accessPolicySummaries', []):
                policy_name = policy['name']
                if policy_name.startswith(prefix):
                    # Check if this policy has an associated collection
                    try:
                        policy_detail = oss_client.get_access_policy(name=policy_name, type='data')
                        policy_doc = json.loads(policy_detail['accessPolicyDetail']['policy'])
                        
                        has_active_collection = False
                        if isinstance(policy_doc, list):
                            for statement in policy_doc:
                                for rule in statement.get('Rules', []):
                                    for resource in rule.get('Resource', []):
                                        if resource.startswith('collection/'):
                                            col_name = resource.replace('collection/', '')
                                            if col_name in existing_collections:
                                                has_active_collection = True
                                                break
                        
                        if not has_active_collection:
                            oss_client.delete_access_policy(name=policy_name, type='data')
                            print(f"  Deleted orphaned access policy: {policy_name}")
                            deleted_count += 1
                    except Exception as e:
                        # If we can't parse, try to delete anyway
                        try:
                            oss_client.delete_access_policy(name=policy_name, type='data')
                            print(f"  Deleted access policy: {policy_name}")
                            deleted_count += 1
                        except:
                            pass
        except Exception as e:
            print(f"⚠ Error processing access policies: {e}")
        
        print(f"\n✓ Cleanup complete. Deleted {deleted_count} orphaned policies.")
        
    except Exception as e:
        print(f"✗ Error during cleanup: {e}")


def cleanup_knowledge_base_resources(
    region: str,
    kb_name: str = None,
    collection_name: str = None,
    bucket_name: str = None,
    role_name: str = None,
):
    """
    Cleanup all resources created for Knowledge Base tutorial.
    
    Args:
        region: AWS region
        kb_name: Knowledge Base name (optional, will delete if provided)
        collection_name: OpenSearch collection name (optional, will delete if provided)
        bucket_name: S3 bucket name (optional, will delete if provided)
        role_name: IAM role name (optional, will delete if provided)
    """
    print("\n" + "=" * 60)
    print("CLEANUP: Deleting AWS Resources")
    print("=" * 60)
    
    # 1. Delete Knowledge Base (must be first)
    if kb_name:
        print(f"\n[1/4] Deleting Knowledge Base: {kb_name}")
        try:
            kb_manager = KnowledgeBaseManager(region)
            kbs = kb_manager.client.list_knowledge_bases()
            
            for kb in kbs.get("knowledgeBaseSummaries", []):
                if kb["name"] == kb_name:
                    kb_id = kb["knowledgeBaseId"]
                    
                    # Delete data sources first
                    try:
                        ds_list = kb_manager.client.list_data_sources(knowledgeBaseId=kb_id)
                        for ds in ds_list.get("dataSourceSummaries", []):
                            ds_id = ds["dataSourceId"]
                            print(f"  Deleting data source: {ds_id}")
                            kb_manager.client.delete_data_source(
                                knowledgeBaseId=kb_id,
                                dataSourceId=ds_id
                            )
                        if ds_list.get("dataSourceSummaries"):
                            time.sleep(20)
                    except Exception as e:
                        print(f"  ⚠ Error deleting data sources: {e}")
                    
                    # Delete KB
                    print(f"  Deleting KB: {kb_id}")
                    kb_manager.client.delete_knowledge_base(knowledgeBaseId=kb_id)
                    
                    # Wait for deletion
                    max_wait = 120
                    elapsed = 0
                    while elapsed < max_wait:
                        try:
                            kb_manager.client.get_knowledge_base(knowledgeBaseId=kb_id)
                            time.sleep(10)
                            elapsed += 10
                        except ClientError as e:
                            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                                print(f"  ✓ KB deleted")
                                break
                            raise
                    break
            else:
                print(f"  ↻ KB not found: {kb_name}")
        except Exception as e:
            print(f"  ✗ Error deleting KB: {e}")
    
    # 2. Delete OpenSearch Serverless Collection
    if collection_name:
        print(f"\n[2/4] Deleting OpenSearch Collection: {collection_name}")
        try:
            oss_manager = OpenSearchServerlessManager(region)
            collections = oss_manager.client.list_collections(
                collectionFilters={"name": collection_name}
            )
            
            if collections.get("collectionSummaries"):
                collection_id = collections["collectionSummaries"][0]["id"]
                print(f"  Deleting collection: {collection_id}")
                oss_manager.client.delete_collection(id=collection_id)
                
                # Wait for deletion
                time.sleep(30)
                print(f"  ✓ Collection deleted")
            else:
                print(f"  ↻ Collection not found: {collection_name}")
            
            # Delete associated policies (regardless of collection existence)
            print(f"  Cleaning up OpenSearch policies...")
            
            # Delete encryption and network policies
            for policy_type in ['encryption', 'network']:
                try:
                    policies = oss_manager.client.list_security_policies(type=policy_type)
                    for policy in policies.get('securityPolicySummaries', []):
                        policy_name = policy['name']
                        # Match policies for this collection or orphaned kb-* policies
                        if collection_name in policy_name:
                            try:
                                oss_manager.client.delete_security_policy(
                                    name=policy_name,
                                    type=policy_type
                                )
                                print(f"    Deleted {policy_type} policy: {policy_name}")
                            except Exception as e:
                                print(f"    ⚠ Could not delete {policy_type} policy {policy_name}: {e}")
                except Exception as e:
                    print(f"    ⚠ Error listing {policy_type} policies: {e}")
            
            # Delete data access policies
            try:
                policies = oss_manager.client.list_access_policies(type='data')
                for policy in policies.get('accessPolicySummaries', []):
                    policy_name = policy['name']
                    if collection_name in policy_name:
                        try:
                            oss_manager.client.delete_access_policy(
                                name=policy_name,
                                type='data'
                            )
                            print(f"    Deleted data access policy: {policy_name}")
                        except Exception as e:
                            print(f"    ⚠ Could not delete access policy {policy_name}: {e}")
            except Exception as e:
                print(f"    ⚠ Error listing access policies: {e}")
                
        except Exception as e:
            print(f"  ✗ Error deleting collection: {e}")
    
    # 3. Delete S3 Bucket
    if bucket_name:
        print(f"\n[3/4] Deleting S3 Bucket: {bucket_name}")
        try:
            s3_client = boto3.client('s3', region_name=region)
            
            # Empty bucket first
            try:
                print(f"  Emptying bucket...")
                paginator = s3_client.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=bucket_name):
                    if 'Contents' in page:
                        objects = [{'Key': obj['Key']} for obj in page['Contents']]
                        s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': objects}
                        )
                        print(f"    Deleted {len(objects)} objects")
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchBucket':
                    raise
            
            # Delete bucket
            try:
                s3_client.delete_bucket(Bucket=bucket_name)
                print(f"  ✓ Bucket deleted")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucket':
                    print(f"  ↻ Bucket not found: {bucket_name}")
                else:
                    raise
        except Exception as e:
            print(f"  ✗ Error deleting bucket: {e}")
    
    # 4. Delete IAM Role
    if role_name:
        print(f"\n[4/4] Deleting IAM Role: {role_name}")
        try:
            iam_client = boto3.client('iam')
            
            # Delete inline policies first
            try:
                policies = iam_client.list_role_policies(RoleName=role_name)
                for policy_name in policies.get('PolicyNames', []):
                    iam_client.delete_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name
                    )
                    print(f"  Deleted inline policy: {policy_name}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise
            
            # Delete role
            try:
                iam_client.delete_role(RoleName=role_name)
                print(f"  ✓ Role deleted")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    print(f"  ↻ Role not found: {role_name}")
                else:
                    raise
        except Exception as e:
            print(f"  ✗ Error deleting role: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Cleanup Complete")
    print("=" * 60)


def cleanup_cognito_resources(
    region: str,
    user_pool_name: str = None,
):
    """
    Cleanup Cognito resources.
    
    Args:
        region: AWS region
        user_pool_name: User pool name to delete (optional)
    """
    if not user_pool_name:
        return
    
    print("\n" + "=" * 60)
    print("CLEANUP: Deleting Cognito Resources")
    print("=" * 60)
    
    try:
        cognito_manager = CognitoManager(region)
        pools = cognito_manager.client.list_user_pools(MaxResults=60)
        
        for pool in pools.get("UserPools", []):
            if pool["Name"] == user_pool_name:
                pool_id = pool["Id"]
                print(f"\nDeleting User Pool: {pool_id}")
                
                # Delete app clients first
                try:
                    clients = cognito_manager.client.list_user_pool_clients(
                        UserPoolId=pool_id,
                        MaxResults=60
                    )
                    for client in clients.get("UserPoolClients", []):
                        cognito_manager.client.delete_user_pool_client(
                            UserPoolId=pool_id,
                            ClientId=client["ClientId"]
                        )
                        print(f"  Deleted app client: {client['ClientId']}")
                except Exception as e:
                    print(f"  ⚠ Error deleting app clients: {e}")
                
                # Delete user pool
                cognito_manager.client.delete_user_pool(UserPoolId=pool_id)
                print(f"  ✓ User Pool deleted")
                break
        else:
            print(f"  ↻ User Pool not found: {user_pool_name}")
    except Exception as e:
        print(f"  ✗ Error deleting User Pool: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Cleanup Complete")
    print("=" * 60)


class AuroraServerlessManager:
    """Manage Aurora Serverless v2 PostgreSQL clusters"""

    def __init__(self, region: str):
        self.rds = boto3.client("rds", region_name=region)
        self.ec2 = boto3.client("ec2", region_name=region)
        self.region = region
        self.account_id = boto3.client("sts").get_caller_identity()["Account"]

    def get_or_create_cluster(
        self,
        cluster_name: str,
        database_name: str = "insurance_claims",
        master_username: str = "postgres",
        master_password: str = None,
    ):
        """Get existing Aurora cluster or create new one"""
        
        # Check if cluster exists
        try:
            response = self.rds.describe_db_clusters(DBClusterIdentifier=cluster_name)
            if response["DBClusters"]:
                cluster = response["DBClusters"][0]
                endpoint = cluster["Endpoint"]
                cluster_arn = cluster["DBClusterArn"]
                secret_arn = f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:{cluster_name}-credentials"
                print(f"✓ Found existing Aurora cluster: {cluster_name}")
                print(f"  Endpoint: {endpoint}")
                return {
                    "cluster_id": cluster_name,
                    "cluster_arn": cluster_arn,
                    "endpoint": endpoint,
                    "port": cluster["Port"],
                    "database": cluster["DatabaseName"],
                    "secret_arn": secret_arn,
                    "status": cluster["Status"],
                }
        except self.rds.exceptions.DBClusterNotFoundFault:
            pass

        if not master_password:
            import secrets
            master_password = secrets.token_urlsafe(16) + "Aa1!"
            print(f"  Generated password: {master_password}")

        print(f"Creating Aurora Serverless v2 cluster: {cluster_name}")

        # Get default VPC and subnets
        vpcs = self.ec2.describe_vpcs(Filters=[{"Name": "is-default", "Values": ["true"]}])
        if not vpcs["Vpcs"]:
            raise Exception("No default VPC found")
        vpc_id = vpcs["Vpcs"][0]["VpcId"]

        subnets = self.ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
        subnet_ids = [s["SubnetId"] for s in subnets["Subnets"][:2]]

        # Create DB subnet group
        subnet_group_name = f"{cluster_name}-subnet-group"
        try:
            self.rds.create_db_subnet_group(
                DBSubnetGroupName=subnet_group_name,
                DBSubnetGroupDescription=f"Subnet group for {cluster_name}",
                SubnetIds=subnet_ids,
            )
            print(f"  ✓ Created subnet group: {subnet_group_name}")
        except self.rds.exceptions.DBSubnetGroupAlreadyExistsFault:
            print(f"  ↻ Subnet group exists: {subnet_group_name}")

        # Create security group
        sg_name = f"{cluster_name}-sg"
        try:
            sg_response = self.ec2.create_security_group(
                GroupName=sg_name,
                Description=f"Security group for {cluster_name}",
                VpcId=vpc_id,
            )
            sg_id = sg_response["GroupId"]
            
            # Allow PostgreSQL access from anywhere (for demo - restrict in production)
            self.ec2.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[{
                    "IpProtocol": "tcp",
                    "FromPort": 5432,
                    "ToPort": 5432,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "PostgreSQL access"}],
                }],
            )
            print(f"  ✓ Created security group: {sg_id}")
        except self.ec2.exceptions.ClientError as e:
            if "InvalidGroup.Duplicate" in str(e):
                sgs = self.ec2.describe_security_groups(
                    Filters=[{"Name": "group-name", "Values": [sg_name]}]
                )
                sg_id = sgs["SecurityGroups"][0]["GroupId"]
                print(f"  ↻ Security group exists: {sg_id}")
            else:
                raise

        # Create Aurora Serverless v2 cluster
        # Use a version compatible with Aurora Serverless v2
        self.rds.create_db_cluster(
            DBClusterIdentifier=cluster_name,
            Engine="aurora-postgresql",
            EngineVersion="16.4",  # Aurora PostgreSQL 16.4 supports Serverless v2
            EngineMode="provisioned",  # Serverless v2 uses provisioned mode
            DatabaseName=database_name,
            MasterUsername=master_username,
            MasterUserPassword=master_password,
            DBSubnetGroupName=subnet_group_name,
            VpcSecurityGroupIds=[sg_id],
            ServerlessV2ScalingConfiguration={
                "MinCapacity": 0.5,  # Minimum ACUs (can scale to 0 with pause)
                "MaxCapacity": 4.0,  # Maximum ACUs
            },
            EnableHttpEndpoint=True,  # Enable Data API
            StorageEncrypted=True,
        )
        print(f"  ✓ Created Aurora cluster")

        # Create Serverless v2 instance
        instance_id = f"{cluster_name}-instance"
        self.rds.create_db_instance(
            DBInstanceIdentifier=instance_id,
            DBInstanceClass="db.serverless",
            Engine="aurora-postgresql",
            DBClusterIdentifier=cluster_name,
        )
        print(f"  ✓ Created Serverless v2 instance: {instance_id}")

        # Store credentials in Secrets Manager for Data API
        secrets_client = boto3.client("secretsmanager", region_name=self.region)
        secret_name = f"{cluster_name}-credentials"
        
        try:
            # Check if secret exists
            secrets_client.describe_secret(SecretId=secret_name)
            # Update existing secret
            secrets_client.put_secret_value(
                SecretId=secret_name,
                SecretString=json.dumps({
                    "username": master_username,
                    "password": master_password,
                    "host": f"{cluster_name}.cluster-{self.region}.rds.amazonaws.com",
                    "port": 5432,
                    "dbname": database_name
                })
            )
            print(f"  ✓ Updated credentials in Secrets Manager")
        except secrets_client.exceptions.ResourceNotFoundException:
            # Create new secret
            secrets_client.create_secret(
                Name=secret_name,
                SecretString=json.dumps({
                    "username": master_username,
                    "password": master_password,
                    "host": f"{cluster_name}.cluster-{self.region}.rds.amazonaws.com",
                    "port": 5432,
                    "dbname": database_name
                })
            )
            print(f"  ✓ Stored credentials in Secrets Manager: {secret_name}")
        
        secret_arn = f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:{secret_name}"

        # Wait for cluster to be available
        print("  Waiting for cluster to be available (this may take 5-10 minutes)...")
        waiter = self.rds.get_waiter("db_cluster_available")
        waiter.wait(
            DBClusterIdentifier=cluster_name,
            WaiterConfig={"Delay": 30, "MaxAttempts": 40}
        )

        # Get endpoint and ARN
        response = self.rds.describe_db_clusters(DBClusterIdentifier=cluster_name)
        cluster = response["DBClusters"][0]
        endpoint = cluster["Endpoint"]
        cluster_arn = cluster["DBClusterArn"]

        print(f"  ✓ Cluster is available")
        print(f"  Endpoint: {endpoint}")

        return {
            "cluster_id": cluster_name,
            "cluster_arn": cluster_arn,
            "endpoint": endpoint,
            "port": cluster["Port"],
            "database": database_name,
            "master_username": master_username,
            "master_password": master_password,
            "secret_arn": secret_arn,
            "status": cluster["Status"],
        }

    def delete_cluster(self, cluster_name: str):
        """Delete Aurora cluster and associated resources"""
        print(f"\nDeleting Aurora cluster: {cluster_name}")

        # Delete instances first
        try:
            instances = self.rds.describe_db_instances(
                Filters=[{"Name": "db-cluster-id", "Values": [cluster_name]}]
            )
            for instance in instances["DBInstances"]:
                instance_id = instance["DBInstanceIdentifier"]
                print(f"  Deleting instance: {instance_id}")
                self.rds.delete_db_instance(
                    DBInstanceIdentifier=instance_id,
                    SkipFinalSnapshot=True,
                )
            
            # Wait for instances to be deleted
            for instance in instances["DBInstances"]:
                instance_id = instance["DBInstanceIdentifier"]
                print(f"  Waiting for instance deletion: {instance_id}")
                waiter = self.rds.get_waiter("db_instance_deleted")
                waiter.wait(
                    DBInstanceIdentifier=instance_id,
                    WaiterConfig={"Delay": 30, "MaxAttempts": 40}
                )
        except Exception as e:
            print(f"  ⚠ Error deleting instances: {e}")

        # Delete cluster
        try:
            self.rds.delete_db_cluster(
                DBClusterIdentifier=cluster_name,
                SkipFinalSnapshot=True,
            )
            print(f"  ✓ Cluster deletion initiated")
            
            # Wait for cluster deletion
            print("  Waiting for cluster deletion...")
            waiter = self.rds.get_waiter("db_cluster_deleted")
            waiter.wait(
                DBClusterIdentifier=cluster_name,
                WaiterConfig={"Delay": 30, "MaxAttempts": 40}
            )
            print(f"  ✓ Cluster deleted")
        except self.rds.exceptions.DBClusterNotFoundFault:
            print(f"  ↻ Cluster not found: {cluster_name}")
        except Exception as e:
            print(f"  ⚠ Error deleting cluster: {e}")

        # Delete subnet group
        subnet_group_name = f"{cluster_name}-subnet-group"
        try:
            self.rds.delete_db_subnet_group(DBSubnetGroupName=subnet_group_name)
            print(f"  ✓ Deleted subnet group: {subnet_group_name}")
        except Exception as e:
            print(f"  ⚠ Error deleting subnet group: {e}")

        # Delete security group
        sg_name = f"{cluster_name}-sg"
        try:
            sgs = self.ec2.describe_security_groups(
                Filters=[{"Name": "group-name", "Values": [sg_name]}]
            )
            if sgs["SecurityGroups"]:
                sg_id = sgs["SecurityGroups"][0]["GroupId"]
                self.ec2.delete_security_group(GroupId=sg_id)
                print(f"  ✓ Deleted security group: {sg_id}")
        except Exception as e:
            print(f"  ⚠ Error deleting security group: {e}")

        print(f"✓ Aurora cluster cleanup complete")


def cleanup_aurora_resources(region: str, cluster_name: str):
    """Cleanup Aurora Serverless resources"""
    print("\n" + "=" * 60)
    print("CLEANUP: Deleting Aurora Serverless Resources")
    print("=" * 60)
    
    aurora = AuroraServerlessManager(region)
    aurora.delete_cluster(cluster_name)
    
    print("\n" + "=" * 60)
    print("✓ Aurora Cleanup Complete")
    print("=" * 60)
