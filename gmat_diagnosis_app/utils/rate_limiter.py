import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
# from streamlit.web.server.server import Server # Potential alternative if get_script_run_ctx is too fragile or removed
import datetime

# This dictionary will store IP addresses and their request counts and last reset date.
# In a production environment with multiple workers/instances, a more robust shared store
# like Redis or a database would be necessary. For a single-instance Streamlit app,
# a global dictionary can work for simplicity, but be aware of potential concurrency issues
# if Streamlit's threading model becomes complex.
RATE_LIMIT_DATA = {}
DAILY_LIMIT = 20 # Daily limit per IP

def get_client_ip():
    """
    Tries to get the client's IP address.
    This can be unreliable in Streamlit as it depends on internal APIs or specific deployment setups (e.g., behind a reverse proxy).
    Adjust this function based on your deployment environment for more reliability.
    """
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            # This case might happen if the function is called outside a Streamlit script run.
            # st.warning("無法獲取 Script Run Context，IP 位址未知。") # Avoid st calls if ctx is None
            print("Warning: get_script_run_ctx returned None. IP address unknown.")
            return None
        
        session_id = ctx.session_id
        
        from streamlit.runtime import get_instance
        # from streamlit.runtime.Runtime import Runtime # Not strictly needed for type hinting here
        
        runtime = get_instance() # Type: Runtime
        session_client = runtime.get_client(session_id)

        if session_client is None:
            st.warning("無法獲取客戶端連線資訊，IP 位址未知。")
            return None
            
        # Try common attribute names for IP. This part is fragile.
        if hasattr(session_client, 'ip'):
            return session_client.ip
        elif hasattr(session_client, 'client_ip'): 
             return session_client.client_ip
        # Add more checks if other attributes are known, e.g. for specific server setups
        # elif hasattr(session_client, '_forwarded_for_ip'): # example
        #     return session_client._forwarded_for_ip
        else:
            # Removed warning message about not being able to read IP directly
            # Fallback for local development (use with caution, only for trusted local env)
            return "local_development_ip"

    except ImportError:
        st.error("導入 Streamlit 內部模組時發生錯誤。IP 獲取功能可能不相容目前版本。")
        return None
    except Exception as e:
        st.error(f"獲取 IP 位址時發生未預期錯誤: {e}。速率限制可能無法正常運作。")
        return None

def check_rate_limit(ip_address: str) -> bool:
    """
    Checks if the given IP address has exceeded the daily API call limit.
    Resets the count daily.

    Args:
        ip_address: The IP address to check.

    Returns:
        True if the request is allowed, False if the limit is exceeded.
    """
    if not ip_address: 
        st.warning("IP 位址未知，無法執行速率限制。為安全起見，此次請求將被拒絕。")
        return False # Changed to False for safety if IP is unknown

    today = datetime.date.today()
    
    if ip_address not in RATE_LIMIT_DATA:
        RATE_LIMIT_DATA[ip_address] = {"count": 1, "last_reset_date": today}
        return True
    
    ip_data = RATE_LIMIT_DATA[ip_address]
    
    if ip_data["last_reset_date"] != today:
        # Reset for the new day
        ip_data["count"] = 1
        ip_data["last_reset_date"] = today
        return True
    
    if ip_data["count"] >= DAILY_LIMIT:
        # st.error(f"IP: {ip_address} 已達到每日 {DAILY_LIMIT} 次的 API 呼叫上限。") # Message displayed by calling function
        return False # Limit exceeded
    
    ip_data["count"] += 1
    return True

# Example usage (for testing this file directly):
# if __name__ == "__main__":
#     # To test this, you'd typically run it as part of a Streamlit app.
#     # The get_client_ip function relies on Streamlit's runtime context.
#     # For simple standalone test:
#     print(f"RATE_LIMIT_DATA before: {RATE_LIMIT_DATA}")
    
#     # Test with a known IP
#     test_ip_known = "192.168.1.1"
#     print(f"Simulating requests for known IP: {test_ip_known}")
#     for i in range(DAILY_LIMIT + 2):
#         allowed = check_rate_limit(test_ip_known)
#         current_count = RATE_LIMIT_DATA.get(test_ip_known, {}).get('count', 0)
#         print(f"Request {i+1}: Allowed = {allowed}, Count = {current_count}")
#         if not allowed and i < DAILY_LIMIT: # Should not happen before limit
#             print(f"Error: Request {i+1} for {test_ip_known} denied prematurely!")
#         elif allowed and i >= DAILY_LIMIT: # Should not happen after limit
#             print(f"Error: Request {i+1} for {test_ip_known} allowed after limit!")
#     print(f"RATE_LIMIT_DATA after for {test_ip_known}: {RATE_LIMIT_DATA.get(test_ip_known)}")

#     # Simulate next day for test_ip_known
#     print("\\nSimulating next day for {test_ip_known}...")
#     if test_ip_known in RATE_LIMIT_DATA:
#         # Manually "age" the entry to simulate a new day
#         RATE_LIMIT_DATA[test_ip_known]["last_reset_date"] = datetime.date.today() - datetime.timedelta(days=1)
#         print(f"Manually set last_reset_date for {test_ip_known} to yesterday.")
#         allowed = check_rate_limit(test_ip_known)
#         current_count = RATE_LIMIT_DATA.get(test_ip_known, {}).get('count', 0)
#         print(f"Request 1 (next day): Allowed = {allowed}, Count = {current_count}")
#         if not allowed or current_count != 1:
#             print(f"Error: Next day reset failed for {test_ip_known}!")

#     # Test with an unknown IP (simulated by passing None)
#     print("\\nSimulating request with unknown IP (None)...")
#     allowed_unknown = check_rate_limit(None)
#     print(f"Request with None IP: Allowed = {allowed_unknown}")
#     if allowed_unknown: # Based on current logic, this should be False
#         print("Error: Request with unknown IP was allowed, but should be denied for safety.")
        
#     # Test with another IP
#     test_ip_other = "203.0.113.45"
#     print(f"\\nSimulating requests for another IP: {test_ip_other}")
#     for i in range(3):
#         allowed = check_rate_limit(test_ip_other)
#         current_count = RATE_LIMIT_DATA.get(test_ip_other, {}).get('count', 0)
#         print(f"Request {i+1} for {test_ip_other}: Allowed = {allowed}, Count = {current_count}")
#         if not allowed or current_count != i + 1:
#             print(f"Error: Request {i+1} for {test_ip_other} failed or count incorrect!")
#     print(f"RATE_LIMIT_DATA at end: {RATE_LIMIT_DATA}") 