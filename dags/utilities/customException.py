class SettingsException(Exception):
    pass

class ProjectNotFoundException(Exception):
    pass

class DependencyGraphNotFoundException(Exception):
    pass

class ArcanOutputNotFoundException(Exception):
    pass

class GitRestApiException(Exception):
    pass

class ArcanException(Exception):
    pass

class MakeDirException(Exception):
    pass

class DeleteDirException(Exception):
    pass

class CloneRepositoryException(Exception):
    pass

class CheckoutRepositoryException(Exception):
    pass

class GitRestApiProjectNotFoundException(GitRestApiException):
    pass

class GitRestApiValidationFailedException(GitRestApiException):
    pass

class DockerApiException(Exception):
    pass

class DockerException(Exception):
    pass

class ArcanImageNotFoundException(Exception):
    pass

class ArcanExecutionException(Exception):
    pass

