# AI Prompt History & Development Disclosure

## 1. Project Overview

**Project Name:** Workforce Retention Intelligence System

**AI Tool Used:** ChatGPT (OpenAI)

I used ChatGPT as a development assistant while building this project. I worked on understanding the problem statement, planning the architecture, implementing the different modules, debugging issues, testing the application, and preparing the documentation.

I used AI assistance to improve my development workflow, understand unfamiliar concepts, and solve technical problems. I remained responsible for running the code, reviewing the results, and validating the application.

## 2. Development Process and Prompts

The following sections document the main prompts and activities from my development process.

### Phase 1: Understanding the Problem

My first step was to understand the YottaFlex challenge and identify what needed to be developed.

Prompts used:
- Explain the challenge problem statement in simple terms.
- Help me identify the main features and functionalities required.
- Suggest a suitable technology stack for this project.
- Help me plan the project architecture and folder structure.
- Explain the database entities and their relationships.

**My work:** I reviewed the requirements and organized the project into database, generator, analytics, validation, testing, and dashboard modules.

### Phase 2: Database Design and Data Generation

I worked on designing the database structure and generating synthetic employee data.

Prompts used:
- Help me create SQLAlchemy models for the required employee-related entities.
- Explain how to establish relationships between employees, roles, teams, surveys, workload, compensation, and attrition outcomes.
- Help me generate 10,000 synthetic employee records covering 24 months.
- Implement a fixed random seed for reproducibility.
- Explain how to generate voluntary attrition outcomes without using future information.

**My work:** I configured the SQLite database, executed the data generation process, and checked the generated records.

### Phase 3: Feature Engineering and Machine Learning

I worked on preparing employee data for analysis and developing the retention prediction model.

Prompts used:
- Help me perform feature engineering using historical employee information.
- Explain how to prevent future data leakage.
- Help me build a Random Forest classification model.
- Explain train-test splitting and class imbalance.
- Explain accuracy, precision, recall, F1-score, ROC-AUC, and PR-AUC.
- Help me generate employee retention risk scores.
- Explain how to provide understandable reasons behind employee risk scores.

**My work:** I executed feature engineering and model training, reviewed the evaluation metrics, and examined the generated risk scores and feature importance.

### Phase 4: Dashboard Development

I developed an interactive dashboard using Streamlit to present the workforce analytics.

Prompts used:
- Help me build an interactive Streamlit dashboard.
- Add workforce overview and retention distribution.
- Include department-wise and role-wise analysis.
- Display engagement and workload analysis.
- Add employee retention risk scores with explanations.
- Include intervention tracking and downloadable reports.
- Help me troubleshoot dashboard and database integration issues.

**My work:** I ran the dashboard locally, checked the different sections, and verified that the data and visualizations were displayed.

### Phase 5: Validation and Testing

I focused on checking data quality, reproducibility, and the negative scenarios specified in the challenge.

Prompts used:
- Help me validate employee data and database relationships.
- Test future data leakage.
- Test missing survey handling.
- Test attrition outcome date consistency.
- Test whether interventions require human review.
- Help me implement a reproducibility check using checksums.
- Help me export database records into CSV, JSON, and SQL formats.

**My work:** I executed the validation scripts and automated tests and reviewed their outputs.

Validation results:
- 4 out of 4 negative-scenario tests passed.
- Data validation errors: 0.
- Data validation warnings: 0.
- Reproducibility check: Passed.
- Database records: 899,553.

### Phase 6: Documentation and GitHub

I prepared the project documentation and uploaded the project to a dedicated public GitHub repository.

Prompts used:
- Help me write the project README.
- Prepare requirements.txt.
- Help me configure .gitignore.
- Explain how to initialize Git and create commits.
- Help me upload the project to GitHub.
- Help me resolve GitHub file-size restrictions.

**My work:** I created the GitHub repository, initialized Git, committed the project, resolved the oversized SQL file issue, and successfully pushed the project to GitHub.

Repository:
https://github.com/Akshatabagewadi/workforce-retention-intelligence-system

## 3. How AI Helped Me

I used ChatGPT mainly for:
- Understanding the problem statement and planning the architecture.
- Getting implementation guidance for Python, SQLAlchemy, and machine learning.
- Understanding feature engineering and model evaluation.
- Developing and improving the Streamlit dashboard.
- Debugging errors during development.
- Preparing validation scripts and documentation.
- Understanding Git and GitHub commands.

## 4. What I Personally Worked On and Verified

Throughout the development process, I:
- Set up the Python virtual environment.
- Installed and configured the project dependencies.
- Ran the database and data generation scripts.
- Generated and exported the synthetic employee dataset.
- Executed the feature engineering and model evaluation scripts.
- Ran the Streamlit dashboard locally.
- Reviewed the dashboard outputs and model metrics.
- Executed the data validation script.
- Ran the four negative-scenario tests.
- Checked reproducibility using checksum comparison.
- Created and uploaded the public GitHub repository.

## 5. Technical Decisions and Limitations

I selected Python, SQLite, SQLAlchemy, Pandas, Scikit-learn, and Streamlit because they allowed me to build and run the project locally using a simple technology stack.

Some important limitations of the current implementation are:
- The employee dataset is synthetic and does not represent real employees.
- Attrition outcomes are generated using predefined rules.
- Model scores should not be interpreted as calibrated real-world probabilities.
- Feature importance and rule-based explanations do not establish causation.
- Retention predictions should support human review, not automated employment decisions.

## 6. My Understanding and Responsibility

AI assistance helped me accelerate development, but I understand that using AI does not replace understanding the implementation.

I am responsible for explaining the project architecture, database design, feature engineering, machine learning workflow, dashboard functionality, testing approach, and limitations.

I have executed the project locally and reviewed the validation and testing results. I am prepared to explain the technical decisions and demonstrate the working application during the project walkthrough.

---

**Project:** Workforce Retention Intelligence System  
**Repository:** https://github.com/Akshatabagewadi/workforce-retention-intelligence-system  
**Documentation:** AI Prompt History & Development Disclosure