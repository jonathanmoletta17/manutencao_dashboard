"""
Exceções específicas da integração GLPI.

- GLPIAuthError: falhas de autenticação/autorização (401/403).
- GLPISearchError: erros HTTP/semânticos ao consultar a API GLPI.
- GLPINetworkError: falhas de rede/timeout na comunicação com GLPI.

Cada exceção carrega atributos padronizados para facilitar logging e mapeamento:
- code: string curta identificando a classe do erro.
- status_code: código HTTP quando aplicável (ou None).
- timeout (apenas rede): indica se houve timeout.
"""


class GLPIAuthError(Exception):
    def __init__(
        self,
        message: str = "Erro de autenticação GLPI",
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.code = "GLPI_AUTH"
        self.status_code = status_code


class GLPISearchError(Exception):
    def __init__(
        self,
        message: str = "Erro ao consultar GLPI",
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.code = "GLPI_SEARCH"
        self.status_code = status_code


class GLPINetworkError(Exception):
    def __init__(
        self,
        message: str = "Falha de comunicação com GLPI",
        timeout: bool = False,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.code = "GLPI_NETWORK"
        self.timeout = timeout
        self.status_code = status_code