### Step 1: Verify or Create an ECS Cluster
If you already have an ECS cluster named `ewallet-cluster`, you can skip to Step 2. Otherwise, let’s create one.

1. **Log in to the AWS Management Console**:
   - Open your browser and go to `https://console.aws.amazon.com/`.
   - Log in with your AWS credentials.

2. **Navigate to ECS**:
   - In the AWS Management Console, use the search bar at the top and type “ECS”.
   - Click on **Elastic Container Service** to open the ECS dashboard.

3. **Check for Existing Cluster**:
   - In the left sidebar, click **Clusters**.
   - Look for a cluster named `ewallet-cluster`. If it exists, note it and proceed to Step 2.

4. **Create a New Cluster (if needed)**:
   - Click the orange **Create cluster** button in the top-right corner.
   - **Cluster name**: Enter `ewallet-cluster`.
   - **Infrastructure**: Select **AWS Fargate (serverless)** (this is the easiest option as it doesn’t require managing EC2 instances).
   - **Networking**:
     - **VPC**: Select your existing VPC (e.g., the one where your RDS instance resides).
     - **Subnets**: Select your private subnets (e.g., `subnet-12345678`, `subnet-87654321`).
     - **Security group**: Leave as default for now; we’ll configure it later.
   - **Monitoring**: Leave the default settings (CloudWatch Container Insights can be enabled if desired).
   - Click the orange **Create** button at the bottom-right.

5. **Verify the Cluster**:
   - Once created, you’ll see `ewallet-cluster` in the list of clusters. Click on it to view its details.

---

### Step 2: Create or Update an IAM Role for ECS Task Execution
You need an IAM role for ECS tasks to pull images from ECR and send logs to CloudWatch. If you already have a role named `ecsTaskExecutionRole`, skip to Step 3.

1. **Navigate to IAM**:
   - In the AWS Management Console search bar, type “IAM” and click on **IAM**.
   - In the left sidebar, click **Roles**.

2. **Create a New Role**:
   - Click the blue **Create role** button.
   - **Trusted entity type**: Select **AWS service**.
   - **Use case**: Scroll down and select **Elastic Container Service**, then choose **Elastic Container Service Task**.
   - Click **Next**.

3. **Add Permissions**:
   - In the search bar, type `AmazonECSTaskExecutionRolePolicy`.
   - Check the box next to `AmazonECSTaskExecutionRolePolicy` (this policy allows the task to pull images from ECR and send logs to CloudWatch).
   - Click **Next**.

4. **Name the Role**:
   - **Role name**: Enter `ecsTaskExecutionRole`.
   - **Description**: Optionally, add a description like “Role for ECS task execution”.
   - Click **Create role**.

5. **Verify the Role**:
   - Search for `ecsTaskExecutionRole` in the Roles list to confirm it was created.

---

### Step 3: Create or Update Security Groups
You need a security group for the ECS tasks to allow communication between services and with the RDS database. If you already have a security group named `ewallet-ecs-sg`, verify its rules and skip to Step 4.

1. **Navigate to EC2**:
   - In the AWS Management Console search bar, type “EC2” and click on **EC2**.

2. **Go to Security Groups**:
   - In the left sidebar, under **Network & Security**, click **Security Groups**.

3. **Create a New Security Group (if needed)**:
   - Click the orange **Create security group** button.
   - **Security group name**: Enter `ewallet-ecs-sg`.
   - **Description**: Enter “Security group for eWallet ECS tasks”.
   - **VPC**: Select your VPC (the same one used for the ECS cluster and RDS).
   - **Inbound rules**:
     - Click **Add rule**:
       - **Type**: Custom TCP.
       - **Port range**: `5000-5002` (for User Service, Wallet Service, and Frontend Service).
       - **Source**: Select **Custom**, then enter your VPC CIDR (e.g., `10.0.0.0/16`) to allow internal communication between services.
     - Click **Add rule** (if needed for ALB):
       - **Type**: Custom TCP.
       - **Port range**: `5002` (for Frontend Service via ALB).
       - **Source**: Select the security group of your ALB (e.g., `ewallet-alb-sg`, if it exists; we’ll create it later if not).
   - **Outbound rules**: Leave as default (allow all traffic).
   - Click **Create security group**.

4. **Update RDS Security Group**:
   - Find the security group associated with your RDS instance (e.g., `ewallet-db-sg`).
   - Edit its inbound rules:
     - **Type**: MySQL/Aurora.
     - **Port range**: `3306`.
     - **Source**: Select the `ewallet-ecs-sg` security group (this allows ECS tasks to connect to the RDS database).
   - Save the changes.

---

### Step 4: Create or Verify an Application Load Balancer (ALB)
If you already have an ALB named `ewallet-alb` and a target group named `ewallet-frontend-tg`, verify their settings and skip to Step 5.

1. **Navigate to EC2**:
   - In the AWS Management Console, go to **EC2**.

2. **Go to Load Balancers**:
   - In the left sidebar, under **Load Balancing**, click **Load Balancers**.

3. **Create a New ALB (if needed)**:
   - Click the orange **Create load balancer** button.
   - **Load balancer type**: Select **Application Load Balancer**.
   - Click **Create**.
   - **Name**: Enter `ewallet-alb`.
   - **Scheme**: Select **Internet-facing**.
   - **IP address type**: IPv4.
   - **VPC**: Select your VPC.
   - **Mappings**: Select your public subnets (e.g., `subnet-12345678-public`, `subnet-87654321-public`).
   - **Security groups**:
     - Remove the default security group.
     - Add a new security group:
       - Click **Create new security group**.
       - **Name**: `ewallet-alb-sg`.
       - **Description**: “Security group for eWallet ALB”.
       - **Inbound rules**:
         - **Type**: HTTP.
         - **Port range**: `80`.
         - **Source**: `0.0.0.0/0` (allow all traffic for testing; restrict this in production).
       - Click **Create security group**.
     - Select `ewallet-alb-sg`.
   - **Listeners**:
     - **Protocol**: HTTP.
     - **Port**: `80`.
     - **Default action**: Select **Forward to**, then click **Create target group**:
       - **Target group name**: `ewallet-frontend-tg`.
       - **Target type**: IP.
       - **Protocol**: HTTP.
       - **Port**: `5002` (Frontend Service port).
       - **VPC**: Select your VPC.
       - **Health check path**: `/`.
       - Click **Create target group**.
     - Back in the listener setup, select `ewallet-frontend-tg` as the target group.
   - Click **Create load balancer**.

4. **Note the ALB DNS Name**:
   - Once created, click on `ewallet-alb` in the Load Balancers list.
   - Copy the **DNS name** (e.g., `ewallet-alb-1234567890.ap-southeast-1.elb.amazonaws.com`). You’ll use this to access the application later.

---

### Step 5: Create or Update Cloud Map for Service Discovery
If you already have a Cloud Map namespace (`ewallet.local`) and services (`user-service`, `wallet-service`), verify their settings and skip to Step 6.

1. **Navigate to Cloud Map**:
   - In the AWS Management Console search bar, type “Cloud Map” and click on **Cloud Map**.

2. **Create a Namespace (if needed)**:
   - Click **Create namespace**.
   - **Namespace name**: Enter `ewallet.local`.
   - **Namespace type**: Select **Private DNS namespace**.
   - **VPC**: Select your VPC.
   - Click **Create namespace**.

3. **Create Services (if needed)**:
   - In the `ewallet.local` namespace, click **Create service**.
   - **Service 1: User Service**:
     - **Name**: `user-service`.
     - **DNS record type**: A.
     - **Routing policy**: Multivalue answer.
     - **Health check**: Enable if desired (optional).
     - Click **Create service**.
   - **Service 2: Wallet Service**:
     - **Name**: `wallet-service`.
     - **DNS record type**: A.
     - **Routing policy**: Multivalue answer.
     - **Health check**: Enable if desired.
     - Click **Create service**.

---

### Step 6: Create CloudWatch Log Groups
You need CloudWatch Log Groups to store logs for each service. If they already exist, skip to Step 7.

1. **Navigate to CloudWatch**:
   - In the AWS Management Console search bar, type “CloudWatch” and click on **CloudWatch**.

2. **Go to Log Groups**:
   - In the left sidebar, click **Log groups**.

3. **Create Log Groups**:
   - Click **Create log group**.
   - **Log group name**: `/ecs/ewallet-user-service`.
   - Click **Create**.
   - Repeat for:
     - `/ecs/ewallet-wallet-service`
     - `/ecs/ewallet-frontend-service`

Alternatively, you can create these using the AWS CLI:

```bash
aws logs create-log-group --log-group-name /ecs/ewallet-user-service --region ap-southeast-1
aws logs create-log-group --log-group-name /ecs/ewallet-wallet-service --region ap-southeast-1
aws logs create-log-group --log-group-name /ecs/ewallet-frontend-service --region ap-southeast-1
```

---

### Step 7: Create or Update Task Definitions
You need to create or update task definitions for each service. If you already have task definitions (`ewallet-user-service`, `ewallet-wallet-service`, `ewallet-frontend-service`), you can update them by creating new revisions.

1. **Navigate to ECS**:
   - Go back to the ECS dashboard.

2. **Go to Task Definitions**:
   - In the left sidebar, click **Task Definitions**.

3. **Create or Update Task Definitions**:

   #### User Service Task Definition
   - If it exists, select `ewallet-user-service` and click **Create new revision**. If not, click **Create new task definition**.
   - **Task definition family**: `ewallet-user-service`.
   - **Launch type**: Fargate.
   - **Task role**: Leave blank (not needed for this example).
   - **Task execution role**: Select `ecsTaskExecutionRole`.
   - **Operating system family**: Linux.
   - **Task size**:
     - **CPU**: 0.25 vCPU (256).
     - **Memory**: 0.5 GB (512).
   - **Container Definitions**:
     - Click **Add container**.
     - **Container name**: `user-service`.
     - **Image**: `123456789012.dkr.ecr.ap-southeast-1.amazonaws.com/ewallet-user-service:latest`.
     - **Port mappings**:
       - **Container port**: `5000`.
       - **Protocol**: TCP.
     - **Environment**:
       - Under **Environment variables**, click **Add environment variable**:
         - `DB_HOST`: `ewallet-db.abcdef.ap-southeast-1.rds.amazonaws.com`.
         - `DB_USER`: `admin`.
         - `DB_PASSWORD`: `SecurePassword123!` (consider using Secrets Manager in production).
         - `DB_NAME`: `ewallet`.
         - `DB_PORT`: `3306`.
         
     - **Log configuration**:
       - Check **Auto-configure CloudWatch Logs**.
       - **Log group**: `/ecs/ewallet-user-service`.
       - **Log stream prefix**: `ecs`.
     - Click **Add**.
   - Click **Create** (or **Create revision** if updating).

   #### Wallet Service Task Definition
   - Repeat the process for `ewallet-wallet-service`:
     - **Task definition family**: `ewallet-wallet-service`.
     - **Launch type**: Fargate.
     - **Task execution role**: `ecsTaskExecutionRole`.
     - **Task size**: CPU 0.25 vCPU, Memory 0.5 GB.
     - **Container Definitions**:
       - **Container name**: `wallet-service`.
       - **Image**: `123456789012.dkr.ecr.ap-southeast-1.amazonaws.com/ewallet-wallet-service:latest`.
       - **Port mappings**:
         - **Container port**: `5001`.
         - **Protocol**: TCP.
       - **Environment variables** (same as User Service):
         - `DB_HOST`: `ewallet-db.abcdef.ap-southeast-1.rds.amazonaws.com`.
         - `DB_USER`: `admin`.
         - `DB_PASSWORD`: `SecurePassword123!`.
         - `DB_NAME`: `ewallet`.
         - `DB_PORT`: `3306`.
       - **Log configuration**:
         - **Log group**: `/ecs/ewallet-wallet-service`.
         - **Log stream prefix**: `ecs`.
     - Click **Create**.

   #### Frontend Service Task Definition
   - Repeat for `ewallet-frontend-service`:
     - **Task definition family**: `ewallet-frontend-service`.
     - **Launch type**: Fargate.
     - **Task execution role**: `ecsTaskExecutionRole`.
     - **Task size**: CPU 0.25 vCPU, Memory 0.5 GB.
     - **Container Definitions**:
       - **Container name**: `frontend-service`.
       - **Image**: `123456789012.dkr.ecr.ap-southeast-1.amazonaws.com/ewallet-frontend-service:latest`.
       - **Port mappings**:
         - **Container port**: `5002`.
         - **Protocol**: TCP.
       - **Environment variables**:
         - `USER_SERVICE_URL`: `http://user-service.ewallet.local:5000`.
         - `WALLET_SERVICE_URL`: `http://wallet-service.ewallet.local:5001`.
       - **Log configuration**:
         - **Log group**: `/ecs/ewallet-frontend-service`.
         - **Log stream prefix**: `ecs`.
     - Click **Create**.

---

### Step 8: Create or Update ECS Services
Now, deploy the services to the `ewallet-cluster`.

1. **Go to the Cluster**:
   - In the ECS dashboard, click **Clusters** in the left sidebar.
   - Click on `ewallet-cluster`.

2. **Create or Update Services**:

   #### User Service
   - If it exists, select `user-service` under the **Services** tab, click **Update**, and skip to the configuration. Otherwise, click **Create** under the **Services** tab.
   - **Launch type**: Fargate.
   - **Task definition**: Select `ewallet-user-service` (latest revision).
   - **Service name**: `user-service`.
   - **Number of tasks**: `1`.
   - **Networking**:
     - **VPC**: Select your VPC.
     - **Subnets**: Select your private subnets.
     - **Security group**: Select `ewallet-ecs-sg`.
     - **Public IP**: Disabled.
   - **Service Discovery**:
     - Check **Enable service discovery integration**.
     - **Namespace**: Select `ewallet.local`.
     - **Service discovery service**: Select `user-service`.
     - **DNS record type**: A.
     - **Routing policy**: Multivalue answer.
   - Click **Create** (or **Update service** if updating).

   #### Wallet Service
   - Repeat for `wallet-service`:
     - **Launch type**: Fargate.
     - **Task definition**: `ewallet-wallet-service` (latest revision).
     - **Service name**: `wallet-service`.
     - **Number of tasks**: `1`.
     - **Networking**:
       - **VPC**: Select your VPC.
       - **Subnets**: Select your private subnets.
       - **Security group**: `ewallet-ecs-sg`.
       - **Public IP**: Disabled.
     - **Service Discovery**:
       - **Namespace**: `ewallet.local`.
       - **Service discovery service**: `wallet-service`.
       - **DNS record type**: A.
       - **Routing policy**: Multivalue answer.
     - Click **Create**.

   #### Frontend Service
   - Repeat for `frontend-service`:
     - **Launch type**: Fargate.
     - **Task definition**: `ewallet-frontend-service` (latest revision).
     - **Service name**: `frontend-service`.
     - **Number of tasks**: `1`.
     - **Networking**:
       - **VPC**: Select your VPC.
       - **Subnets**: Select your private subnets.
       - **Security group**: `ewallet-ecs-sg`.
       - **Public IP**: Disabled.
     - **Load Balancing**:
       - Check **Enable load balancing**.
       - **Load balancer type**: Application Load Balancer.
       - **Load balancer**: Select `ewallet-alb`.
       - **Container to load balance**: `frontend-service:5002`.
       - **Target group**: Select `ewallet-frontend-tg`.
     - **Service Discovery**: Optional (not needed for Frontend Service).
     - Click **Create**.

---

### Step 9: Test the Deployed Application
1. **Verify the Services**:
   - In the `ewallet-cluster` dashboard, under the **Services** tab, ensure all services (`user-service`, `wallet-service`, `frontend-service`) have a status of “RUNNING” with 1 task each.
   - Under the **Tasks** tab, click on a task to view its details. Check the **Logs** tab to see the container logs if there are any issues.

2. **Check Cloud Map**:
   - Go to Cloud Map > `ewallet.local`.
   - Verify that `user-service` and `wallet-service` have registered instances with IP addresses.

3. **Access the Application**:
   - Open a browser and navigate to the ALB DNS name (e.g., `http://ewallet-alb-1234567890.ap-southeast-1.elb.amazonaws.com/`).
   - You should see the eWallet UI.

4. **Test the Application**:
   - Create a user (e.g., username: `dave`, email: `dave@example.com`).
   - Deposit funds (e.g., `500.00`) and withdraw funds (e.g., `200.00`).
   - Verify the balance updates to `300.00`.

5. **Verify in the Database**:
   - Connect to the RDS MySQL instance using a MySQL client (e.g., MySQL Workbench).
   - Run:
     ```sql
     SELECT * FROM users;
     SELECT * FROM wallets;
     SELECT * FROM transactions;
     ```
   - Confirm the user, wallet, and transactions are recorded correctly.

---

#########################################

# Migrate ECS to EKS

### Install kubectl

```sh
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Install eksctl

```sh
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin/
```

### Install aws-cli (if not already installed)

```sh
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```
### Navigate to EKS:

- In the AWS Management Console, search for “EKS” and click on Elastic Kubernetes Service.
- Create a New Cluster:
  - Click the orange Create cluster button.
  - Cluster name: Enter ewallet-eks-cluster.
Kubernetes version: Select the latest stable version (e.g., 1.30).
  - Cluster service role:
  - If you don’t have an EKS cluster role, create one:
      - Go to IAM > Roles > Create role.
      - Trusted entity type: AWS service.
      - Use case: EKS - Cluster.
      - Attach policies: AmazonEKSClusterPolicy and     AmazonEKSVPCResourceController.
      - Role name: eksClusterRole.
      - Click Create role.
      - Select eksClusterRole.
      - Networking:
      - VPC: Select your existing VPC (same as your ECS setup).
Subnets: Select your private subnets (e.g., subnet-12345678-private, subnet-87654321-private).
      - Security group: Use ewallet-ecs-sg (or create a new one with inbound rules for port 443 from your VPC CIDR).
      - Cluster endpoint access:
Select Public and private (allows access from within the VPC and externally via kubectl).
      - Logging: Enable control plane logging to CloudWatch (optional but recommended).
      - Click Next.
      - Configure Node Group:
      - Node group name: ewallet-node-group.
      - Node group role:
      - Create a new role in IAM:
      - Trusted entity type: AWS service.
      - Use case: EC2.
      - Attach policies: AmazonEKSWorkerNodePolicy, - AmazonEC2ContainerRegistryReadOnly, AmazonEKS_CNI_Policy.
      - Role name: eksNodeGroupRole.
      - Click Create role.
      - Select eksNodeGroupRole.
      - Instance type: t3.medium (or choose based on your workload).
      - Desired capacity: 2 nodes.
      - Subnets: Select your private subnets.
      - Click Next.
      - Review and Create:
      - Review the settings and click Create.
      - The cluster creation will take 10-15 minutes. Wait until the status changes to “Active”.
      - Configure kubectl to Access the Cluster:
After the cluster is created, update your kubeconfig to connect to the cluster:
      - ```sh
        aws eks update-kubeconfig --region ap-southeast-1 --name ewallet-eks-cluster
        ```
      - Verify connectivity:
      - ```sh
        kubectl get nodes
        ```
      - ```sh
        kubectl apply -f mainifest/.
        kubectl get ingress -n ewallet
        ```

- Look for the ADDRESS column (e.g., xxxx.ap-southeast-1.elb.amazonaws.com). This is the URL to access your application.
Test the Application:
Open a browser and navigate to the ALB DNS name (e.g., http://xxxx.ap-southeast-1.elb.amazonaws.com/).
Test creating a user, depositing, and withdrawing funds to ensure the application works as expected.


# Expose the Frontend Service with an ALB

- To make the Frontend Service accessible externally, we’ll use the AWS Load Balancer Controller to create an Application Load Balancer (ALB) for the Frontend Service.

- Install the AWS Load Balancer Controller:
Create an IAM policy for the controller:
Go to IAM > Policies > Create policy.
Select JSON and paste the policy from the AWS documentation (search for “AWS Load Balancer Controller IAM policy” to get the latest JSON).
Name: AWSLoadBalancerControllerIAMPolicy.
Click Create policy.

- Create an IAM role for the controller using eksctl:

```sh
eksctl create iamserviceaccount \
  --cluster=ewallet-eks-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::123456789012:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve \
  --region=ap-southeast-1
```

- Install the controller using Helm:

``` sh
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=ewallet-eks-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```
- Verify the controller is running:

```sh
kubectl get pods -n kube-system | grep aws-load-balancer-controller

kubectl get ingress -n ewallet
```

# Set Up AWS CodePipeline for CI/CD

## Create an IAM Role for CodePipeline and CodeBuild

### Create a CodePipeline Role:
- Go to IAM > Roles > Create role.
- Trusted entity type: AWS service.
- Use case: CodePipeline.
- Attach policies: AWSCodePipeline_FullAccess, AWSCodeCommitFullAccess, AmazonEC2ContainerRegistryFullAccess.
- Role name: CodePipelineRole.
- Click Create role.
### Create a CodeBuild Role:
- Go to IAM > Roles > Create role.
- Trusted entity type: AWS service.
- Use case: CodeBuild.
- Attach policies: AWSCodeBuildAdminAccess, AmazonEC2ContainerRegistryFullAccess, AmazonS3FullAccess, CloudWatchLogsFullAccess.
- Role name: CodeBuildRole.
- Click Create role.
- Create an EKS Deploy Role:
- Go to IAM > Roles > Create role.
- Trusted entity type: AWS service.
- Use case: CodePipeline (select it manually by choosing “Custom trust policy”).
- Custom trust policy:
  ```sh
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "codepipeline.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      },
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "codebuild.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
  ```
- Attach policies: AmazonEKSClusterPolicy, AmazonEKSWorkerNodePolicy.
- Role name: EKSDeployRole.
- Click Create role.

### Grant the EKS Deploy Role Access to the EKS Cluster:

Use eksctl to map the role to the EKS cluster:
```bash
eksctl create iamidentitymapping \
  --cluster ewallet-eks-cluster \
  --arn arn:aws:iam::123456789012:role/EKSDeployRole \
  --group system:masters \
  --username eks-deploy-role \
  --region ap-southeast-1
```
### Create the CodePipeline

- Navigate to CodePipeline:
- In the AWS Management Console, search for “CodePipeline” and click on AWS CodePipeline.
- Create a New Pipeline:
- Click Create pipeline.
- Pipeline name: ewallet-pipeline.
- Service role: Select CodePipelineRole.
- Click Next.

#### Add Source Stage:
- Source provider: AWS CodeCommit.
- Repository name: ewallet-repo.
- Branch name: main.
- Click Next.
- Add Build Stage:
- Build provider: AWS CodeBuild.
- Create a new build project:
- Project name: ewallet-build.
    - Environment:
    - Environment image: Managed image.
    - Operating system: Amazon Linux 2.
    - Runtime: Standard.
    - Image: aws/codebuild/amazonlinux2-x86_64-standard:5.0.
    - Service role: Select CodeBuildRole.
    - Buildspec: Use the buildspec file in the repository (e.g., user_service/buildspec.yml for the User Service).
- Click Continue to CodePipeline.
- Build projects: Add three build projects (one for each service):
    - ewallet-build-user (for User Service).
    - ewallet-build-wallet (for Wallet Service).
    - ewallet-build-frontend (for Frontend Service).
You’ll need to create each project separately in CodeBuild:

- Go to CodeBuild > Create build project.
- Repeat the above settings for each service, specifying the correct buildspec.yml path (e.g., user_service/buildspec.yml).
- In CodePipeline, add each build project as a parallel action in the Build stage.
- Add Deploy Stage:
- Deploy provider: AWS CodeBuild (we’ll use CodeBuild to apply Kubernetes manifests).
- Create a new build project:
- Project name: ewallet-deploy.
    - Environment:
    - Environment image: Managed image.
    - Operating system: Amazon Linux 2.
    - Runtime: Standard.
    - Image: aws/codebuild/amazonlinux2-x86_64-standard:5.0.
    - Service role: Select CodeBuildRole.
    - Buildspec: Choose a buildspec.yml for deployment in the root of the repository
- Review the pipeline settings and click Create pipeline.