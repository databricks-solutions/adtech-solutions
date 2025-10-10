import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import MessageStatus, GenieGetMessageQueryResultResponse, GenieMessage
from databricks.sdk.service.sql import StatementState
from prettytable import PrettyTable
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Workspace Client
workspace_client = None
DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')

# GENIE_SPACE_ID can be loaded here or passed to functions if more dynamic
# For now, the Streamlit app will fetch it and pass it.

if DATABRICKS_HOST and DATABRICKS_TOKEN:
    try:
        workspace_client = WorkspaceClient(
            host=DATABRICKS_HOST,
            token=DATABRICKS_TOKEN,
            auth_type='pat'  # Explicitly specify PAT authentication
        )
        # print("genie_logic.py: WorkspaceClient initialized successfully.") # Keep this for server logs if helpful
    except Exception as e:
        print(f"genie_logic.py: Error initializing WorkspaceClient: {e}")
        workspace_client = None
else:
    print("genie_logic.py: DATABRICKS_HOST and DATABRICKS_TOKEN must be set for genie_logic.")
    workspace_client = None

def get_workspace_client_status():
    """Returns a boolean indicating if the workspace client is initialized and the client itself or None."""
    if workspace_client:
        return True, workspace_client
    return False, None

def format_sdk_response_to_table_html(sdk_response: GenieGetMessageQueryResultResponse) -> str:
    """Format query results from a SUCCEEDED GenieGetMessageQueryResultResponse into an HTML table string"""
    
    if not hasattr(sdk_response, 'statement_response') or not sdk_response.statement_response:
        return "<p>No statement_response found in the SDK response.</p>"
        
    statement_resp = sdk_response.statement_response
    
    if not hasattr(statement_resp, 'result') or not statement_resp.result or \
       not hasattr(statement_resp.result, 'data_array'):
        if hasattr(statement_resp, 'manifest') and hasattr(statement_resp.manifest, 'total_row_count') and statement_resp.manifest.total_row_count == 0:
            return "<p>Query executed successfully and returned 0 rows.</p>"
        return "<p>No data_array found in statement_response.result, though query may have succeeded.</p>"

    data_array = statement_resp.result.data_array
    
    if not data_array:
        if hasattr(statement_resp, 'manifest') and hasattr(statement_resp.manifest, 'total_row_count') and statement_resp.manifest.total_row_count == 0:
            return "<p>Query returned 0 rows.</p>"
        return "<p>Result data_array is empty or None.</p>"

    table = PrettyTable()
    
    if hasattr(statement_resp, 'manifest') and \
       hasattr(statement_resp.manifest, 'schema') and \
       hasattr(statement_resp.manifest.schema, 'columns') and \
       statement_resp.manifest.schema.columns:
        table.field_names = [col.name for col in statement_resp.manifest.schema.columns if hasattr(col, 'name')]
    else:
        num_cols = len(data_array[0]) if data_array and data_array[0] else 0
        if num_cols > 0:
            table.field_names = [f"Column {i+1}" for i in range(num_cols)]
        else:
            return "<p>No column information and no data to infer columns, despite SUCCEEDED status.</p>"
            
    for row_list in data_array:
        table.add_row(row_list) 
    
    # Return HTML representation of the table
    # Ensure header=True (which is the default, so explicitly stating it or removing header=False is fine)
    return table.get_html_string() # Reverted: Removed header=False to show column names

def ask_genie_question(w_client, space_id_to_use, question_text):
    """
    Send a question to Genie and return the response content and any table.
    Returns a dictionary:
    {
        "text_response": str | None,
        "table_html": str | None,
        "error": str | None
    }
    """
    if not w_client:
        return {"text_response": None, "table_html": None, "error": "WorkspaceClient is not initialized."}

    try:
        print(f"[LOGIC_DEBUG] Calling start_conversation_and_wait for space: {space_id_to_use}")
        message = w_client.genie.start_conversation_and_wait(
            space_id=space_id_to_use,
            content=question_text,
        )
        print(f"[LOGIC_DEBUG] Message received. Status: {message.status}, Content: '{message.content}'")
        genie_text_response = message.content if hasattr(message, 'content') else "Genie did not provide a text response."

        if message.status != MessageStatus.COMPLETED:
            error_detail = f"Message processing did not complete successfully. Status: {message.status}"
            if hasattr(message, 'error') and message.error:
                error_detail += f" Error details: {message.error}"
            return {"text_response": genie_text_response, "table_html": None, "error": error_detail}

        if not message.attachments:
            print("[LOGIC_DEBUG] No attachments found in message.")
            return {"text_response": genie_text_response, "table_html": None, "error": None} # No attachments, just text
            
        print(f"[LOGIC_DEBUG] Raw message.attachments object: {message.attachments}")

        # For this version, we'll focus on the first query attachment if multiple exist.
        table_html_output = None
        error_from_attachment = None
        visualization_data = None
        text_from_attachments = []
        processed_query_description = None
        raw_table_data_for_charting = None

        print(f"[LOGIC_DEBUG] Attachments found ({len(message.attachments)}). Processing...")
        for i, attachment in enumerate(message.attachments):
            print(f"[LOGIC_DEBUG] Loop {i}: Processing attachment (raw): {attachment}")
            
            try:
                attachment_dict = vars(attachment) if hasattr(attachment, '__dict__') else {}
                print(f"[LOGIC_DEBUG] Loop {i}: Attachment fields: {attachment_dict}")
                if attachment.query:
                    print(f"[LOGIC_DEBUG] Loop {i}: Attachment query attribute: {vars(attachment.query) if hasattr(attachment.query, '__dict__') else attachment.query}")
                if attachment.text:
                     print(f"[LOGIC_DEBUG] Loop {i}: Attachment text attribute: {attachment.text}")
                if hasattr(attachment, 'visualization'):
                    print(f"[LOGIC_DEBUG] Loop {i}: Attachment has a 'visualization' attribute: {attachment.visualization}")
                    visualization_data = attachment.visualization
                if hasattr(attachment, 'chart'):
                    print(f"[LOGIC_DEBUG] Loop {i}: Attachment has a 'chart' attribute: {attachment.chart}")
                    visualization_data = attachment.chart
                if hasattr(attachment, 'data') and not attachment.query:
                    print(f"[LOGIC_DEBUG] Loop {i}: Attachment has a 'data' attribute: {attachment.data}")
                if hasattr(attachment, 'link'):
                     print(f"[LOGIC_DEBUG] Loop {i}: Attachment has a 'link' attribute: {attachment.link}")

            except Exception as e_log_detail:
                print(f"[LOGIC_DEBUG] Loop {i}: Error trying to log attachment details: {e_log_detail}")

            if attachment.query:
                #print(f"[LOGIC_DEBUG] Loop {i}: Attachment IS a query. Statement ID: {attachment.query.statement_id if attachment.query else 'N/A'}")
                # if not attachment.query.statement_id:
                #     error_from_attachment = (error_from_attachment or "") + \
                #         f"Query attachment (ID: {attachment.attachment_id}) has no statement_id. "
                #     continue # Move to next attachment or finish

                try:
                    print(f"[LOGIC_DEBUG] Loop {i}: Calling get_message_attachment_query_result for attachment_id: {attachment.attachment_id}")
                    result_response = w_client.genie.get_message_attachment_query_result(
                        space_id=space_id_to_use,
                        conversation_id=message.conversation_id,
                        message_id=message.id,
                        attachment_id=attachment.attachment_id
                    )
                    print(f"[LOGIC_DEBUG] Loop {i}: Raw result_response: {result_response}")
                    query_result_state_obj = None
                    raw_state_value = "NOT_FOUND_IN_RESPONSE"
                    if (hasattr(result_response, 'statement_response') and 
                        result_response.statement_response and 
                        hasattr(result_response.statement_response, 'status') and 
                        result_response.statement_response.status and 
                        hasattr(result_response.statement_response.status, 'state')):
                        query_result_state_obj = result_response.statement_response.status.state
                        raw_state_value = str(query_result_state_obj) # Get its string representation for logging
                    print(f"[LOGIC_DEBUG] Loop {i}: Extracted query_result_state_obj: {query_result_state_obj} (Raw string: '{raw_state_value}')")
                    print(f"[LOGIC_DEBUG] Loop {i}: Comparing with StatementState.SUCCEEDED: {StatementState.SUCCEEDED}")
                    
                    if query_result_state_obj == StatementState.SUCCEEDED:
                        print(f"[LOGIC_DEBUG] Loop {i}: Condition SUCCEEDED met for attachment {attachment.attachment_id}. Calling format_sdk_response_to_table_html.")
                        table_html_output = format_sdk_response_to_table_html(result_response)
                        
                        if (result_response.statement_response and 
                            hasattr(result_response.statement_response, 'manifest') and 
                            hasattr(result_response.statement_response.manifest, 'schema') and 
                            hasattr(result_response.statement_response.manifest.schema, 'columns') and 
                            result_response.statement_response.manifest.schema.columns and 
                            hasattr(result_response.statement_response, 'result') and 
                            hasattr(result_response.statement_response.result, 'data_array') and 
                            result_response.statement_response.result.data_array is not None):
                            
                            cols = [col.name for col in result_response.statement_response.manifest.schema.columns if hasattr(col, 'name')]
                            data = result_response.statement_response.result.data_array
                            
                            if cols and data: # Ensure we have both columns and some data rows
                                raw_table_data_for_charting = {"columns": cols, "data": data}
                                print(f"[LOGIC_DEBUG] Loop {i}: Extracted raw_table_data_for_charting: {len(cols)} columns, {len(data)} rows.")
                            else:
                                print(f"[LOGIC_DEBUG] Loop {i}: Could not extract raw_table_data for charting - missing cols or data rows.")
                        else:
                            print(f"[LOGIC_DEBUG] Loop {i}: Could not extract raw_table_data for charting - schema or data_array missing/incomplete.")

                        if attachment.query.description:
                            processed_query_description = attachment.query.description
                            print(f"[LOGIC_DEBUG] Loop {i}: Captured query description: {processed_query_description}")
                        print(f"[LOGIC_DEBUG] Loop {i}: format_sdk_response_to_table_html returned: {'HTML content' if table_html_output and '<table' in table_html_output else table_html_output}")
                        if table_html_output: 
                            print(f"[LOGIC_DEBUG] Loop {i}: Table HTML generated, breaking attachment loop.")
                            break
                    elif query_result_state_obj == StatementState.EXPIRED:
                        error_from_attachment = (error_from_attachment or "") + \
                            "Query results expired. "
                        # Potentially add logic here to try re-executing if that's a desired feature
                    else:
                        status_str = str(query_result_state_obj) if query_result_state_obj else "UNKNOWN_STATUS"
                        err_msg = f"Query result status: {status_str}. "
                        if hasattr(result_response, 'statement_response') and \
                           hasattr(result_response.statement_response, 'status') and \
                           hasattr(result_response.statement_response.status, 'error_message') and \
                           result_response.statement_response.status.error_message:
                             err_msg += f"Details: {result_response.statement_response.status.error_message}"
                        error_from_attachment = (error_from_attachment or "") + err_msg
                
                except Exception as e_fetch:
                    print(f"[LOGIC_ERROR] Loop {i}: Exception fetching query result: {str(e_fetch)}")
                    error_from_attachment = (error_from_attachment or "") + \
                        f"Error fetching query result for attachment {attachment.attachment_id}: {str(e_fetch)}. "
                
                if table_html_output: # if we got a table, stop processing attachments
                    break
            elif attachment.text and hasattr(attachment.text, 'content') and attachment.text.content:
                # This is a non-query attachment that has text content
                print(f"[LOGIC_DEBUG] Loop {i}: Attachment is NOT a query, but HAS text content: {attachment.text.content}")
                text_from_attachments.append(attachment.text.content)

        print(f"[LOGIC_DEBUG] Finished attachment loop. Final table_html_output is {'SET' if table_html_output else 'None'}. Error: {error_from_attachment}. Visualization data found: {'YES' if visualization_data else 'NO'}. Additional texts found: {len(text_from_attachments)}. Query description: {processed_query_description}. Raw table data extracted: {'YES' if raw_table_data_for_charting else 'NO'}")
        return {
            "text_response": genie_text_response, 
            "table_html": table_html_output, 
            "error": error_from_attachment,
            "visualization_info": visualization_data,
            "additional_texts": text_from_attachments,
            "query_description": processed_query_description,
            "raw_table_data": raw_table_data_for_charting
        }

    except Exception as e:
        print(f"[LOGIC_ERROR] Top-level exception in ask_genie_question: {str(e)}")
        return {"text_response": None, "table_html": None, "error": f"Outer error in ask_genie_question: {str(e)}"} 