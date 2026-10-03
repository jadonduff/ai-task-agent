#!/bin/bash

llama-server \
  -m "$LLAMA_MODEL_PATH" \
  --host 127.0.0.1 \
  --port 6575 \
  -c 100000 \
  -ctk f16 \
  -ctv f16 \
  --load-mode mmap+mlock \
  --temp 1.0 \
  --top-p 0.95 \
  --top-k 20 \
  --min-p 0 \
  --repeat-penalty 1.0 \
  --presence-penalty 0 \
  --reasoning on \
  --reasoning-effort low \
  --spec-type draft-mtp,ngram-mod \
  --spec-ngram-mod-n-min 1 \
  --spec-ngram-mod-n-max 8 \
  --spec-ngram-mod-n-match 24
