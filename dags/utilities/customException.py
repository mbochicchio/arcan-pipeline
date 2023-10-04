class SettingsException(Exception):
    pass

class ProjectNotFoundException(Exception):
    pass

class ArcanOutputNotFoundException(Exception):
    status="EMPTY_DEPENDENCY_GRAPH"

class GitRestApiException(Exception):
    pass

class GitRestApiForbiddenException(GitRestApiException):
    pass

class MakeDirException(Exception):
    pass

class DeleteDirException(Exception):
    pass

class CloneRepositoryException(Exception):
    status="CANNOT_CLONE_REPOSITORY"

class CheckoutRepositoryException(Exception):
    status="CANNOT_CHECKOUT_BRANCH"

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
    status="ARCAN_INTERNAL_ERROR"

class MaximumExecutionTimeExeededException(Exception):
    status="MAXIMUM_EXECUTION_TIME_EXCEEDED"

class BenchmarkImageNotFoundException(Exception):
    pass

class BenchmarkExecutionException(Exception):
    pass