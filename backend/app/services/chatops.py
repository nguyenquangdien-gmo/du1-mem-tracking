import httpx
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

async def send_chatops_message(group_id: str, message: str) -> bool:
    if not group_id:
        logger.warning("No ChatOps group ID configured, skipping message.")
        return False
        
    url = f"{os.getenv('CHATOPS_URL')}/api/v4/posts"
    headers = {
        "Authorization": f"Bearer {os.getenv('CHATOPS_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    props = {}
    assistant_id = os.getenv("CHATOPS_ASSISTANT_ID")
    if assistant_id:
        props["assistant_id"] = assistant_id
        
    payload = {
        "channel_id": group_id,
        "message": message,
        "props": props
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers, timeout=10.0)
            resp.raise_for_status()
            logger.info("Successfully sent ChatOps message")
            return True
        except Exception as e:
            logger.error(f"Error sending ChatOps message: {e}")
            return False
