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
        """
        try:
            resp = self.session.get(f"{self.base_url}/iserver/secdef/search?symbol={ticker}")
            if resp.ok:
                results = resp.json()
                # Filter for exact match and secType
                for res in results:
                    if res.get('symbol') == ticker.upper():
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
            conid = self.resolve_conid(ticker)
            if not conid: return {"status": "error", "message": f"Could not resolve conid for {ticker}"}
            
            payload = {
                "orders": [
                    {
                        "conid": conid,
                        "secType": "STK",
                        "orderType": order_type,
                        "side": action.upper(), # BUY / SELL
                        "quantity": float(quantity),
                        "tif": "DAY"
                    }
                ]
            }
            
            # Submit Order
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
