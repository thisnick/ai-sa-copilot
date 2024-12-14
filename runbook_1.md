## Requirements for Databricks Deployment on AWS

### Goals

This section aims to identify and document the prerequisites necessary for successfully deploying Databricks on AWS. This includes understanding the permissions needed within AWS, setting up the required AWS resources such as VPCs and NAT gateways, and evaluating service quotas and creating IAM roles essential for deployment.

### High-level Steps

1. Permission Requirements in AWS
2. Setting up Necessary AWS Resources
3. Service Quotas and IAM Roles

### Permission Requirements in AWS

When setting up Databricks on AWS, specific IAM permissions are crucial for managing infrastructure efficiently. These permissions differ based on whether one is using a Databricks-managed VPC or a customer-managed VPC. 

#### IAM Permissions for Databricks-managed VPCs

To operate in a Databricks-managed VPC, the following permissions are required:

- **ec2:AllocateAddress**: Allocates an Elastic IP associated with the NAT Gateway.
- **ec2:AttachInternetGateway**: Attaches an Internet Gateway to enable connectivity between the Internet and the VPC.
- **ec2:CreateNatGateway**: Creates a NAT Gateway, essential for secure connectivity.
- **ec2:RunInstances**: Launches AWS instances to create Spark Clusters, also used during scaling.

Complete IAM permissions listing and their purposes can be referenced for additional details.

### Setting up Necessary AWS Resources

Setting up AWS infrastructure is integral to deploying Databricks successfully:

- **Virtual Private Cloud (VPC)**: Establish a VPC setup to isolate your AWS resources securely. In a customer-managed VPC, additional configurations like security groups, DNS, and subnet configurations are recommended.
- **NAT Gateway**: Required for handling traffic between instances within the VPC and the Internet in the Databricks-managed VPC setup.

### Service Quotas and IAM Roles

Ensuring that sufficient AWS service quotas are available in your selected region for deploying Databricks is pivotal. Additionally:

- **Evaluate Service Quotas**: Use the AWS Service Quotas console to view and adjust quotas as needed.
- **Create IAM Roles**: Establish cross-account IAM roles with permissions aligning with Databricks deployment needs.

For more information on AWS-specific IAM role configuration, see the detailed instructions available in Databricks documentation.

References:
- [Security and Compliance Guide | Databricks on AWS](https://docs.databricks.com/en/security/index.html)
- [Permissions in Cross-account IAM Roles | Databricks on AWS](https://docs.databricks.com/en/admin/cloud-configurations/aws/permissions.html)

## Step 1: Create a Databricks Workspace

### Goals

The goal of this section is to guide users through the process of successfully creating a Databricks workspace on AWS using AWS Quickstart. This will ensure that users have a properly configured environment to deploy Databricks and begin data processing.

### High-level Steps

1. Sign up and verify account
2. Navigate to Databricks account and initiate workspace setup
3. Use AWS Quickstart for deployment
4. Monitor deployment status until completion

### Sign up and verify account

To begin setting up your Databricks workspace, you must first sign up for a free trial and verify your email address. Once verified, you'll have access to your Databricks account.

### Navigate to Databricks account and initiate workspace setup

1. Upon logging in, follow the on-screen instructions to set up your workspace.
2. In the Databricks account console, click on the 'Workspaces' icon.
3. Select 'Create Workspace'.

### Use AWS Quickstart for deployment

AWS Quickstart offers a streamlined method for deploying Databricks workspaces:

1. Enter a readable name for the workspace. Keep in mind, this cannot be changed later.
2. Choose the AWS region for deployment. Ensure a VPC and NAT gateway exist in your selected cloud region.
3. Click **Start Quickstart**—this process will automatically populate the AWS Console with a CloudFormation template.
4. Check the acknowledgment box for IAM resources' creation.
5. Click **Create stack** in the AWS Console.

### Monitor deployment status until completion

1. Return to the Databricks account console.
2. Monitor the workspace status as it transitions from 'Provisioning' to 'Running'. It should only take a few minutes to complete.

Consider reaching out to [onboarding-help@databricks.com](mailto:onboarding-help@databricks.com) if the deployment encounters issues.

### Additional Considerations

- Administrators may manage workspace assets, user access, and other settings directly through the workspace console once set up.
- It's crucial to validate the setup through required checks like connectivity and configurations post-deployment.

References:
- [Get started: Databricks workspace onboarding | Databricks on AWS](https://docs.databricks.com/en/getting-started/onboarding-account.html)
- [Manually create a workspace | Databricks on AWS](https://docs.databricks.com/en/admin/workspace/create-workspace.html)

## Step 2: Creating and Configuring Compute Resources

### Goals

The goal of this section is to provide a comprehensive guide on setting up and configuring compute resources necessary for Databricks users to perform data processing effectively.

### High-level Steps

1. Open Databricks Workspace
2. Create a Serverless SQL Warehouse
3. Configure Required Permissions for Workspace and Users

### Open Databricks Workspace

1. Log in to the Databricks workspace through your account.
2. Utilize the workspace console interface to navigate towards compute resource settings.

### Create a Serverless SQL Warehouse

A Serverless SQL Warehouse in Databricks allows efficient execution of SQL commands and serves as a key component in handling data processing loads.

1. Within the Databricks console, locate and click the **SQL Warehouses** option in the sidebar menu.
2. Select **Create SQL Warehouse**.
3. Assign a distinct name to the SQL Warehouse for easy identification.
4. Select **Create** to initiate the formation of the Serverless SQL Warehouse.
5. Set permissions by adding `All Users` under the permissions modal and confirm by clicking **Add**.

### Configure Required Permissions for Workspace and Users

1. Navigate back to the main settings in the Databricks console.
2. Configure and manage user permissions to ensure seamless access control tailored to organizational needs.
   - Implement access control lists to determine user access to different Databricks objects like clusters or data tables.
3. Utilize Unity Catalog to manage data privileges effectively.

References:
- [Get started: Databricks workspace onboarding | Databricks on AWS](https://docs.databricks.com/en/getting-started/onboarding-account.html)
- [Cluster Configuration for Databricks Connect | Databricks on AWS](https://docs.databricks.com/en/dev-tools/databricks-connect/cluster-config.html)

## Step 3: Connecting Databricks to Data Sources

### Goals

The primary goal of this section is to guide users through linking their Databricks workspace to cloud data storage services, ensuring efficient access and processing of data.

### High-level Steps

1. Create External Location within Databricks
2. Use AWS S3 Buckets for Data Storage
3. Verify Connectivity and Test Data Flow

### Create External Location within Databricks

An external location in Databricks defines a path in cloud storage that maps with storage credentials.

1. In the Databricks workspace, click **Catalog** in the sidebar.
2. Click **+ Add** at the top of the page, and select **Add an external location**.
3. Enter the name of the AWS S3 bucket you want to connect to.
4. Click **Generate New Token** and copy the token.
5. Click **Launch in Quickstart** and enter the token in the AWS console under **Databricks Personal Access Token**.
6. Acknowledge any AWS CloudFormation template IAM resource warnings before creating the stack.

### Use AWS S3 Buckets for Data Storage

Using AWS S3 for storage allows easy data management and sharing:

1. Add data to your Databricks environment using the default S3 bucket or external locations.
2. Organize data using Databricks's three-level namespace (catalog.schema.table) for easy management.

### Verify Connectivity and Test Data Flow

To ensure proper connectivity and data flow, verify the setup:

1. In the Databricks workspace, click on the external location to test.
2. Click **Test Connection**.
3. Review test results to confirm successful data integration.

References:
- [Get started: Databricks workspace onboarding | Databricks on AWS](https://docs.databricks.com/en/getting-started/onboarding-account.html)

## Managing Users and Permissions in Databricks

### Goals

The goal of this section is to set up user access and permissions effectively in Databricks, ensuring security and proper data governance.

### High-level Steps

1. Add users to the workspace
2. Grant appropriate permissions based on roles
3. Configure data access hierarchy within Databricks

### Add users to the workspace

1. In the Databricks workspace, navigate to your account settings by clicking your username in the top bar and selecting **Settings**.
2. In the sidebar, select **Identity and Access**.
3. Click **Manage** next to Users.
4. Click **Add user**, then select **Add new**.
5. Enter the user's email address and click **Add**.

Users will receive an email invitation to set up their account.

### Grant appropriate permissions based on roles

1. After adding users, grant necessary permissions for accessing data and resources.
2. Permissions follow a hierarchical model in Databricks, where granting permissions at a higher level (e.g., catalog or schema) propagates permissions to contained objects.
3. Use access control lists (ACLs) to define who can perform operations on different Databricks objects.

### Configure data access hierarchy within Databricks

1. Utilize Unity Catalog for advanced data governance and to specify access privileges.
2. Define external location and storage credential permissions if users need access to data sources outside of Databricks.

For comprehensive permission management, refer to Unity Catalog privileges and securable objects.

References
- [Get started: Databricks workspace onboarding | Databricks on AWS](https://docs.databricks.com/en/getting-started/onboarding-account.html)