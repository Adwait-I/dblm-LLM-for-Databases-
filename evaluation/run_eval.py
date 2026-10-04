"""
evaluation/run_eval.py
----------------------
Benchmark evaluation runner for QueryMind Text-to-SQL.
Tests a suite of natural-language questions of varying complexity.
"""

import time
import httpx

EVAL_SUITE = [
    {
        "id": "Q1_SIMPLE_COUNT",
        "question": "How many total employees are there?",
        "expected_table": "employees",
    },
    {
        "id": "Q2_AGGREGATION_GROUP",
        "question": "How many employees are in each department?",
        "expected_table": "departments",
    },
    {
        "id": "Q3_JOIN_FILTER",
        "question": "Show all employees who work in the IT department.",
        "expected_table": "employees",
    },
    {
        "id": "Q4_ORDER_LIMIT",
        "question": "List the top 5 highest paid employees with their salaries.",
        "expected_table": "employees",
    },
    {
        "id": "Q5_MULTI_JOIN",
        "question": "Which departments are located in the Americas region?",
        "expected_table": "regions",
    },
    {
        "id": "Q6_DEPENDENTS_JOIN",
        "question": "List all employees who have children as dependents.",
        "expected_table": "dependents",
    },
]


def run_evaluation(api_base: str = "http://localhost:8000/api"):
    print(f"--- Running QueryMind Benchmark Suite ({len(EVAL_SUITE)} questions) ---")
    results = []

    with httpx.Client(base_url=api_base, timeout=120.0) as client:
        for item in EVAL_SUITE:
            print(f"\nEvaluating [{item['id']}]: '{item['question']}'")
            start = time.time()
            try:
                res = client.post("/query", json={"question": item["question"]})
                data = res.json()
                elapsed = round((time.time() - start) * 1000, 2)

                if res.status_code == 200 and not data.get("error"):
                    print(f"  Status: SUCCESS ({elapsed}ms, attempts: {data.get('attempts', 1)})")
                    print(f"  SQL: {data.get('sql')}")
                    print(f"  Rows returned: {data.get('row_count')}")
                    results.append({"id": item["id"], "success": True, "time_ms": elapsed})
                else:
                    print(f"  Status: FAILED - {data.get('error', res.text)}")
                    results.append({"id": item["id"], "success": False, "error": data.get("error")})
            except Exception as e:
                print(f"  Status: ERROR - {e}")
                results.append({"id": item["id"], "success": False, "error": str(e)})

    total = len(results)
    passed = sum(1 for r in results if r["success"])
    print("\n" + "=" * 50)
    print(f"Summary: {passed}/{total} Passed ({(passed/total)*100:.1f}%)")
    print("=" * 50)


if __name__ == "__main__":
    run_evaluation()
