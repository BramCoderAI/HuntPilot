from dataclasses import dataclass


@dataclass
class ProjectInfo:
    name: str
    folder_name: str
    created_at: str
    updated_at: str