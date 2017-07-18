# OpsBot - A Slack Chatbot built on Amazon Lex for AWS Guides

OpsBot enables a DevOps team to collaboratively assign and track tasks, share knowledge and collect resolution logs for issues faced during task execution. 
Runbooks are task templates that capture repetitive activities that the team performs, while Runlogs capture the task context including issues and resolution for reuse.
The bot uses runbooks and runlogs to ensure that team members have the resources they require to search for information regarding their tasks or designate 
tasks to others in their team. 
Users can search, filter runbooks and assign runbooks to others or pick them up for execution themselves. They can also check runbooks assigned to them and execute them. 
The execution phase creates runlogs which keeps getting updated at each step of the execution. Users can also raise issues they face during execution and look for 
resolutions available in the repository or on stackoverflow (via google custom search) or seek help from other team members by delegating the task, so the team member can
start from where the first user left off.

### Glossary
* A __runbook__ is a compilation of standard procedural operations or steps that dev execute sequentially for repetitive tasks. Though Runbooks are generally 
  a set of how-to instructions which contains the steps needed to get a job done. Runbooks can also be tutorials or guides 
  to walkthrough over relevant information and learn about standard dev tools, scripts, products or services. OpsBot currently stores runbooks in elasticsearch, 
  crawled from AWS tutorials, troubleshooting guides and how-to manuals.
* A __runlog__ is an instance of a task execution enabling tracking it to completion while capturing contextual details of user, environment, dependencies, issues 
  and corresponding resolutions. Runlogs are sharable within the team, enabling users to delegate sub-tasks to each other while maintaining the overall context.  



# Using OpsBot

Users can get started with OpsBot in the following ways:

* Searching for runbooks for particular AWS products.
* Execution and troubleshooting of runbooks.
* Resolution of issues in runlog.

The details of distinct features of OpsBot are:  

### Searching for runbooks
Users can give commands such as ```search``` or ``` find``` in slack to start searching for runbooks. The bot prompts the user to enter further details such 
as ```product name``` along with some optional parameters such as runbook type, nature of information required and tool type of AWS product so as to fetch only 
the most relevant runbooks. Some command examples include:
```
How can I manage my AWS products
I need help with some AWS ​products
find runbooks
```

### Assigning Runbooks
Users can assign a particular runbook after searching and selecting one. The bot prompts user to enter the team members's name whom to assign and the date
when to assign. Upon validation, the runbook gets assigned and a runlog is created with entries such as originator, recipient, user, logtime, runbook id, runlog 
id, runbook name, status.

### Execute Runbooks
Users can give commands such as ``` execute``` to execute a particular runbook assigned to them in the runlogs. At each step of the execution, user is prompted 
to mark a step as ```complete``` or ```raise an issue``` regarding the step by clicking on the options button and he gets directed to the selected intent. 
The corresponding runlog gets updated with fields such as issue and status.A command example to get this intent started is:
```
List all the tasks assigned to me
I want to complete my assignments
```

### Raise Issue
The execution process provides the user with the opportunity to raise errors or issues if need be at particular steps/tasks. The user is asked to provide a small 
description or summary of the issue whereby it gets logged into the runlog in a new field. Next, the user is shown resolutions for the issue which may be available
from some previously completed runlogs or from stackoverflow. The user is prompted to select a resolution and then shown the complete details present in it.
The user has an option to make it known whether the resolution was helpful. If yes, either the resolution count in runlog gets increased or the resolution gets 
updated in the runlog depending on whether the resolution came from the existing runlogs or from stackoverflow. Some command examples include:
```
troubleshoot error
I need Help
Help me with the error
Encountered an error. Need help
```

### Resolve Issue
Users can give commands such as ``` resolve``` to resolve an issue registered in a runlog with known runlog id. The user then provides a resolution to the issue 
listed in the runlog and the runlog gets updated with this information.A command example to get this intent started is:
```
List issues assigned to me
```

### Listing Runbooks
Users can give commands such ``` list runbooks``` to display all the runlogs which contain runbooks assigned to them with the latest status in the runlogs.
Users can select the ```execute``` option after selecting a particular runlog to start execution of the runbook step by step. The user will thus be directed to 
the ```execute``` intent.


# Installation Instructions

# GORDON

Gordon is a tool to create, wire and deploy AWS Lambdas using CloudFormation. Gordon has two aims:
* Easily deploy and manage lambdas.
* Easily connect those lambdas to other AWS services (kinesis, dynamo, s3, etc...)

Documentation: [Click here](https://gordon.readthedocs.io/en/latest/)

Lambdas are simple functions written in any of the supported AWS languages (python, javascript and java). Working with lambdas is quite easy to start with, but 
once you want to develop some complex integrations, it becomes a bit of a burden to deal with all the required steps to put some changes live. Gordon tries to 
make the entire process as smooth as possible.In gordon, Lambdas are resources that you’ll group and define within apps. The idea is to keep Lambdas with the 
same business domain close to each other in the same app.

### What gordon will do for you?

* Download any external requirements your lambdas might have.
* Create a zip file with your lambda, packages and libraries.
* Upload this file to S3.
* Create a lambda with your code and settings (memory, timeout...)
* Publish a new version of the lambda.
* Create an alias named current pointing to this new version.
* Create a new IAM Role for this lambda and attach it.
* As result, your lambda will be ready to run on AWS!

Gordon requires several python libraries, but all of them should get installed seamlessly using pip.
```$ pip install gordon```

### Creating a project

From the command line, cd into a directory where you’d like to store your code, then run the following command:
   ```$ gordon startproject demo```
This will create a demo directory in your current directory with the following structure:
```
demo
└── settings.yml
```

### Creating an application

Now that we have our project created, we need to create our first app. Run the following command from the command line:
```$ gordon startapp firstapp```
This will create a firstapp directory inside your project with the following structure:
```
firstapp/
├── helloworld
│   └── code.py
└── settings.yml
```
These files are:

* code.py : File where the source code of our first helloworld lambda will be. By default gordon creates a function called handler inside this file and registers 
  it as the main handler.
* settings.yml : Configuration related to this application. By default gordon registers a helloworld lambda function.
Now that we know what these files does, we need to install this firstapp. In order to do so, open your project settings.yml and add firstapp to the apps list:
```
project: demo
default-region: us-east-1
code-bucket: gordon-demo-5f1fb41f
apps:
  - gordon.contrib.lambdas
  - firstapp
 ```
 This will make Gordon take count of the resources registered within the firstapp application.

### Build your project
Now that your project is ready, you need to build it. You’ll need to repeat this step every time you make some local changes and want to deploy them to AWS.

From the command line, cd into the project root, then run the following command:
```$ gordon build```
This command will have an output similar to:
```
$ gordon build
Loading project resources
Loading installed applications
  contrib_lambdas:
    ✓ version
  firstapp:
    ✓ helloworld
Building project...
  ✓ 0001_p.json
    ✓ lambda:contrib_lambdas:version
    ✓ lambda:firstapp:helloworld
  ✓ 0002_pr_r.json
  ✓ 0003_r.json
  ```
  
You’ll now see a new _build directory in your project path. That directory contains everything gordon needs to put your lambdas live.

### Deploy your project
Deploying a project is a as easy as using the apply command:
```$ gordon apply```
This command will have an output similar to:
```
$ gordon apply
Applying project...
  0001_p.json (cloudformation)
    CREATE_COMPLETE waiting...
  0002_pr_r.json (custom)
    ✓ code/contrib_lambdas_version.zip (da0684c2)
    ✓ code/firstapp_helloworld.zip (45da7d76)
  0003_r.json (cloudformation)
    CREATE_COMPLETE waiting...
```
Your lambdas are ready to be used

# ElasticSearch

Setting up Elasticsearch Cloud Instance

### Creating cluster
	1.Log into the Elastic Cloud Console, if you aren’t logged in already.
	2.Select Clusters at the top and then click New Cluster.
	3.Set the cluster size. During the free trial period, you get access to provision one cluster with 1GB memory, and 24GB storage.
	4.Choose a region close to you.
	5.Configure the details relating ES version,shards,plugins
	6.Optional: Name your cluster.
	7.Click on the Create Cluster button.

After provisioning of new cluster is complete Overview page appears with details of URL endpoints.
Use the url endpoints to create index and insert data.
Enable kibana in configurations page.

### 1.Create the index for runbooks
Use cURL or postman client with mappings included in request body
```
curl -X PUT \
  <elasticsearch url> \
  -H 'authorization: Basic <authorization token>' \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/json' \
  -H 'postman-token: <postman token>' \
  --data-binary  @runbook_mappings.json
 ```

### 2.Create the index for runlogs
```
curl -X PUT \
  <elasticsearch url> \
  -H 'authorization: Basic <authorization token>' \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/json' \
  -H 'postman-token: <postman token>' \
  --data-binary  @runlog_mappings.json
```

### 3.Indexing the documents(runbooks)
```
curl -X PUT \
  <elasticsearch url> \
  -H 'authorization: Basic <authorization token>' \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/json' \
  -H 'postman-token: <postman token>' \
 --data-binary  @documents.json
 ```

# Feedback
We would love to hear as much feedback as possible! If you have any comment, please drop us an email to awsxbot@gmail.com


