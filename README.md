<p align="center">
  <img src="https://github.com/AbhigyanSr/EchoMail/blob/d18a17a2da65190f612e363ac3ca747e3db88884/assets/banner.png" alt="EchoMail Banner"/>
</p>

<h1 align="center">EchoMail: Bulk Email Sender</h1>

<p align="center">
  A cloud-native bulk email service built on AWS.
  <br />
  This project uses an event-driven architecture to send mass emails from a CSV file.
</p>

<p align="center">
  <a href="#features"><strong>Features</strong></a> ·
  <a href="#architecture-overview"><strong>Architecture</strong></a> ·
  <a href="#deployment-guide"><strong>Deployment</strong></a>
</p>

---

<h3 align="center">Tech Stack</h3>
<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python"/>
  <img src="https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="AWS"/>
  <img src="https://img.shields.io/badge/S3-569A31?style=for-the-badge&logo=amazon-s3&logoColor=white" alt="S3"/>
  <img src="https://img.shields.io/badge/Lambda-FF9900?style=for-the-badge&logo=aws-lambda&logoColor=white" alt="Lambda"/>
  <img src="https://img.shields.io/badge/EC2-FF9900?style=for-the-badge&logo=amazon-ec2&logoColor=white" alt="EC2"/>
</p>

---

<h2><b>✨ Features</b></h2>

- **Bulk Emailing:** Send thousands of emails by uploading a single CSV file.  
- **Event-Driven:** Automatically triggered on file upload, requiring no manual intervention.  
- **Decoupled Architecture:** Lambda orchestrates the workflow, delegating email delivery to an EC2 worker.  
- **Flexible SMTP Support:** Easily configurable for Gmail, Outlook, and other providers.  
- **Error Reporting:** Provides a success/failure summary after execution.  

---

<h2><b>🗂 Architecture Overview</b></h2>
<p align="center">
  <img alt="EchoMail AWS Architecture" src="https://github.com/AbhigyanSr/EchoMail/blob/bee7257bb2e46d5a2070a82b197d6a7082780d0b/assets/architecture.png">
</p>

**Workflow:**
1. A CSV file with recipient details is uploaded to an **S3 bucket**.  
2. The S3 event triggers the **EchoMail Lambda function**.  
3. Lambda constructs a POST request with file metadata & credentials.  
4. The request is sent to a **Flask microservice** on an EC2 instance.  
5. Flask downloads the CSV, parses it, and sends emails via **SMTP**.  

---

<h2><b>🚀 Deployment Guide</b></h2>
This project supports two deployment methods: automated with Terraform (recommended) or manual via the AWS Console.

<h3>Option A: Automated Deployment with Terraform (Recommended)</h3>
Terraform automates the creation of all necessary AWS resources (S3 Bucket, EC2 Instance, IAM Roles, Security Groups).<br>

<b>Prerequisites:</b>
Terraform installed on your local machine.<br>
AWS CLI installed and configured with your credentials.<br>

<h3>Steps:</h3>
<b>Clone the repository:</b><br>

```bash
git clone https://github.com/AbhigyanSr/EchoMail.git
cd EchoMail
```
<b>Initialize Terraform:</b><br>
Navigate to the terraform/ directory and run:<br>

```bash
terraform init
```
<b>Deploy the Infrastructure:</b><br>
Apply the configuration. You will be prompted to confirm the resources that will be created.<br>

```bash
terraform apply
```

Terraform will output the public IP of the EC2 instance upon completion.<br>
<b>Configure Lambda:</b><br>
After deployment, manually configure the Lambda function's environment variables in the AWS Console as described in the manual setup guide below. This is to avoid committing sensitive credentials to your repository.
Upload the Lambda.py code to your newly created Lambda function.<br>

<b>Deploy Flask App:</b><br>
SSH into the EC2 instance using the IP from the Terraform output.
Follow the steps in the "EC2 Flask Microservice" section below to install dependencies and run the application.<br>
<h3>Option B: Manual Deployment</h3>

### 1. S3 Bucket
- Create a unique bucket (e.g., `echomail-csv`).  
- IAM policies will handle access permissions.  

### 2. EC2 Flask Microservice
- Launch a **t2.micro Ubuntu EC2 instance**.  
- Attach an **IAM role** with `s3:GetObject` permission for your bucket.  
- Update **Security Group**: allow inbound traffic on `5000` (Flask) and `22` (SSH).  

SSH into the instance and install dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install flask boto3
```
Copy the EC2 code and run it using 
```bash
python3 EC2.py
```
### 3. Lambda Function
-Create a Lambda function (e.g., EchoMail-Trigger) with Python runtime.
-Set Trigger: S3 → ObjectCreated:Put.
-Configure Environment Variables:
| Variable   | Description                                        |
| ---------- | -------------------------------------------------- |
| `EC2_IP`   | `http://<EC2_PUBLIC_IP>:5000/send-emails`          |
| `Email_id` | Sender email address                               |
| `Password` | Email password / app password (for Gmail with 2FA) |
| `subject`  | Email subject line                                 |
| `body`     | Email body content                                 |

-Increase Timeout to at least 30 seconds.<br>
-Upload the Lambda.py code and configure the testevent.json file.

<h2><b>Future Improvements</b></h2>

Key enhancements to evolve the project into a production-grade service:

<ul>
  <li><b>Web Frontend:</b> Create a user-friendly webpage for CSV uploads using S3 pre-signed URLs, removing the need for direct S3 console access.</li>
  <li><b>Use Amazon SES:</b> Replace the personal SMTP logic with Amazon's Simple Email Service (SES) for superior email deliverability, scalability, and tracking.</li>
  <li><b>Implement a Job Queue (SQS):</b> For very large email lists, use an SQS queue to process jobs asynchronously, preventing timeouts and increasing reliability.</li>
  <li><b>Add a Database (DynamoDB):</b> Log the status of each email campaign to a DynamoDB table to track history and success rates.</li>
  <li><b>Containerize with Docker:</b> Package the Flask application in a Docker container for consistent, portable, and simplified deployments.</li>
</ul>

<h2><b>Authors</b></h2> <p> Built by <a href="https://github.com/AbhigyanSr">Abhigyan Srivastava</a> </p> 
