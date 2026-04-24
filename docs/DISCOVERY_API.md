# Provider Discovery API — Added to hybrid-collab-bridge

## New Endpoints

### POST /v1/discover
Discover or query AI providers.

**Request:**
```json
{
  "query": "kimi",
  "scan_type": "auto"
}
```

**Query values:**
| Query | Behavior |
|-------|----------|
| `"other"`, `"scan"`, `"all"` | Full scan: local + env + network |
| `"local"`, `"on-premise"` | Scan only localhost/127.0.0.1 |
| `"cloud"`, `"env"`, `"api"` | Scan only environment variables |
| `"openai"`, `"kimi"`, etc. | Query specific provider |

**Response:**
```json
{
  "scan_type": "query",
  "results": [
    {
      "provider_id": "kimi",
      "provider_name": "Moonshot AI (Kimi)",
      "status": "discoverable",
      "reason": "API key not found: MOONSHOT_API_KEY",
      "connection_method": "manual",
      "instructions": [
        "1. Sign up: https://platform.moonshot.ai",
        "2. Get API key and set env var: MOONSHOT_API_KEY=your-key",
        "3. Pricing: https://platform.moonshot.ai/pricing",
        "4. Docs: https://platform.moonshot.ai/docs"
      ],
      "config_template": { "name": "kimi", "type": "kimi_text", ... },
      "requires_network": true,
      "requires_api_key": true,
      "estimated_cost_tier": "standard"
    }
  ],
  "total_found": 1,
  "total_available": 0,
  "total_discoverable": 1,
  "total_denied": 0
}
```

### GET /v1/discover/scan
Quick scan — returns only currently available providers.

### POST /v1/discover/connect
Connect a discovered provider to the bridge.

**Request:**
```json
{
  "provider_id": "kimi",
  "provider_type": "kimi_text",
  "config": { "capabilities": ["text-generate"] },
  "test_connection": true
}
```

**Response:**
```json
{
  "status": "connected",
  "provider": "kimi",
  "test": { "success": true, "output": "connected" },
  "instructions": [
    "Provider 'kimi' added to providers.txt",
    "It is now available in /v1/run requests."
  ]
}
```

## Discovery Methods

| Method | What it scans | No-network fallback |
|--------|---------------|---------------------|
| **Local** | localhost:11434 (Ollama), :8000 (vLLM), :8080 (llama.cpp) | Always works if server running |
| **Environment** | Env vars: OPENAI_API_KEY, ANTHROPIC_API_KEY, etc. | Works offline if keys set |
| **Network** | 192.168.1.x, 10.0.0.x for LAN Ollama | Skips if no network |
| **Query** | Lookup by name in known provider registry | Returns manual setup instructions |

## Status Types

| Status | Meaning | User Action |
|--------|---------|-------------|
| `available` | Connected and ready | Use immediately |
| `discoverable` | Supported but not configured | Follow instructions to connect |
| `denied` | Not supported / no compatibility path | Use alternative or request integration |

## Denied Reasons (with alternatives)

When a provider is denied, the response includes:
- Why it cannot be connected (proprietary protocol, no public API, etc.)
- Alternative providers with similar capabilities
- Path to request governance integration (human+AI quorum)
- Instructions to build custom adapter if OpenAI-compatible
