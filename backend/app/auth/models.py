from enum import Enum

class UserRole(str, Enum):
    ADMIN = "Admin"
    HELPDESK = "HelpDesk"
    HR = "HR"
    AUDITOR = "Auditor"
