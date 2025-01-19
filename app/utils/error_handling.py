import ast

def handle_bad_request_error(bre):
    try:
        # Attempt to parse the error response into a dictionary
        error_details = ast.literal_eval(bre.args[0].split(" - ", 1)[1])
        print("Error Details:", error_details)
        
        # Extract error information
        error = error_details.get('error', {})
        inner_error = error.get('inner_error', {})
        message = error.get('message', "No message provided")
        content_filter_results = inner_error.get('content_filter_results', {})
        revised_prompt = inner_error.get('revised_prompt', None)

        # Log content policy violation specifics
        if error.get('code') == 'content_policy_violation':
            print(f"Content Policy Violation: {message}")
            print("Content Filter Results:", content_filter_results)
        
        # Handle the presence of revised_prompt
        if revised_prompt:
            print("Using revised prompt for retry:", revised_prompt)
            return self.text_to_image(revised_prompt)
        else:
            print("Revised prompt is not available.")
            # Handle cases where no revised prompt is provided
            raise ValueError("Revised prompt not available in the error details.")
    
    except (ValueError, KeyError, SyntaxError) as e:
        # Handle parsing or missing key errors gracefully
        print(f"Error while processing the bad request error: {e}")
        raise e

    except Exception as e:
        # Catch any other unexpected exceptions
        print(f"Unexpected error: {e}")
        raise e
