from functools import lru_cache
from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from deepeval import evaluate
from deepeval.dataset import EvaluationDataset
from deepeval.evaluate.configs import AsyncConfig, ErrorConfig
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric,
)
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase

from src.query.pipeline import run_rag_pipeline
from src.query.retriever import close_retriever_client


DEFAULT_GOLDEN_DATASET_PATH = (
    PROJECT_ROOT / "data" / "evaluation" / "goldenDatasets" / "cis_controls_v8_golden_dataset.json"
)
DEFAULT_PIPELINE_CACHE_PATH = (
    PROJECT_ROOT / ".deepeval" / "cached_pipeline_outputs.json"
)
DEFAULT_EVAL_LOG_PATH = (
    PROJECT_ROOT / ".deepeval" / "evaluation_run.log"
)
DEFAULT_EVAL_RESULTS_PATH = (
    PROJECT_ROOT / ".deepeval" / "evaluation_results.json"
)
DEFAULT_JUDGE_MODEL = "llama3.2:3b"
DEFAULT_JUDGE_GENERATION_KWARGS = {
    "num_predict": 1024,
}


def load_golden_dataset(dataset_path=DEFAULT_GOLDEN_DATASET_PATH):
    with open(dataset_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_cached_pipeline_outputs(cache_path=DEFAULT_PIPELINE_CACHE_PATH):
    if not cache_path.exists():
        return {}

    with open(cache_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_cached_pipeline_outputs(cache_data, cache_path=DEFAULT_PIPELINE_CACHE_PATH):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as file:
        json.dump(cache_data, file, ensure_ascii=False, indent=2)


def save_eval_results(results, results_path=DEFAULT_EVAL_RESULTS_PATH):
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as file:
        json.dump(results.__dict__, file, ensure_ascii=False, indent=2, default=str)


@lru_cache(maxsize=1)
def build_judge_model(model_name=DEFAULT_JUDGE_MODEL):
    return OllamaModel(
        model=model_name,
        temperature=0,
        generation_kwargs=DEFAULT_JUDGE_GENERATION_KWARGS,
    )


def build_test_case(question, index_name="RAGDocs", top_k=5, cache=None, refresh_cache=False):
    cache_key = question["input"]
    cached_item = None if refresh_cache else (cache or {}).get(cache_key)

    if cached_item is None:
        pipeline_result, _ = run_rag_pipeline(question["input"], index_name=index_name, top_k=top_k)
        cached_item = {
            "input": question["input"],
            "actual_output": pipeline_result["answer"],
            "expected_output": question["expected_output"],
            "retrieval_context": pipeline_result["retrieval_context"],
        }
        return LLMTestCase(**cached_item), cached_item

    return (
        LLMTestCase(
            input=cached_item["input"],
            actual_output=cached_item["actual_output"],
            expected_output=cached_item["expected_output"],
            retrieval_context=cached_item["retrieval_context"],
        ),
        cached_item,
    )


def build_test_cases(golden_dataset, index_name="RAGDocs", top_k=5, refresh_cache=False, limit=10):
    cached_outputs = load_cached_pipeline_outputs()
    test_cases = []

    for question in golden_dataset.get("questions", [])[:limit]:
        test_case, cached_item = build_test_case(
            question,
            index_name=index_name,
            top_k=top_k,
            cache=cached_outputs,
            refresh_cache=refresh_cache,
        )
        test_cases.append(test_case)
        cached_outputs[question["input"]] = cached_item

    save_cached_pipeline_outputs(cached_outputs)
    return test_cases


def run_evaluation(dataset_path=DEFAULT_GOLDEN_DATASET_PATH, index_name="RAGDocs", top_k=5, refresh_cache=False, limit=10):
    golden_dataset = load_golden_dataset(dataset_path)
    test_cases = build_test_cases(
        golden_dataset,
        index_name=index_name,
        top_k=top_k,
        refresh_cache=refresh_cache,
        limit=limit,
    )
    judge_model = build_judge_model()

    metrics = [
        FaithfulnessMetric(threshold=0.7, model=judge_model),
        AnswerRelevancyMetric(threshold=0.7, model=judge_model),
        ContextualPrecisionMetric(threshold=0.6, model=judge_model),
        ContextualRecallMetric(threshold=0.6, model=judge_model),
    ]

    dataset = EvaluationDataset()
    dataset.test_cases = test_cases

    return evaluate(
        test_cases,
        metrics,
        async_config=AsyncConfig(run_async=True, throttle_value=0, max_concurrent=1),
        error_config=ErrorConfig(ignore_errors=True, skip_on_missing_params=False),
    )


def main():
    DEFAULT_EVAL_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        results = run_evaluation(limit=10)
        save_eval_results(results)
        print(f"Evaluation completed. Full log saved to: {DEFAULT_EVAL_LOG_PATH}")
        print(f"Structured results saved to: {DEFAULT_EVAL_RESULTS_PATH}")
    finally:
        print("Closing retriever client...")
        close_retriever_client()


if __name__ == "__main__":
    main()
