class GLPIAuthError(Exception):
    def __init__(self, message: str = "Erro de autenticação GLPI", status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GLPISearchError(Exception):
    def __init__(self, message: str = "Erro ao consultar GLPI", status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GLPINetworkError(Exception):
    def __init__(self, message: str = "Falha de comunicação com GLPI", timeout: bool = False):
        super().__init__(message)
        self.timeout = timeout