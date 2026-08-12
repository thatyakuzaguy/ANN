"""Generated, deterministic product-domain contract."""

DOMAIN_ID = "ai_chatbot"
DOMAIN_NAME = "AI Chatbot SaaS"
DOMAIN_DESCRIPTION = "Tenant chat, conversations, messages, model providers, usage limits, and support handoff."
ENTITIES = [
    "chat",
    "conversation",
    "message",
    "model",
    "provider",
    "knowledge_base",
    "usage_event"
]
WORKFLOWS = [
    "stream response",
    "support handoff",
    "quality review",
    "usage alert"
]
INTEGRATIONS = [
    "local model",
    "Stripe",
    "vector store",
    "helpdesk"
]
ENTITY_TYPES = frozenset(ENTITIES)
