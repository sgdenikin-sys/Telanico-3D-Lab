# Baseline for a CPU-only headless Blender build on a future Linux VM.
# Ubuntu distro Blender may differ from desktop Blender; pin a matching
# official Blender release before requiring byte-for-byte output matching.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    blender python3 ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY . /workspace
CMD ["blender", "--background", "--python", "blender/scripts/build_smoke_test.py"]
