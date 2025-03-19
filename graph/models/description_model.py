from typing import TypedDict, Union, Literal, Optional
from dataclasses import dataclass
# Possible color values for icons
ThemeIconColor = Literal[
    "gray",
    "black",
    "blue",
    "light-blue",
    "dark-blue",
    "orange",
    "orange-red",
    "pink-red",
    "red",
    "light-green",
    "green",
    "dark-green",
    "azure",
    "purple",
    "crimson",
]

class LightDarkStr(TypedDict):
    light: str
    dark: str

ThemedString = Union[str, LightDarkStr]

Icon = Union[str, ThemedString]

class CodexData(TypedDict, total=False):
    details: str

@dataclass
class NodeTypeBaseDescription:
    displayName: str
    name: str
    icon: Icon
    iconColor: ThemeIconColor
    iconUrl: ThemedString
    badgeIconUrl: ThemedString
    group: list[str]
    description: str
    documentationUrl: str
    subtitle: str
    defaultVersion: int
    codex: CodexData
    parameterPane: Literal["wide"]
    hidden: bool
    usableAsTool: bool

@dataclass
class NodeTypeDescription(NodeTypeBaseDescription):
    pass