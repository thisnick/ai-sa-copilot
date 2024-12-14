## Prerequisites

### Goals
Ensure all necessary requirements and permissions are in place before starting the Databricks deployment on AWS. This preparation will help avoid deployment issues and ensure a smooth setup process.

### High-level Steps
1. Verify AWS account permissions and access
2. Check AWS service quotas
3. Ensure Databricks account access

### Step 1: Verify AWS Account Permissions and Access

You need permissions in your AWS account to:
- Provision IAM roles
- Create and manage S3 buckets
- Deploy CloudFormation stacks

Ensure you have administrator access or the necessary IAM permissions to perform these actions.

### Step 2: Check AWS Service Quotas

Before deployment, verify you have available service quotas in your chosen AWS region for:
1. VPC (Virtual Private Cloud)
2. NAT gateway

To check your quotas:
1. Navigate to the [AWS Service Quotas console](https://console.aws.amazon.com/servicequotas/home)
2. Review your VPC and NAT gateway limits
3. If needed, request quota increases through the AWS console

### Step 3: Ensure Databricks Account Access

You need:
1. A Databricks account (sign up for a free trial if you don't have one)
2. Account administrator permissions on Databricks
3. Email verification completed for your Databricks account

Note: If you decide to cancel your Databricks subscription later, remember to delete all associated resources from your AWS console to prevent continued costs.

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)

## Step 1: Create Databricks Workspace

### Goals
Deploy your first Databricks workspace on AWS using the quickstart method, which streamlines the process by automatically provisioning required cloud resources.

### High-level Steps
1. Log into Databricks account and start workspace creation
2. Configure basic workspace settings
3. Deploy AWS resources
4. Verify deployment completion

### Step 1: Log into Databricks Account

1. Sign into your Databricks account at [accounts.cloud.databricks.com](https://accounts.cloud.databricks.com)
2. If this is your first time, you'll be automatically guided to the workspace creation flow
3. If not, click on "Create Workspace" to begin

### Step 2: Configure Workspace Settings

1. Enter a human-readable name for your workspace
   - This name cannot be changed later
   - Choose something descriptive that identifies the workspace's purpose

2. Select your AWS region
   - Choose a region where you have verified your service quotas
   - Ensure the region complies with your data residency requirements

### Step 3: Deploy AWS Resources

1. Click "Start Quickstart" to begin the deployment
   - This will open your AWS Console with a pre-populated CloudFormation template

2. In the AWS Console:
   - Review the template parameters (avoid editing to prevent deployment failures)
   - Check the box that says "I acknowledge that AWS CloudFormation might create IAM resources with custom names"
   - Click "Create stack"

### Step 4: Verify Deployment

1. Return to the Databricks account console
2. Wait for the workspace deployment to complete
   - This typically takes a few minutes
   - The status will update automatically

3. Once complete, you can click on the workspace name to access it

Note: If you encounter any deployment errors, contact Databricks support at onboarding-help@databricks.com for troubleshooting assistance.

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)
- [Create a workspace](https://docs.databricks.com/en/admin/workspace/index.html)

## Step 2: Set Up Compute Resources

### Goals
Create a serverless SQL warehouse that will serve as the compute resource for running SQL queries and data processing tasks in your Databricks workspace.

### High-level Steps
1. Navigate to SQL Warehouses section
2. Create new SQL warehouse
3. Configure warehouse settings
4. Set up access permissions

### Step 1: Navigate to SQL Warehouses

1. Open your newly created Databricks workspace
2. In the sidebar menu, click on "SQL Warehouses"
3. This will take you to the compute resources management page

### Step 2: Create SQL Warehouse

1. Click the "Create SQL warehouse" button
2. Enter a descriptive name for your warehouse
   - Choose a name that reflects its intended use
   - The name can be changed later if needed
3. Keep the default settings for basic setup
4. Click "Create"

### Step 3: Configure Access Permissions

1. When prompted in the permissions modal:
   - Enter and select "All Users" in the field
   - Click "Add" to grant access
2. This ensures all workspace users can utilize this compute resource

Note: While Databricks does not charge during the free trial period, AWS will charge for the compute resources that Databricks deploys in your linked AWS account.

Your serverless SQL warehouse should be available immediately for running queries after creation.

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)

## Step 3: Configure Data Access

### Goals
Connect your Databricks workspace to your data sources by creating and configuring external locations for secure data access.

### High-level Steps
1. Create external location for S3 access
2. Generate access token and configure AWS
3. Test connection
4. Verify access

### Step 1: Create External Location

1. Click "Catalog" on the workspace sidebar
2. Click "+ Add" at the top of the page
3. Select "Add an external location"
4. Choose "AWS Quickstart" (recommended method)
5. Enter your S3 bucket name in the "Bucket Name" field

### Step 2: Configure AWS Access

1. Click "Generate New Token" and copy the generated token
2. Click "Launch in Quickstart"
3. In the AWS console:
   - Paste the copied token in the "Databricks Personal Access Token" field
   - Select the acknowledgment checkbox for IAM resource creation
   - Click "Create stack"

### Step 3: Test Connection

1. Return to your Databricks workspace
2. Navigate to "Catalog" in the sidebar
3. Click "External Data" at the bottom of the left navigation
4. Click "External Locations"
5. Find your new external location (named `db_s3_external_databricks-S3-ingest-<id>`)
6. Click on the location and select "Test connection"

### Notes
- Your workspace comes with a default external location that connects to the S3 bucket provisioned with your workspace
- The external location name follows the format: `db_s3_external_databricks-S3-ingest-<id>`
- Always test connections after setup to ensure proper configuration

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)

## Step 4: Manage Users and Permissions

### Goals
Add users to your Databricks workspace and configure appropriate access permissions to ensure secure and controlled access to resources.

### High-level Steps
1. Access workspace settings
2. Add users to workspace
3. Configure user permissions
4. Set up data access privileges

### Step 1: Access Workspace Settings

1. In the top bar of your Databricks workspace, click your username
2. Select "Settings" from the dropdown menu
3. Click "Identity and access" in the sidebar

### Step 2: Add Users to Workspace

1. Next to "Users", click "Manage"
2. Click "Add user", then "Add new"
3. Enter the user's email address
4. Click "Add" to send an invitation
   - New users will receive an email to set up their account
   - They must verify their email address before accessing the workspace

### Step 3: Configure User Permissions

1. Remember these key permission concepts:
   - Permissions are hierarchical and inherited downward
   - Users need both `SELECT` and `USE` permissions for data access
   - Grant minimum required permissions following the principle of least privilege

2. Common permission considerations:
   - For data access: grant `SELECT` on specific schemas or tables
   - For external data sources: grant `CREATE EXTERNAL LOCATION` and `CREATE STORAGE CREDENTIAL`
   - For compute resources: ensure access to required SQL warehouses

### Step 4: Grant Data Access Privileges

1. Navigate to "Catalog" in the sidebar
2. Select the catalog, schema, or table to manage
3. Click "Permissions"
4. Add users or groups and assign appropriate privileges:
   - `USE` for accessing catalogs and schemas
   - `SELECT` for reading data
   - Additional privileges based on user roles and needs

Note: The security model is hierarchical - granting privileges at a higher level (catalog or schema) automatically grants those privileges to all current and future objects within that level.

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)
- [Unity Catalog privileges and securable objects](https://docs.databricks.com/en/data-governance/unity-catalog/manage-privileges/privileges.html)