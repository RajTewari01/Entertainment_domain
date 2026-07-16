from __future__ import annotations
from typing import(
    List,Literal,cast,Any,TypeAlias
)
from pathlib import Path

PathType : TypeAlias = str | Path

class AssetsNotFound(FileNotFoundError):
    def __init__(self,path:PathType,message:str|None=None):
        self.path : str = str(path)
        self.message = message or f"{Path(self.path).name} not found. Please check your assets folder."
        super().__init__(self.message)

    def __str__(self)->str:
        return f"{self.path} :: {self.message}\n{self.__class__.__name__}"

class DirectoryNotFound(FileNotFoundError):
    def __init__(
        self,
        path:PathType,
        message:str|None=None
    ):
        self.path : str = str(path)
        self.message : str = message or f"{Path(self.path).name} directory not found."
        super().__init__(self.message)

    def __str__(self)->str:
        return f"{self.path} :: {self.message}\n{self.__class__.__name__}"

class ImageNotFound(FileNotFoundError):
    def __init__(
        self,
        path:PathType,
        message:str|None=None
    ):
        self.path : str = str(path)
        self.message : str = message or f"{Path(self.path).name} image not found."
        super().__init__(self.message)

    def __str__(self)->str:
        return f"{self.path} :: {self.message}\n{self.__class__.__name__}"

class VideoNotFound(FileNotFoundError):
    def __init__(
        self,
        path:PathType,
        message:str|None=None
    ):
        self.path : str = str(path)
        self.message : str = message or f"{Path(self.path).name} video not found."
        super().__init__(self.message)

    def __str__(self)->str:
        return f"{self.path} :: {self.message}\n{self.__class__.__name__}"

class AudioNotFound(FileNotFoundError):
    def __init__(
        self,
        path:PathType,
        message:str|None=None
    ):
        self.path : str = str(path)
        self.message : str = message or f"{Path(self.path).name} audio not found."
        super().__init__(self.message)

    def __str__(self)->str:
        return f"{self.path} :: {self.message}\n{self.__class__.__name__}"


class InvalidAssetPath(FileNotFoundError):
    def __init__(
        self,
        path:PathType,
        message:str|None=None
    ):
        self.path : str = str(path)
        self.message : str = message or f"{Path(self.path).name} invalid asset path."
        super().__init__(self.message)

    def __str__(self)->str:
        return f"{self.path} :: {self.message}\n{self.__class__.__name__}"






