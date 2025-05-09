import unittest
from utils.real_data_provider import RealDataProvider

class TestRealDataProvider(unittest.TestCase):
    def setUp(self):
        self.provider = RealDataProvider()

    def test_prepare_sql_query(self):
        query = "SELECT Nettokertymä, Lisätalousarvio FROM budget_transactions"
        expected_query = "SELECT `Nettokertymä`, `Lisätalousarvio` FROM budget_transactions"
        prepared_query = self.provider._prepare_sql_query(query)
        self.assertEqual(prepared_query, expected_query)

if __name__ == "__main__":
    unittest.main()