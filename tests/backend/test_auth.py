from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from api.auth.max import app


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()

    def test_employee_code_returns_employee(self) -> None:
        response = self.client.post(
            "/api/auth/max",
            json={"employeeCode": " bux-2048 ", "initData": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["code"], "BUX-2048")
        self.assertEqual(response.json()["displayName"], "Менеджер Buxme")

    def test_invalid_employee_code_is_rejected(self) -> None:
        response = self.client.post(
            "/api/auth/max",
            json={"employeeCode": "invalid", "initData": ""},
        )

        self.assertEqual(response.status_code, 422)
