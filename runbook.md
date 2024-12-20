## Sign Up for Databricks

### Goals

This section aims to guide you through setting up a Databricks account, allowing you to be prepared for creating and managing a workspace on AWS.

### High-level Steps

1. Create an AWS account (if not already available)
2. Choose a sign-up method: via Databricks directly or through AWS Marketplace.
3. Follow the sign-up process specific to the method chosen (email verification, creating passwords, etc.).
4. Manage billing options during or post-trial if required.

### Step 1: Create an AWS Account

1. Navigate to the [AWS website](https://aws.amazon.com/).
2. Follow the instructions to sign up for a new account if you do not already have one. This step is necessary as Databricks requires compute and storage resources from your AWS account.

### Step 2: Choose a Sign-Up Method

- **Through Databricks Directly:**
  1. Visit the [Try Databricks](https://databricks.com/try-databricks) page.
  2. Enter your name, company, email, and title, then click **Continue**.
  3. Select **Amazon Web Services** as your cloud provider and click **Get started**.
  4. Verify your email address through the link sent to you.
  5. Proceed to create your workspace from the Databricks account console.

- **Through AWS Marketplace:**
  1. Log in to your AWS account with Purchaser role access.
  2. Navigate to [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-wtyi5lgtce6n6).
  3. Select **View purchase options** then click **Subscribe**.
  4. Complete the email verification process and set your password to access Databricks account console.

### Step 3: Manage Billing Options

- For **Direct Databricks signup**, add billing information to maintain account utility post-trial. This involves:
  1. Logging in to the account console and accessing **Subscription & Billing** under settings.
  2. Adding and saving your billing information.
- For **AWS Marketplace**, billing is managed alongside your AWS charges post-trial.

References:
- [Start a Databricks free trial](https://databricks.com/try-databricks)
- [AWS website](https://aws.amazon.com/)

## Set Up Databricks Workspace

### Goals

The aim of this section is to help establish a Databricks workspace on AWS, ensuring that you have a ready environment for data processing and analytics.

### High-level Steps

1. Verify necessary permissions in AWS (IAM roles, S3 buckets, VPC, NAT gateway).
2. Initiate workspace setup in chosen AWS region using AWS CloudFormation.
3. Name the workspace and complete stack creation through AWS console.

### Step 1: Verify Necessary Permissions in AWS

1. Ensure that you have the permission to provision IAM roles and S3 buckets in your AWS account.
2. Check that you have available service quotas for a Databricks deployment in your AWS region, including a Virtual Private Cloud (VPC) and a Network Address Translation (NAT) gateway.

### Step 2: Initiate Workspace Setup

1. Sign into your Databricks account.
2. Follow the instructions provided in the Databricks account console to set up your workspace.
3. Select the AWS region for the deployment and ensure necessary network configurations are available.

### Step 3: Complete Workspace Creation

1. Click **Start Quickstart** to open the AWS Console with a prepopulated CloudFormation template.
2. Check "I acknowledge that AWS CloudFormation might create IAM resources with custom names."
3. Click **Create stack** to begin the setup.
4. Return to the Databricks account console and wait for the workspace to finish deploying.

### Troubleshooting

- If deployment fails, refrain from editing additional fields in the CloudFormation template.
- For additional support, contact [onboarding-help@databricks.com](mailto:onboarding-help@databricks.com).

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)

## Create Compute Resources

### Goals

The goal of this section is to guide you in creating a compute resource, specifically a serverless SQL warehouse, which will allow you to run queries efficiently.

### High-level Steps

1. Open Databricks workspace.
2. Navigate to SQL Warehouses.
3. Create SQL Warehouse and set permissions for access.

### Step 1: Open Databricks Workspace

1. Go to your Databricks account and log in.
2. Access your previously set up Databricks workspace.

### Step 2: Navigate to SQL Warehouses

1. Once in the workspace interface, locate the sidebar menu.
2. Click on **SQL Warehouses** to go to the SQL management area.

### Step 3: Create SQL Warehouse

1. Click the **Create SQL Warehouse** button.
2. Provide a name for your SQL warehouse to identify it easily.
3. Click **Create** to establish the SQL warehouse.

### Step 4: Set Permissions

1. After creating the warehouse, a permissions modal will appear.
2. Enter `All Users` into the permission field, then click **Add**.
3. Confirm that your SQL warehouse is operational and available for SQL queries.

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)

## Connect to Data Sources

### Goals

In this section, the focus is on establishing a connection between the Databricks workspace and your data storage sources in AWS, specifically using Amazon S3.

### High-level Steps

1. Navigate to Databricks Catalog.
2. Create an external location using AWS Quickstart for S3.
3. Test connection to ensure proper setup.

### Step 1: Navigate to Databricks Catalog

1. In your Databricks workspace, click **Catalog** on the sidebar.

### Step 2: Create an External Location

1. At the top of the page, click **+ Add**.
2. Click **Add an external location**.
3. Use **AWS Quickstart** to ensure that your workspace is given the correct permissions on the S3 bucket.
4. Enter the bucket name from which you want to import data.
5. Click **Generate New Token** and copy the token.
6. Click **Launch in Quickstart**.
7. Enter the copied token in the **Databricks Personal Access Token** field in your AWS console.
8. Check the option "I acknowledge that AWS CloudFormation might create IAM resources with custom names."
9. Click **Create stack**.

### Step 3: Test Your Connection

1. Navigate back to the external locations in your workspace.
2. Click on the external location you've set up.
3. Click **Test connection** to ensure the setup works.

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)

## Add Users and Set Permissions

### Goals

This section focuses on allowing multiple users to access and work within the Databricks workspace by adding them and setting their permissions according to roles and needs.

### High-level Steps

1. Add users to Databricks workspace from settings.
2. Set permissions according to user roles and needs.

### Step 1: Add Users

1. In the top bar of the Databricks workspace, click your username and then click **Settings**.
2. In the sidebar, click **Identity and access**.
3. Next to **Users**, click **Manage**.
4. Click **Add user**, and then click **Add new**.
5. Enter the user’s email address, and then click **Add**.

### Step 2: Set Permissions

1. Once users are added, define the permissions that meet your organization’s data governance policy.
2. Common permissions include:
   - Granting users `SELECT` permissions on catalogs or schemas.
   - Setting `USE` permissions on the objects for accessing specific data.
   - Granting `CREATE EXTERNAL LOCATION` for connection to external data sources.
3. Ensure permissions are cascaded properly if assigning to higher-level objects such as catalogs and schemas.

References:
- [Get started: Databricks workspace onboarding](https://docs.databricks.com/en/getting-started/onboarding-account.html)

## Install Databricks CLI

### Goals

The objective of this section is to provide guidance on setting up the Databricks Command-Line Interface (CLI), which facilitates advanced management and automation options for your Databricks environment.

### High-level Steps

1. Choose installation method: Homebrew, WinGet, or Source.
2. Follow the appropriate installation steps for your operating system.
3. Authenticate CLI using Databricks account details.

### Step 1: Choose Installation Method
Databricks CLI can be installed using several methods depending on your operating system:

- **Homebrew (Linux/MacOS):**
  1. Install Homebrew if not already installed:
     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```
  2. Tap the Databricks repo and install:
     ```bash
     brew tap databricks/tap
     brew install databricks
     ```
- **WinGet or Chocolatey (Windows):**
  1. Use WinGet:
     ```bash
     winget install Databricks.DatabricksCLI
     ```
  2. Alternatively, use Chocolatey:
     ```bash
     choco install databricks-cli
     ```
- **Source (Linux/MacOS/Windows):**
  1. Download the `.zip` file from the [Databricks CLI's GitHub Releases](https://github.com/databricks/cli/releases).
  2. Extract and move the executable to a directory included in your `PATH`.

### Step 2: Verify Installation

1. Open your command prompt or terminal.
2. Execute `databricks -v` or `databricks version` to ensure the correct installation:
   ```bash
   databricks -v
   # Or:
   databricks version
   ```
   - If the version number is 0.205.0 or higher, the installation is valid.

### Step 3: Authenticate CLI

The final step is to authenticate the Databricks CLI:

1. Run the authentication command:
   ```bash
   databricks configure --token
   ```
2. Enter your Databricks host URL and your personal access token when prompted.

References:
- [Databricks CLI Installation Guide](https://docs.databricks.com/en/dev-tools/cli/install.html)