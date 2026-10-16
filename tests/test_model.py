import unittest
from unittest.mock import Mock, patch

import model


class OllamaCloudTests(unittest.TestCase):
    def test_cloud_api_key_is_sent_as_bearer_token(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "message": {"content": "Food"},
        }
        with (
            patch.object(model, "OLLAMA_API_KEY", "test-cloud-key"),
            patch.object(model, "OLLAMA_URL", "https://ollama.com"),
            patch("model.requests.post", return_value=response) as post,
        ):
            category = model.categorize_expense("Lunch")

        self.assertEqual(category, "Food")
        self.assertEqual(
            post.call_args.kwargs["headers"],
            {"Authorization": "Bearer test-cloud-key"},
        )
        self.assertEqual(
            post.call_args.args[0],
            "https://ollama.com/api/chat",
        )

    def test_local_requests_do_not_send_auth_header(self):
        response = Mock()
        response.raise_for_status.return_value = None
        with (
            patch.object(model, "OLLAMA_API_KEY", ""),
            patch.object(model, "OLLAMA_URL", "http://localhost:11434"),
            patch("model.requests.get", return_value=response) as get,
        ):
            available, _ = model.ollama_status()

        self.assertTrue(available)
        self.assertEqual(get.call_args.kwargs["headers"], {})


if __name__ == "__main__":
    unittest.main()
