import requests
import urllib3
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

class IBKRWebAPIService:
    def __init__(self, base_url="https://trade.jtcml.com/v1/api"):
        self.base_url = base_url
        self.session = requests.Session()
        # verify=True as we are now using the public Certbot certificate
        self.session.verify = True 
        self.session.headers.update({
            "User-Agent": "Console",
            "Content-Type": "application/json"
        })

    def set_cookies(self, cookies: dict):
        """
        Iteration 51: Updated to handle potential 'secure' flag issues in local dev.
        """
        self.session.cookies.clear()
        for name, value in cookies.items():
            self.session.cookies.set(name, value)
        logger.info(f"IBKR: Session cookies synchronized ({len(cookies)} cookies).")

    def get_accounts(self):
        """
        Fetches the list of accessible account IDs.
        """
        try:
            resp = self.session.get(f"{self.base_url}/iserver/accounts", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "accounts" in data:
                    return data["accounts"] # List of account strings
                if isinstance(data, list):
                    # Some versions return just a list of strings or dicts
                    return [d.get("id") if isinstance(d, dict) else d for d in data]
        except Exception as e:
            logger.error(f"IBKR Account Fetch Error: {e}")
        return []

    def check_auth(self):
        try:
            # Iteration 65: Aggressive linkage trigger
            # The Client Portal API REQUIRES /iserver/accounts to move from 'logged in' to 'brokerage session active'
            self.session.get(f"{self.base_url}/iserver/accounts", timeout=5)
            
            # Use /iserver/auth/status to verify
            resp = self.session.get(f"{self.base_url}/iserver/auth/status", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                is_auth = data.get("authenticated", False)
                
                # If authenticated but not connected to brokerage, try one more accounts call
                if is_auth and not data.get("connected", False):
                    self.session.get(f"{self.base_url}/iserver/accounts")
                
                if is_auth:
                    self.session.post(f"{self.base_url}/tickle", timeout=1)
                return is_auth
        except Exception as e:
            logger.error(f"IBKR Auth Check Error: {e}")
        return False

    def resolve_conid(self, ticker: str, sec_type="STK"):
        """
        Resolves a symbol to an IBKR Contract ID (conid).
        Supports STK and CASH (FX).
        """
        try:
            # Simple heuristic: if ticker has '.', '=', or '/', likely FX (e.g. EUR.USD, EUR=X)
            # Or if sec_type is explicitly passed as CASH
            is_fx = sec_type == "CASH" or any(c in ticker for c in ['.', '=', '/'])
            
            search_term = ticker.replace('=X', '').replace('/', '').replace('.', '')
            if is_fx and len(search_term) == 6:
                # Format for search: "EUR" usually returns "EUR.USD"
                # But safer to search the base currency
                search_term = search_term[:3]
            
            # Explicit search for name=false to search by symbol
            resp = self.session.get(f"{self.base_url}/iserver/secdef/search?symbol={search_term}&name=false&secType={sec_type}")
            if resp.ok:
                results = resp.json()
                
                # Filter for exact match and secType
                for res in results:
                    # Check secType match if available in response (some endpoints don't return it clearly in search)
                    # But usually 'description' or 'name' helps.
                    # IBKR search is messy.
                    
                    # If we want FX, look for secType 'CASH' or 'FUT' (but we want CASH)
                    if is_fx:
                        # For CASH, the search for "EUR" returns symbol="EUR", description="IDEALPRO"
                        # It doesn't explicitly say "EUR.USD" in the search result top level.
                        # However, conid 12087792 is the base EUR contract.
                        # IBKR uses the same conid for the currency itself often?
                        # Actually, for CASH execution, we often need the pair conid.
                        # Let's search for "EUR.USD" explicitly first.
                        
                        # If we searched for "EUR" and got "EUR", and our ticker starts with "EUR", it's a candidate.
                        if res.get('symbol') == search_term.upper() and 'CASH' in [s['secType'] for s in res.get('sections', [])]:
                            return res.get('conid')

                    # If STK, standard check
                    elif res.get('symbol') == ticker.upper():
                        return res.get('conid')
                        
                if results: return results[0].get('conid')
        except Exception as e:
            logger.error(f"Conid Resolution Failed for {ticker}: {e}")
        return None

    def execute_order(self, account_id, ticker, action, quantity, order_type="MARKET"):
        """
        Iteration 52: Robust order execution with conid resolution and confirmation handling.
        """
        try:
            # Determine sec_type
            is_fx = any(c in ticker for c in ['.', '=', '/'])
            sec_type = "CASH" if is_fx else "STK"
            
            # Normalize ticker for FX (EUR.USD)
            if is_fx:
                ticker = ticker.replace('=X', '').replace('/', '.')
                if '.' not in ticker and len(ticker) == 6:
                    ticker = f"{ticker[:3]}.{ticker[3:]}"

            conid = self.resolve_conid(ticker, sec_type)
            if not conid: return {"status": "error", "message": f"Could not resolve conid for {ticker}"}
            
            # ensure conid is an integer
            try:
                conid = int(conid)
            except:
                pass
            
            # Format quantity
            # IBKR API is picky.
            # For STK, it often wants a number (int/float).
            # For CASH, it definitely wants a number.
            # We'll ensure it's a number, not a string.
            qty_val = float(quantity) 

            payload = {
                "orders": [
                    {
                        "conid": int(conid), # Ensure strict int
                        "secType": sec_type,
                        "orderType": order_type,
                        "side": action.upper(), # BUY / SELL
                        "quantity": qty_val,
                        "tif": "GTC" # Changed from DAY to GTC to see if it helps, though DAY is usually fine.
                    }
                ]
            }
            
            # Submit Order
            logger.info(f"Submitting Order Payload: {payload}")
            resp = self.session.post(f"{self.base_url}/iserver/account/{account_id}/orders", json=payload)
            
            # Handle reply-required (IBKR Gateway sometimes asks for confirmation)
            if resp.status_code == 200:
                data = resp.json()
                # Check if we need to confirm (reply required)
                if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
                    reply_id = data[0]["id"]
                    # Auto-confirm typical warnings
                    confirm_resp = self.session.post(f"{self.base_url}/iserver/reply/{reply_id}", json={"confirmed": True})
                    return {"status": "success", "data": confirm_resp.json(), "orderId": reply_id}
                
                return {"status": "success", "data": data}
            else:
                return {"status": "error", "message": resp.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

ib_web_service = IBKRWebAPIService()
