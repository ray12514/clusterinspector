import shutil


def command_available(name: str) -> bool:
    return shutil.which(name) is not None
