# Future VM / headless Blender execution

The Dockerfile is a **starting build environment**, not a provisioned VM or a running remote desktop.

Try on a Linux host with Docker:

~~~sh
docker build -t telanico-blender -f infra/Dockerfile .
docker run --rm -v "$(pwd)/blender/generated:/workspace/blender/generated" -v "$(pwd)/godot/assets/generated:/workspace/godot/assets/generated" telanico-blender
~~~

Blender generation and GLB export run headlessly without a GPU. Preview renders or interactive Blender desktop sessions may require a different machine and GPU drivers.

A future worker could use GitHub Actions, Docker on a cloud VM, or a Codex environment with Blender installed. Never add tokens or credentials to Dockerfile/Git commits.

For remote access from iPhone, prefer submitting Codex Cloud tasks or GitHub workflow dispatch jobs and then retrieving artifacts; avoid exposing a VM's desktop directly to the public internet.
