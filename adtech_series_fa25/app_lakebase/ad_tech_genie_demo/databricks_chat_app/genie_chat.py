from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import MessageStatus
from prettytable import PrettyTable
import os
import time

# Initialize the Workspace Client
workspace_client = WorkspaceClient(
    host=os.getenv('DATABRICKS_HOST'),
    token=os.getenv('DATABRICKS_TOKEN')
)

print(workspace_client)

def display_results(result):
    """Display query results in a formatted table"""
    if not result.result.rows:
        print("No results found")
        return

    # Create table with column headers
    table = PrettyTable()
    table.field_names = [col.name for col in result.result.metadata.column_info]
    
    # Add rows to the table
    for row in result.result.rows:
        table.add_row(row)
    
    print(table)

def ask_genie_question(space_id, question):
    """Send a question to Genie and display results"""
    try:
        # Start a new conversation
        message = workspace_client.genie.start_conversation_and_wait(
            space_id=space_id,
            content=question
        )

        # Check message status
        if message.status != MessageStatus.COMPLETED:
            print(f"Message processing failed. Status: {message.status}")
            if message.error:
                print(f"Error details: {message.error}")
            return

        print(f"\nGenie Response: {message.content}\n")

        # Process attachments
        for attachment in message.attachments:
            if attachment.query:  # If this is a query attachment
                print(f"Processing query results...")
                
                # Get query results
                result = workspace_client.genie.get_message_attachment_query_result(
                    space_id=space_id,
                    conversation_id=message.conversation_id,
                    message_id=message.id,
                    attachment_id=attachment.attachment_id
                )
                
                display_results(result)

    except Exception as e:
        print(f"Error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    SPACE_ID = os.getenv("GENIE_SPACE_ID")  # Replace with your Genie space ID
    
    while True:
        question = input("\nAsk Genie a question (type 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        
        ask_genie_question(SPACE_ID, question)
        print("\n" + "="*50 + "\n")
