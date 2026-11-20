#!/bin/bash
for name in MCP_TOKEN LLAMA_API_KEY; do
  if [ -f .env ]; then
    grep -Eq "^${name}=[^[:space:]]" .env && continue
    if grep -q "^${name}=" .env; then
      echo "${name} is empty in .env. Fill it in or delete that line." >&2
      exit 1
    fi
    [ -n "$(tail -c1 .env)" ] && echo >> .env
  fi
  echo "${name}=$(openssl rand -hex 24)" >> .env
  echo "Added ${name} to .env."
done