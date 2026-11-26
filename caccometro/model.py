"""Data types shared by every layer: the storage returns them, the rules and the replies read them."""
from typing import NamedTuple, Optional


class User(NamedTuple):
    """A Telegram user known to a chat."""
    user_id: int
    username: Optional[str]
    display_name: str

    @property
    def name(self):
        """Plain name for charts and tables: the username if any, otherwise the display name."""
        return self.username or self.display_name

    @property
    def mention(self):
        """Name for messages: '@username' if any, otherwise the display name."""
        return f"@{self.username}" if self.username else self.display_name
