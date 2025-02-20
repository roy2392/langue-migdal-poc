import boto3
import json
import os
import pandas as pd
import sqlite3
import uuid
import zipfile
from botocore.exceptions import ClientError
from pathlib import Path
import time

# AWS Helper Functions
def get_account_id():
    sts_client = boto3.client('sts')
    return sts_client.get_caller_identity()['Account']

def create_unique_bucket_name(base_name):
    account_id = get_account_id()
    random_suffix = uuid.uuid4().hex[:6]
    return f"{base_name}-{account_id}-{random_suffix}"

# S3 Bucket Creation and Setup
def create_s3_bucket_with_permissions(base_bucket_name, region='us-west-2'):
    bucket_name = create_unique_bucket_name(base_bucket_name)
    s3_client = boto3.client('s3')
    s3 = boto3.resource('s3')
    
    try:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
        print(f"Created bucket: {bucket_name}")

        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowAthenaAccess",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "athena.amazonaws.com"
                    },
                    "Action": [
                        "s3:GetBucketLocation",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:PutObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                },
                {
                    "Sid": "AllowCurrentUserReadWrite",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": boto3.client('sts').get_caller_identity()['Arn']
                    },
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket",
                        "s3:GetBucketLocation"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
            ]
        }

        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print("Applied bucket policy")
        return bucket_name

    except ClientError as e:
        print(f"Error: {e}")
        return None

# Data Processing Functions
def create_and_unzip(first_zip, new_directory, second_zip):
    notebook_dir = Path.cwd()
    new_dir = Path(new_directory)
    new_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {new_dir}")
    
    with zipfile.ZipFile(first_zip, 'r') as zip_ref:
        zip_ref.extractall(new_directory)
    print(f"Unzipped {first_zip} to {new_directory}")
    
    subdirs = [d for d in new_dir.iterdir() if d.is_dir()]

    if subdirs:
        auto_found_dir = subdirs[0]
        print(f"Found directory: {auto_found_dir}")
        second_zip_path = auto_found_dir / second_zip
        print(second_zip_path)
        if second_zip_path.exists():
            with zipfile.ZipFile(second_zip_path, 'r') as zip_ref:
                zip_ref.extractall(notebook_dir)
            print(f"Unzipped {second_zip} in {notebook_dir}")
        else:
            print(f"Could not find {second_zip} in {auto_found_dir}")
    else:
        print(f"No directories found in {new_dir}")

def process_database_and_upload(database_folder, bucket_name):
    folder_path = Path(database_folder)
    database_name = folder_path.name
    
    sqlite_files = list(folder_path.glob('*.db')) + list(folder_path.glob('*.sqlite'))
    if not sqlite_files:
        print(f"No SQLite file found in {database_folder}")
        return
    
    sqlite_file = sqlite_files[0]
    print(f"\nProcessing database: {database_name}")
    print(f"SQLite file: {sqlite_file}")
    
    try:
        conn = sqlite3.connect(sqlite_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        s3_client = boto3.client('s3')
        
        for table in tables:
            table_name = table[0]
            print(f"\nProcessing table: {table_name}")
            
            try:
                df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
                parquet_filename = f"{table_name}.parquet"
                local_parquet_path = folder_path / parquet_filename
                df.to_parquet(local_parquet_path, index=False)
                
                s3_key = f"{database_name}/{parquet_filename}"
                s3_client.upload_file(
                    str(local_parquet_path),
                    bucket_name,
                    s3_key
                )
                print(f"Uploaded to s3://{bucket_name}/{s3_key}")
                os.remove(local_parquet_path)
                
            except Exception as e:
                print(f"Error processing table {table_name}: {str(e)}")
                continue
        
        conn.close()
        
    except Exception as e:
        print(f"Error processing database {database_name}: {str(e)}")
        return

# Athena Setup Functions
def add_athena_permissions(data_bucket, results_bucket):
    iam = boto3.client('iam')
    sts = boto3.client('sts')

    # Get current user/role info
    caller_identity = sts.get_caller_identity()
    current_user_arn = caller_identity['Arn']
    account_id = caller_identity['Account']
    region = boto3.session.Session().region_name

    # Define the policy
    athena_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "athena:*"
                ],
                "Resource": [
                    f"arn:aws:athena:*:{account_id}:capacity-reservation/*",
                    f"arn:aws:athena:*:{account_id}:workgroup/primary",
                    f"arn:aws:athena:*:{account_id}:datacatalog/*"
                ]
            },

            {
                # Data bucket permissions (read-only)
                "Effect": "Allow",
                "Action": [
                    "s3:GetBucketLocation",
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{data_bucket}",
                    f"arn:aws:s3:::{data_bucket}/*"
                ]
            },
            {
                # Results bucket permissions (read and write)
                "Effect": "Allow",
                "Action": [
                    "s3:GetBucketLocation",
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject",
                    "s3:ListMultipartUploadParts",
                    "s3:AbortMultipartUpload"
                ],
                "Resource": [
                    f"arn:aws:s3:::{results_bucket}",
                    f"arn:aws:s3:::{results_bucket}/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "glue:CreateDatabase",
                    "glue:DeleteDatabase",
                    "glue:GetCatalog",
                    "glue:GetCatalogs",
                    "glue:GetDatabase",
                    "glue:GetDatabases",
                    "glue:UpdateDatabase",
                    "glue:CreateTable",
                    "glue:DeleteTable",
                    "glue:BatchDeleteTable",
                    "glue:UpdateTable",
                    "glue:GetTable",
                    "glue:GetTables",
                    "glue:BatchCreatePartition",
                    "glue:CreatePartition",
                    "glue:DeletePartition",
                    "glue:BatchDeletePartition",
                    "glue:UpdatePartition",
                    "glue:GetPartition",
                    "glue:GetPartitions",
                    "glue:BatchGetPartition",
                    "glue:StartColumnStatisticsTaskRun",
                    "glue:GetColumnStatisticsTaskRun",
                    "glue:GetColumnStatisticsTaskRuns",
                    "glue:GetCatalogImportStatus"
                ],
                "Resource": [
                    f"arn:aws:glue:*:{account_id}:catalog",
                    f"arn:aws:glue:*:{account_id}:database/*",
                    f"arn:aws:glue:*:{account_id}:table/*"
                ]
            }
        ]
    }

    try:
        # Delete existing policy if it exists
        try:
            existing_policies = iam.list_policies(Scope='Local')['Policies']
            for policy in existing_policies:
                if policy['PolicyName'] == 'AthenaQueryPermissions':
                    policy_arn= policy['Arn']
                    # First detach from user if it exists
                    if ':user/' in current_user_arn:
                        username = current_user_arn.split('/')[-1]
                        try:
                            iam.detach_user_policy(
                                UserName=username,
                                PolicyArn=policy_arn
                            )
                            print(f"Detached existing policy from user: {username}")
                        except Exception as e:
                            print(f"Note when detaching from user: {e}")
                    
                    # Then detach from role if it exists
                    elif ':assumed-role/' in current_user_arn:
                        role_name = current_user_arn.split('/')[-2]
                        try:
                            iam.detach_role_policy(
                                RoleName=role_name,
                                PolicyArn=policy_arn
                            )
                            print(f"Detached existing policy from role: {role_name}")
                        except Exception as e:
                            print(f"Note when detaching from role: {e}")
                    
                    # Finally delete the policy
                    try:
                        iam.delete_policy(PolicyArn=policy_arn)
                        print("Deleted existing policy")
                    except Exception as e:
                        print(f"Note when deleting policy: {e}")
        except Exception as e:
            print(f"Note: {e}")

        # Create the policy
        response = iam.create_policy(
            PolicyName='AthenaQueryPermissions',
            PolicyDocument=json.dumps(athena_policy)
        )
        policy_arn = response['Policy']['Arn']
        print(f"Created policy: {policy_arn}")

        # Attach the policy to the current user/role
        if ':user/' in current_user_arn:
            username = current_user_arn.split('/')[-1]
            try:
                iam.detach_user_policy(
                    UserName=username,
                    PolicyArn=policy_arn
                )
            except:
                pass
            iam.attach_user_policy(
                UserName=username,
                PolicyArn=policy_arn
            )
            print(f"Attached policy to user: {username}")
        elif ':assumed-role/' in current_user_arn:
            role_name = current_user_arn.split('/')[-2]
            try:
                iam.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
            except:
                pass
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"Attached policy to role: {role_name}")

        print("Successfully added Athena permissions with specific bucket access")
        return True

    except Exception as e:
        print(f"Error adding permissions: {e}")
        return False


def set_athena_result_location(result_bucket):
    try:
        athena_client = boto3.client('athena')
        s3_output_location = f's3://{result_bucket}/athena-results/'
        
        response = athena_client.update_work_group(
            WorkGroup='primary',
            ConfigurationUpdates={
                'ResultConfigurationUpdates': {
                    'OutputLocation': s3_output_location
                },
                'EnforceWorkGroupConfiguration': True
            }
        )
        
        print(f"Successfully set Athena query result location to: {s3_output_location}")
        return True
        
    except Exception as e:
        print(f"Error setting result location: {e}")
        return False

def list_s3_folders_and_files(bucket_name):
    """Get all database folders and their parquet files"""
    s3_client = boto3.client('s3')
    
    try:
        # Get all objects in bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        database_tables = {}
        
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                # Split the key into parts
                parts = obj['Key'].split('/')
                
                # Check if it's a parquet file
                if len(parts) >= 2 and parts[-1].endswith('.parquet'):
                    database_name = parts[0]
                    table_name = parts[-1].replace('.parquet', '')
                    
                    if database_name not in database_tables:
                        database_tables[database_name] = []
                    database_tables[database_name].append(table_name)
        
        return database_tables
    
    except ClientError as e:
        print(f"Error listing S3 contents: {e}")
        return None


def generate_and_create_table(results_bucket_name, parquet_bucket_name, database_name, table_name):
    """Generate and create a single table"""
    try:
        # Generate DDL
        s3_path = f's3://{parquet_bucket_name}/{database_name}/{table_name}.parquet'
        df = pd.read_parquet(s3_path)
        
        # Map pandas types to Athena types
        type_mapping = {
            'object': 'string',
            'int64': 'int',
            'float64': 'double',
            'bool': 'boolean',
            'datetime64[ns]': 'timestamp'
        }
        
        # Generate column definitions
        columns = []
        for col, dtype in df.dtypes.items():
            athena_type = type_mapping.get(str(dtype), 'string')
            columns.append(f"`{col}` {athena_type}")
        
        # Create DDL statement
        column_definitions = ',\n    '.join(columns)
        s3_location = f's3://{parquet_bucket_name}/{database_name}/'
        
        ddl = f"""CREATE EXTERNAL TABLE IF NOT EXISTS {database_name}.{table_name} (
        {column_definitions}
    )
    STORED AS PARQUET
    LOCATION '{s3_location}';"""
        
        print(f"\nGenerating table: {database_name}.{table_name}")
        
        # Execute DDL
        athena_client = boto3.client('athena')
        
        # Create table
        response = athena_client.start_query_execution(
            QueryString=ddl,
            QueryExecutionContext={
                'Database': database_name
            },
            ResultConfiguration={
                'OutputLocation': f's3://{results_bucket_name}/athena-results/'
            }
        )
        
        # Wait for table creation
        query_execution_id = response['QueryExecutionId']
        while True:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            state = response['QueryExecution']['Status']['State']
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(1)
        
        if state == 'SUCCEEDED':
            print(f"Created table: {database_name}.{table_name}")
            return True
        else:
            print(f"Failed to create table {database_name}.{table_name}: {state}")
            return False
            
    except Exception as e:
        print(f"Error creating table {database_name}.{table_name}: {e}")
        return False

def create_all_databases_and_tables(results_bucket_name, parquet_bucket_name):
    """Create all databases and tables from S3 bucket structure"""
    try:
        # Get database and table structure from S3
        database_tables = list_s3_folders_and_files(parquet_bucket_name)
        if not database_tables:
            print("No databases/tables found in S3")
            return False
            
        athena_client = boto3.client('athena')
        
        # Process each database
        for database_name, tables in database_tables.items():
            print(f"\nProcessing database: {database_name}")
            
            # Create database
            create_database = f"CREATE DATABASE IF NOT EXISTS {database_name}"
            response = athena_client.start_query_execution(
                QueryString=create_database,
                ResultConfiguration={
                    'OutputLocation': f's3://{results_bucket_name}/athena-results/'
                }
            )
            
            # Wait for database creation
            query_execution_id = response['QueryExecutionId']
            while True:
                response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
                state = response['QueryExecution']['Status']['State']
                if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                    break
                time.sleep(1)
            
            if state == 'SUCCEEDED':
                print(f"Created database: {database_name}")
                
                # Create each table in the database
                for table_name in tables:
                    generate_and_create_table(
                        results_bucket_name,
                        parquet_bucket_name,
                        database_name,
                        table_name
                    )
            else:
                print(f"Failed to create database {database_name}: {state}")
                continue
        
        return True
        
    except Exception as e:
        print(f"Error in create_all_databases_and_tables: {e}")
        return False

def main():
    # Configuration
    REGION = 'us-west-2'
    BASE_BUCKET_NAME = 'text2sql-agent'
    ATHENA_RESULTS_BUCKET_NAME = 'text2sql-athena-results'
    BASE_DIR = 'dev_databases'

    # Step 1: Unzip files
    create_and_unzip(
        first_zip='dev.zip',
        new_directory='unzipped_dev',
        second_zip='dev_databases.zip'
    )

    # Step 2: Create buckets
    main_bucket = create_s3_bucket_with_permissions(BASE_BUCKET_NAME, REGION)
    athena_results_bucket = create_s3_bucket_with_permissions(ATHENA_RESULTS_BUCKET_NAME, REGION)

    if not all([main_bucket, athena_results_bucket]):
        print("Failed to create required buckets")
        return

    # Step 3: Process and upload databases
    base_path = Path(BASE_DIR)
    for database_folder in base_path.iterdir():
        if database_folder.is_dir():
            process_database_and_upload(database_folder, main_bucket)

    # Step 4: Setup Athena permissions and configuration
    add_athena_permissions(main_bucket, athena_results_bucket)
    set_athena_result_location(athena_results_bucket)

    # Step 5: Create Athena databases and tables
    success = create_all_databases_and_tables(athena_results_bucket, main_bucket)
    if success:
        print("\nCompleted creating all databases and tables in Athena!")

if __name__ == "__main__":
    main()
