import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "pages.yml"


class DeploymentWorkflowTests(unittest.TestCase):
    def test_pages_workflow_verifies_before_deploying_dist(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("pull_request:", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("actions/checkout@v6", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertIn("actions/configure-pages@v5", workflow)
        self.assertIn("actions/upload-pages-artifact@v4", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("pages: read", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn(
            "python tools/site_builder.py build --root . --output dist", workflow
        )
        self.assertIn(
            "python tools/site_audit.py check --root dist", workflow
        )
        self.assertIn("needs: build", workflow)
        self.assertIn("path: dist", workflow)
        self.assertIn("include-hidden-files: true", workflow)
        self.assertNotIn("path: '.'", workflow)


if __name__ == "__main__":
    unittest.main()
