import base64
import logging
import os
import tempfile
import docker

logger = logging.getLogger(__name__)


class CodeInterpreter:
    DOCKER_IMAGE = "code-interpreter-sandbox:latest"
    BASE_IMAGE = "python:3.12-slim"
    TIMEOUT_SECONDS = 30
    PRE_INSTALLED = ["pandas", "matplotlib", "numpy", "scipy", "seaborn", "requests"]

    def __init__(self) -> None:
        try:
            self._client = docker.from_env()
        except Exception as e:
            self._client = None
            logger.warning("Docker client failed to initialize: %s", e)

    def _ensure_image(self) -> None:
        if not self._client:
            return
        try:
            self._client.images.get(self.DOCKER_IMAGE)
        except docker.errors.ImageNotFound:
            logger.info("Building sandbox Docker image: %s", self.DOCKER_IMAGE)
            with tempfile.TemporaryDirectory() as tmpdir:
                dockerfile_content = f"""FROM {self.BASE_IMAGE}
RUN pip install --no-cache-dir {' '.join(self.PRE_INSTALLED)}
"""
                with open(os.path.join(tmpdir, "Dockerfile"), "w") as f:
                    f.write(dockerfile_content)
                self._client.images.build(path=tmpdir, tag=self.DOCKER_IMAGE, rm=True)

    def execute(self, code: str) -> dict:
        if not self._client:
            return {
                "stdout": "",
                "stderr": "Docker daemon is not running or Docker is not installed.",
                "plots": [],
                "error": "Docker unavailable",
            }

        try:
            self._ensure_image()
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Failed to build or find Docker sandbox image: {e}",
                "plots": [],
                "error": "Docker image error",
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Ensure container has write permission to bind mount in some OS environments
            os.chmod(tmpdir, 0o777)
            code_path = os.path.join(tmpdir, "run.py")
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)

            try:
                container = self._client.containers.create(
                    self.DOCKER_IMAGE,
                    command="python /code/run.py",
                    volumes={tmpdir: {"bind": "/code", "mode": "rw"}},
                    working_dir="/code",
                    mem_limit="256m",
                    network_disabled=True,
                    user="root",
                )
                container.start()

                # Wait for completion or timeout
                result_status = container.wait(timeout=self.TIMEOUT_SECONDS)
                exit_code = result_status.get("StatusCode", 0)

                logs_bytes = container.logs(stdout=True, stderr=False)
                err_bytes = container.logs(stdout=False, stderr=True)

                container.remove(force=True)

                stdout = logs_bytes.decode("utf-8", errors="replace")
                stderr = err_bytes.decode("utf-8", errors="replace")

                # If execution failed with non-zero exit code
                if exit_code != 0 and not stderr:
                    stderr = f"Exit code: {exit_code}"

                # Extract generated plot files (.png)
                plots = []
                for filename in os.listdir(tmpdir):
                    if filename.endswith(".png"):
                        file_path = os.path.join(tmpdir, filename)
                        with open(file_path, "rb") as img_file:
                            encoded_img = base64.b64encode(img_file.read()).decode("utf-8")
                            plots.append(encoded_img)

                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "plots": plots,
                    "error": stderr if exit_code != 0 else None,
                }

            except docker.errors.ContainerError as ce:
                return {
                    "stdout": "",
                    "stderr": str(ce),
                    "plots": [],
                    "error": str(ce),
                }
            except Exception as e:
                return {
                    "stdout": "",
                    "stderr": str(e),
                    "plots": [],
                    "error": str(e),
                }
