#!/bin/sh
set -e

is_truthy() {
    case "$(echo "${1:-}" | tr '[:upper:]' '[:lower:]')" in
        1|true|yes|on) return 0 ;;
        *) return 1 ;;
    esac
}

if is_truthy "${SHARETREE_TRUST_HEADERS:-}"; then
    echo "Starting sharetree (trusted-headers mode, port 8000)..."
    exec sharetree
else
    if [ -z "${SHARETREE_ADMIN_PASSWORD:-}" ]; then
        echo "ERROR: SHARETREE_ADMIN_PASSWORD must be set when SHARETREE_TRUST_HEADERS is not enabled." >&2
        exit 1
    fi

    echo "Generating Caddy configuration..."
    HASH=$(caddy hash-password --plaintext "$SHARETREE_ADMIN_PASSWORD")

    cat > /tmp/Caddyfile << EOF
:80 {
    @admin {
        path /api/v1/admin/*
    }

    basicauth @admin {
        admin $HASH
    }

    reverse_proxy @admin localhost:8000 {
        header_up Remote-Groups "admins"
    }

    reverse_proxy localhost:8000
}
EOF

    # Tell the app to validate the Remote-Groups header forwarded by Caddy.
    # This ensures direct access to port 8000 (bypassing Caddy) still requires auth.
    export SHARETREE_TRUST_HEADERS=true

    echo "Starting sharetree on localhost:8000..."
    sharetree &

    echo "Starting Caddy reverse proxy on :80 (admin routes protected by basic auth)..."
    exec caddy run --config /tmp/Caddyfile
fi
