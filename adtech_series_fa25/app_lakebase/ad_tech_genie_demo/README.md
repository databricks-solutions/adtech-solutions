# Agent Chat Application

This Streamlit application provides a chat interface to interact with a Databricks Genie space and displays a campaign reporting dashboard.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd demo
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the `demo` project root directory with the following content:

    ```
    DATABRICKS_HOST="your_databricks_host_url" # e.g., https://e2-demo-field-eng.cloud.databricks.com/
    DATABRICKS_TOKEN="your_databricks_api_token" # e.g., dapixxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    GENIE_SPACE_ID="your_genie_space_id" # e.g., 01f031d377521b3e9ccf2572fa3e417e
    ```
    Replace the placeholder values with your actual Databricks host, API token, and Genie Space ID.

## Running the Application

1.  Ensure your virtual environment is activated and you are in the `demo` directory.
2.  Run the Streamlit application:
    ```bash
    streamlit run databricks_chat_app/app.py
    ```

    The application should open in your web browser.

## Deployment to Databricks

To deploy this application as a Databricks App:

1.  **Package the Application:**
    Ensure all necessary files, including `databricks_chat_app/app.py`, `requirements.txt`, and the `.env` file (or ensure environment variables are set in the Databricks App configuration) are available.

2.  **Create a New Databricks App:**
    *   Navigate to your Databricks workspace.
    *   Go to "Compute" -> "Apps".
    *   Click "Create App".
    *   Give your app a name.
    *   **Source Code:** Choose the method to provide your code (e.g., upload a zip file of your `demo` directory, connect to a Git repository).
    *   **Entrypoint:** Specify `databricks_chat_app/app.py` as the entrypoint or main file to run.
    *   **Python Version:** Select a Python version compatible with your dependencies (e.g., Python 3.9 or 3.10).
    *   **Dependencies:** Databricks will typically try to install dependencies from `requirements.txt` if it's included in your source code. You might also have an option to specify a path to this file or manually list packages.
    *   **Environment Variables:** Configure the `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, and `GENIE_SPACE_ID` environment variables directly within the Databricks App settings. This is generally more secure than packaging the `.env` file.

3.  **Deploy and Run:**
    *   Configure any other settings as needed (e.g., instance size).
    *   Click "Create" or "Deploy".
    *   Once the app is deployed, you can run it and access it via the provided URL.

## Deploying to Databricks Apps using Databricks CLI

For a more streamlined deployment process, you can use the Databricks CLI:

### Prerequisites
- Install the Databricks CLI: `pip install databricks-cli`
- Configure authentication with your Databricks workspace

### Step-by-Step Deployment

1.  **Create the Databricks App**
    In your Databricks workspace:
    *   Go to "Compute" -> "Apps"
    *   Click "Create App"
    *   Give your app a name (e.g., `agent-chat`)
    *   Note the app name for the CLI commands

2.  **Prepare the app.yaml file**
    Create an `app.yaml` file inside the `databricks_chat_app` directory:
    ```yaml
    entrypoint: streamlit run app.py --server.port $PORT --server.headless true
    ```

3.  **Sync your files to Databricks Workspace**
    From your project root directory (`demo`):
    ```bash
    databricks sync . /Workspace/Users/YOUR_EMAIL@databricks.com/YOUR_APP_NAME --profile YOUR_PROFILE
    ```
    
    Or with watch mode for automatic syncing:
    ```bash
    databricks sync --watch . /Workspace/Users/YOUR_EMAIL@databricks.com/YOUR_APP_NAME --profile YOUR_PROFILE
    ```

    **Example commands:**
    ```bash
    # Sync with watch mode (recommended for development)
    databricks sync --watch . /Workspace/Users/charlie.hohenstein@databricks.com/agent-chat --profile DEFAULT
    
    # One-time sync
    databricks sync . /Workspace/Users/charlie.hohenstein@databricks.com/agent-chat --profile DEFAULT
    ```

4.  **Deploy the app**
    ```bash
    databricks apps deploy YOUR_APP_NAME --source-code-path /Workspace/Users/YOUR_EMAIL@databricks.com/YOUR_APP_NAME/databricks_chat_app --profile YOUR_PROFILE
    ```

    **Example command:**
    ```bash
    databricks apps deploy agent-chat --source-code-path /Workspace/Users/charlie.hohenstein@databricks.com/agent-chat/databricks_chat_app --profile DEFAULT
    ```

### Important Notes for Databricks App Deployment

1.  **Import Paths:** When deploying, the app runs from within the `databricks_chat_app` directory. The import in `app.py` should be:
    ```python
    from genie_logic import ask_genie_question, get_workspace_client_status
    ```
    (Not `from databricks_chat_app.genie_logic import ...`)

2.  **Hardcoded Credentials:** If you prefer to hardcode credentials in the source code rather than using environment variables, update the values in both `app.py` and `genie_logic.py`:
    
    In `app.py`:
    ```python
    DATABRICKS_HOST = "your_databricks_host_url"
    DATABRICKS_TOKEN = "your_databricks_api_token"
    GENIE_SPACE_ID = "your_genie_space_id"
    ```
    
    In `genie_logic.py`:
    ```python
    workspace_client = WorkspaceClient(
        host="your_databricks_host_url",
        token="your_databricks_api_token",
        auth_type='pat'
    )
    ```

3.  **Authentication Issues:** If you encounter "more than one authorization method configured" errors, ensure:
    *   The `auth_type='pat'` parameter is set in the `WorkspaceClient` initialization
    *   Remove conflicting environment variables from `app.yaml` if using hardcoded credentials

4.  **File Structure:** Your deployment syncs the entire project directory. The structure will be:
    ```
    /Workspace/Users/YOUR_EMAIL@databricks.com/YOUR_APP_NAME/
    ├── databricks_chat_app/
    │   ├── app.yaml
    │   ├── requirements.txt
    │   ├── app.py
    │   └── genie_logic.py
    ├── README.md
    └── requirements.txt (project root)
    ```
    
    The `--source-code-path` points to the `databricks_chat_app` subdirectory within this synced structure.

### Troubleshooting Common Issues

- **"ModuleNotFoundError: No module named 'databricks_chat_app'"**: Update the import in `app.py` to use relative imports
- **"App exited unexpectedly"**: Check the application logs in the Databricks UI for detailed error messages
- **Authentication errors**: Verify your token is valid and has the necessary permissions for the Genie Space

## Project Structure

```
demo/
├── .env                   # Environment variables (DO NOT COMMIT if sensitive)
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── databricks_chat_app/
    ├── __init__.py        # Makes it a Python package
    ├── app.py             # Main Streamlit application logic
    └── genie_logic.py     # Logic for interacting with Databricks Genie
```
