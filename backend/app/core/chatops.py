import requests
from ..config import get_settings

settings = get_settings()

class ChatOpsClient:
    def __init__(self):
        self.base_url = settings.chatops_url
        self.token = settings.chatops_token
        self.assistant_id = settings.chatops_assistant_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def get_user_by_email(self, email: str):
        """Lấy thông tin user bằng email trên Mattermost"""
        url = f"{self.base_url}/api/v4/users/email/{email}"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 200:
            return resp.json()
        return None

    def get_direct_channel_id(self, receiver_id: str):
        """Tạo/Lấy Direct Channel ID giữa Assistant và User"""
        url = f"{self.base_url}/api/v4/channels/direct"
        # Body là list gồm 2 user id
        body = [self.assistant_id, receiver_id]
        resp = requests.post(url, headers=self.headers, json=body)
        if resp.status_code == 201:
            return resp.json().get("id")
        return None

    def send_message(self, channel_id: str, message: str):
        """Gửi tin nhắn vào channel cụ thể"""
        url = f"{self.base_url}/api/v4/posts"
        body = {
            "channel_id": channel_id,
            "message": message.replace("<br>", "\n")
        }
        resp = requests.post(url, headers=self.headers, json=body)
        return resp.status_code == 201

    def send_private_message(self, email: str, message: str):
        """Helper để gửi tin nhắn private cho user qua email"""
        user = self.get_user_by_email(email)
        if not user:
            return False, "User not found on Mattermost"
        
        channel_id = self.get_direct_channel_id(user.get("id"))
        if not channel_id:
            return False, "Could not create direct channel"
        
        success = self.send_message(channel_id, message)
        return success, "Success" if success else "Failed to send message"

chatops = ChatOpsClient()
