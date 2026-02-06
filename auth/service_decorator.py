import inspect
import logging

from functools import wraps
from typing import Dict, List, Optional, Any, Callable, Union, Tuple

from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from fastmcp.server.dependencies import get_access_token, get_context
from auth.google_auth import get_authenticated_google_service, GoogleAuthenticationError
from auth.oauth21_session_store import (
    get_auth_provider,
    get_oauth21_session_store,
    ensure_session_from_access_token,
)
from auth.oauth_config import (
    is_oauth21_enabled,
    get_oauth_config,
)
from core.context import set_fastmcp_session_id
from auth.scopes import (
    GMAIL_READONLY_SCOPE,
    GMAIL_SEND_SCOPE,
    GMAIL_COMPOSE_SCOPE,
    GMAIL_MODIFY_SCOPE,
    GMAIL_LABELS_SCOPE,
    GMAIL_SETTINGS_BASIC_SCOPE,
    DRIVE_READONLY_SCOPE,
    DRIVE_FILE_SCOPE,
    DOCS_READONLY_SCOPE,
    DOCS_WRITE_SCOPE,
    CALENDAR_READONLY_SCOPE,
    CALENDAR_EVENTS_SCOPE,
    SHEETS_READONLY_SCOPE,
    SHEETS_WRITE_SCOPE,
    CHAT_READONLY_SCOPE,
    CHAT_WRITE_SCOPE,
    CHAT_SPACES_SCOPE,
    FORMS_BODY_SCOPE,
    FORMS_BODY_READONLY_SCOPE,
    FORMS_RESPONSES_READONLY_SCOPE,
    SLIDES_SCOPE,
    SLIDES_READONLY_SCOPE,
    TASKS_SCOPE,
    TASKS_READONLY_SCOPE,
    CONTACTS_SCOPE,
    CONTACTS_READONLY_SCOPE,
    CUSTOM_SEARCH_SCOPE,
    SCRIPT_PROJECTS_SCOPE,
    SCRIPT_PROJECTS_READONLY_SCOPE,
    SCRIPT_DEPLOYMENTS_SCOPE,
    SCRIPT_DEPLOYMENTS_READONLY_SCOPE,
)

logger = logging.getLogger(__name__)


# Authentication helper functions
def _get_auth_context(
    tool_name: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get authentication context from FastMCP.

    Returns:
        Tuple of (authenticated_user, auth_method, mcp_session_id)
    """
    try:
        ctx = get_context()
        if not ctx:
            return None, None, None

        authenticated_user = ctx.get_state("authenticated_user_email")
        auth_method = ctx.get_state("authenticated_via")
        mcp_session_id = ctx.session_id if hasattr(ctx, "session_id") else None

        if mcp_session_id:
            set_fastmcp_session_id(mcp_session_id)

        logger.info(
            f"[{tool_name}] Auth from middleware: authenticated_user={authenticated_user}, auth_method={auth_method}, session_id={mcp_session_id}"
        )
        return authenticated_user, auth_method, mcp_session_id

    except Exception as e:
        logger.debug(f"[{tool_name}] Could not get FastMCP context: {e}")
        return None, None, None


def _detect_oauth_version(
    authenticated_user: Optional[str], mcp_session_id: Optional[str], tool_name: str
) -> bool:
    """
    Detect whether to use OAuth 2.1 based on configuration and context.

    Returns:
        True if OAuth 2.1 should be used, False otherwise
    """
    if not is_oauth21_enabled():
        return False

    # When OAuth 2.1 is enabled globally, ALWAYS use OAuth 2.1 for authenticated users
    if authenticated_user:
        logger.info(
            f"[{tool_name}] OAuth 2.1 mode: Using OAuth 2.1 for authenticated user '{authenticated_user}'"
        )
        return True

    # If FastMCP protocol-level auth is enabled, a validated access token should
    # be available even if middleware state wasn't populated.
    try:
        if get_access_token() is not None:
            logger.info(
                f"[{tool_name}] OAuth 2.1 mode: Using OAuth 2.1 based on validated access token"
            )
            return True
    except Exception as e:
        logger.debug(
            f"[{tool_name}] Could not inspect access token for OAuth mode: {e}"
        )

    # Only use version detection for unauthenticated requests
    config = get_oauth_config()
    request_params = {}
    if mcp_session_id:
        request_params["session_id"] = mcp_session_id

    oauth_version = config.detect_oauth_version(request_params)
    use_oauth21 = oauth_version == "oauth21"
    logger.info(
        f"[{tool_name}] OAuth version detected: {oauth_version}, will use OAuth 2.1: {use_oauth21}"
    )
    return use_oauth21


async def _authenticate_service(
    use_oauth21: bool,
    service_name: str,
    service_version: str,
    tool_name: str,
    resolved_scopes: List[str],
    mcp_session_id: Optional[str],
    authenticated_user: Optional[str],
) -> Tuple[Any, str]:
    """
    Authenticate and get Google service using appropriate OAuth version.

    Returns:
        Tuple of (service, actual_user_email)
    """
    if use_oauth21:
        logger.debug(f"[{tool_name}] Using OAuth 2.1 flow")
        return await get_authenticated_google_service_oauth21(
            service_name=service_name,
            version=service_version,
            tool_name=tool_name,
            required_scopes=resolved_scopes,
            session_id=mcp_session_id,
            auth_token_email=authenticated_user,
            allow_recent_auth=False,
        )
    else:
        logger.debug(f"[{tool_name}] Using legacy OAuth 2.0 flow")
        return await get_authenticated_google_service(
            service_name=service_name,
            version=service_version,
            tool_name=tool_name,
            required_scopes=resolved_scopes,
            session_id=mcp_session_id,
        )


async def get_authenticated_google_service_oauth21(
    service_name: str,
    version: str,
    tool_name: str,
    required_scopes: List[str],
    session_id: Optional[str] = None,
    auth_token_email: Optional[str] = None,
    allow_recent_auth: bool = False,
) -> tuple[Any, str]:
    """
    OAuth 2.1 authentication using the session store with security validation.
    """
    provider = get_auth_provider()
    access_token = get_access_token()

    if provider and access_token:
        token_email = None
        if getattr(access_token, "claims", None):
            token_email = access_token.claims.get("email")

        resolved_email = token_email or auth_token_email
        if not resolved_email:
            raise GoogleAuthenticationError(
                "Authenticated user email could not be determined from access token."
            )

        if auth_token_email and token_email and token_email != auth_token_email:
            raise GoogleAuthenticationError(
                "Access token email does not match authenticated session context."
            )

        credentials = ensure_session_from_access_token(
            access_token, resolved_email, session_id
        )
        if not credentials:
            raise GoogleAuthenticationError(
                "Unable to build Google credentials from authenticated access token."
            )

        scopes_available = set(credentials.scopes or [])
        if not scopes_available and getattr(access_token, "scopes", None):
            scopes_available = set(access_token.scopes)

        if not all(scope in scopes_available for scope in required_scopes):
            raise GoogleAuthenticationError(
                f"OAuth credentials lack required scopes. Need: {required_scopes}, Have: {sorted(scopes_available)}"
            )

        service = build(service_name, version, credentials=credentials)
        logger.info(f"[{tool_name}] Authenticated {service_name} for {resolved_email}")
        return service, resolved_email

    store = get_oauth21_session_store()

    if not auth_token_email:
        raise GoogleAuthenticationError(
            "Access denied: Cannot retrieve credentials without authenticated user email."
        )

    # Use the validation method to ensure session can only access its own credentials
    credentials = store.get_credentials_with_validation(
        requested_user_email=auth_token_email,
        session_id=session_id,
        auth_token_email=auth_token_email,
        allow_recent_auth=allow_recent_auth,
    )

    if not credentials:
        raise GoogleAuthenticationError(
            f"Access denied: Cannot retrieve credentials for {auth_token_email}. "
            f"You can only access credentials for your authenticated account."
        )

    if not credentials.scopes:
        scopes_available = set(required_scopes)
    else:
        scopes_available = set(credentials.scopes)

    if not all(scope in scopes_available for scope in required_scopes):
        raise GoogleAuthenticationError(
            f"OAuth 2.1 credentials lack required scopes. Need: {required_scopes}, Have: {sorted(scopes_available)}"
        )

    service = build(service_name, version, credentials=credentials)
    logger.info(f"[{tool_name}] Authenticated {service_name} for {auth_token_email}")

    return service, auth_token_email


# Service configuration mapping
SERVICE_CONFIGS = {
    "gmail": {"service": "gmail", "version": "v1"},
    "drive": {"service": "drive", "version": "v3"},
    "calendar": {"service": "calendar", "version": "v3"},
    "docs": {"service": "docs", "version": "v1"},
    "sheets": {"service": "sheets", "version": "v4"},
    "chat": {"service": "chat", "version": "v1"},
    "forms": {"service": "forms", "version": "v1"},
    "slides": {"service": "slides", "version": "v1"},
    "tasks": {"service": "tasks", "version": "v1"},
    "people": {"service": "people", "version": "v1"},
    "customsearch": {"service": "customsearch", "version": "v1"},
    "script": {"service": "script", "version": "v1"},
}


# Scope group definitions for easy reference
SCOPE_GROUPS = {
    # Gmail scopes
    "gmail_read": GMAIL_READONLY_SCOPE,
    "gmail_send": GMAIL_SEND_SCOPE,
    "gmail_compose": GMAIL_COMPOSE_SCOPE,
    "gmail_modify": GMAIL_MODIFY_SCOPE,
    "gmail_labels": GMAIL_LABELS_SCOPE,
    "gmail_settings_basic": GMAIL_SETTINGS_BASIC_SCOPE,
    # Drive scopes
    "drive_read": DRIVE_READONLY_SCOPE,
    "drive_file": DRIVE_FILE_SCOPE,
    # Docs scopes
    "docs_read": DOCS_READONLY_SCOPE,
    "docs_write": DOCS_WRITE_SCOPE,
    # Calendar scopes
    "calendar_read": CALENDAR_READONLY_SCOPE,
    "calendar_events": CALENDAR_EVENTS_SCOPE,
    # Sheets scopes
    "sheets_read": SHEETS_READONLY_SCOPE,
    "sheets_write": SHEETS_WRITE_SCOPE,
    # Chat scopes
    "chat_read": CHAT_READONLY_SCOPE,
    "chat_write": CHAT_WRITE_SCOPE,
    "chat_spaces": CHAT_SPACES_SCOPE,
    # Forms scopes
    "forms": FORMS_BODY_SCOPE,
    "forms_read": FORMS_BODY_READONLY_SCOPE,
    "forms_responses_read": FORMS_RESPONSES_READONLY_SCOPE,
    # Slides scopes
    "slides": SLIDES_SCOPE,
    "slides_read": SLIDES_READONLY_SCOPE,
    # Tasks scopes
    "tasks": TASKS_SCOPE,
    "tasks_read": TASKS_READONLY_SCOPE,
    # Contacts scopes
    "contacts": CONTACTS_SCOPE,
    "contacts_read": CONTACTS_READONLY_SCOPE,
    # Custom Search scope
    "customsearch": CUSTOM_SEARCH_SCOPE,
    # Apps Script scopes
    "script_readonly": SCRIPT_PROJECTS_READONLY_SCOPE,
    "script_projects": SCRIPT_PROJECTS_SCOPE,
    "script_deployments": SCRIPT_DEPLOYMENTS_SCOPE,
    "script_deployments_readonly": SCRIPT_DEPLOYMENTS_READONLY_SCOPE,
}


def _resolve_scopes(scopes: Union[str, List[str]]) -> List[str]:
    """Resolve scope names to actual scope URLs."""
    if isinstance(scopes, str):
        if scopes in SCOPE_GROUPS:
            return [SCOPE_GROUPS[scopes]]
        else:
            return [scopes]

    resolved = []
    for scope in scopes:
        if scope in SCOPE_GROUPS:
            resolved.append(SCOPE_GROUPS[scope])
        else:
            resolved.append(scope)
    return resolved


def _handle_token_refresh_error(
    error: RefreshError, user_email: str, service_name: str
) -> str:
    """
    Handle token refresh errors gracefully, particularly expired/revoked tokens.

    Args:
        error: The RefreshError that occurred
        user_email: User's email address
        service_name: Name of the Google service

    Returns:
        A user-friendly error message with instructions for reauthentication
    """
    error_str = str(error)

    if (
        "invalid_grant" in error_str.lower()
        or "expired or revoked" in error_str.lower()
    ):
        logger.warning(
            f"Token expired or revoked for user {user_email} accessing {service_name}"
        )

        service_display_name = f"Google {service_name.title()}"

        return (
            f"**Authentication Required: Token Expired/Revoked for {service_display_name}**\n\n"
            f"Your Google authentication token for {user_email} has expired or been revoked. "
            f"This commonly happens when:\n"
            f"- The token has been unused for an extended period\n"
            f"- You've changed your Google account password\n"
            f"- You've revoked access to the application\n\n"
            f"**To resolve this, please:**\n"
            f"1. Run `start_google_auth` with your email ({user_email}) and service_name='{service_display_name}'\n"
            f"2. Complete the authentication flow in your browser\n"
            f"3. Retry your original command\n\n"
            f"The application will automatically use the new credentials once authentication is complete."
        )
    else:
        # Handle other types of refresh errors
        logger.error(f"Unexpected refresh error for user {user_email}: {error}")
        return (
            f"Authentication error occurred for {user_email}. "
            f"Please try running `start_google_auth` with your email and the appropriate service name to reauthenticate."
        )


def require_google_service(
    service_type: str,
    scopes: Union[str, List[str]],
    version: Optional[str] = None,
):
    """
    Decorator that automatically handles Google service authentication and injection.

    Args:
        service_type: Type of Google service ("gmail", "drive", "calendar", etc.)
        scopes: Required scopes (can be scope group names or actual URLs)
        version: Service version (defaults to standard version for service type)

    Usage:
        @require_google_service("gmail", "gmail_read")
        async def search_messages(service, query: str):
            # service parameter is automatically injected
            # Original authentication logic is handled automatically
    """

    def decorator(func: Callable) -> Callable:
        original_sig = inspect.signature(func)
        params = list(original_sig.parameters.values())

        # The decorated function must have 'service' as its first parameter.
        if not params or params[0].name != "service":
            raise TypeError(
                f"Function '{func.__name__}' decorated with @require_google_service "
                "must have 'service' as its first parameter."
            )

        # Create a new signature for the wrapper that excludes the 'service' parameter.
        wrapper_sig = original_sig.replace(parameters=params[1:])

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Note: `args` and `kwargs` are now the arguments for the *wrapper*,
            # which does not include 'service'.

            # Get authentication context early to determine OAuth mode
            authenticated_user, auth_method, mcp_session_id = _get_auth_context(
                func.__name__
            )

            if not authenticated_user:
                raise Exception(
                    f"Authentication required for {func.__name__}, but no authenticated user was found."
                )

            # Get service configuration from the decorator's arguments
            if service_type not in SERVICE_CONFIGS:
                raise Exception(f"Unknown service type: {service_type}")

            config = SERVICE_CONFIGS[service_type]
            service_name = config["service"]
            service_version = version or config["version"]

            # Resolve scopes
            resolved_scopes = _resolve_scopes(scopes)

            try:
                tool_name = func.__name__

                # Log authentication status
                logger.debug(
                    f"[{tool_name}] Auth: {authenticated_user or 'none'} via {auth_method or 'none'} (session: {mcp_session_id[:8] if mcp_session_id else 'none'})"
                )

                # Detect OAuth version
                use_oauth21 = _detect_oauth_version(
                    authenticated_user, mcp_session_id, tool_name
                )

                # Authenticate service
                service, actual_user_email = await _authenticate_service(
                    use_oauth21,
                    service_name,
                    service_version,
                    tool_name,
                    resolved_scopes,
                    mcp_session_id,
                    authenticated_user,
                )
            except GoogleAuthenticationError as e:
                logger.error(
                    f"[{tool_name}] GoogleAuthenticationError during authentication. "
                    f"Method={auth_method or 'none'}, User={authenticated_user or 'none'}, "
                    f"Service={service_name} v{service_version}, MCPSessionID={mcp_session_id or 'none'}: {e}"
                )
                # Re-raise the original error without wrapping it
                raise

            try:
                # Prepend the fetched service object to the original arguments
                return await func(service, *args, **kwargs)
            except RefreshError as e:
                error_message = _handle_token_refresh_error(
                    e, actual_user_email, service_name
                )
                raise Exception(error_message)

        # Set the wrapper's signature to the one without 'service'
        wrapper.__signature__ = wrapper_sig

        # Attach required scopes to the wrapper for tool filtering
        wrapper._required_google_scopes = _resolve_scopes(scopes)

        return wrapper

    return decorator


def require_multiple_services(service_configs: List[Dict[str, Any]]):
    """
    Decorator for functions that need multiple Google services.

    Args:
        service_configs: List of service configurations, each containing:
            - service_type: Type of service
            - scopes: Required scopes
            - param_name: Name to inject service as (e.g., 'drive_service', 'docs_service')
            - version: Optional version override

    Usage:
        @require_multiple_services([
            {"service_type": "drive", "scopes": "drive_read", "param_name": "drive_service"},
            {"service_type": "docs", "scopes": "docs_read", "param_name": "docs_service"}
        ])
        async def get_doc_with_metadata(drive_service, docs_service, doc_id: str):
            # Both services are automatically injected
    """

    def decorator(func: Callable) -> Callable:
        original_sig = inspect.signature(func)

        service_param_names = {config["param_name"] for config in service_configs}
        params = list(original_sig.parameters.values())

        # Remove injected service params from the wrapper signature
        filtered_params = [p for p in params if p.name not in service_param_names]

        wrapper_sig = original_sig.replace(parameters=filtered_params)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get authentication context early
            tool_name = func.__name__
            authenticated_user, _, mcp_session_id = _get_auth_context(tool_name)

            if not authenticated_user:
                raise Exception(
                    f"Authentication required for {tool_name}, but no authenticated user was found."
                )

            # Authenticate all services
            for config in service_configs:
                service_type = config["service_type"]
                scopes = config["scopes"]
                param_name = config["param_name"]
                version = config.get("version")

                if service_type not in SERVICE_CONFIGS:
                    raise Exception(f"Unknown service type: {service_type}")

                service_config = SERVICE_CONFIGS[service_type]
                service_name = service_config["service"]
                service_version = version or service_config["version"]
                resolved_scopes = _resolve_scopes(scopes)

                try:
                    # Detect OAuth version (simplified for multiple services)
                    use_oauth21 = (
                        is_oauth21_enabled() and authenticated_user is not None
                    )

                    # Authenticate service
                    service, _ = await _authenticate_service(
                        use_oauth21,
                        service_name,
                        service_version,
                        tool_name,
                        resolved_scopes,
                        mcp_session_id,
                        authenticated_user,
                    )

                    # Inject service with specified parameter name
                    kwargs[param_name] = service

                except GoogleAuthenticationError as e:
                    logger.error(
                        f"[{tool_name}] GoogleAuthenticationError for service '{service_type}' (user: {authenticated_user}): {e}"
                    )
                    # Re-raise the original error without wrapping it
                    raise

            # Call the original function with refresh error handling
            try:
                return await func(*args, **kwargs)
            except RefreshError as e:
                # Handle token refresh errors gracefully
                error_message = _handle_token_refresh_error(
                    e, authenticated_user, "Multiple Services"
                )
                raise Exception(error_message)

        # Set the wrapper's signature
        wrapper.__signature__ = wrapper_sig

        # Attach all required scopes to the wrapper for tool filtering
        all_scopes = []
        for config in service_configs:
            all_scopes.extend(_resolve_scopes(config["scopes"]))
        wrapper._required_google_scopes = all_scopes

        return wrapper

    return decorator
