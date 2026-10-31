from typing import List, Dict, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Unified Knowledge Base: each problem contains everything needed
KNOWLEDGE_BASE = {
    "High Dimensionality": {
        "characteristic": "HD",
        "severity": 2,
        "strategies": ["QBC", "DIVERSITY", "UNC", "CLUSTER", "DENSITY"],
        "description": "QBC and Diversity strategies excel with high-dimensional data by maintaining performance across feature spaces",
    },
    "Imbalance": {
        "characteristic": "IMBALANCE",
        "severity": 2,
        "strategies": ["UNC", "DIVERSITY", "QBC", "CLUSTER"],
        "description": "UNC and Diversity strategies effectively target rare classes in imbalanced datasets",
    },
    "Missing Values": {
        "characteristic": "MISSING",
        "severity": 3,
        "strategies": ["UNC", "QBC", "DIVERSITY", "CLUSTER"],
        "description": "UNC handles missing values robustly, with QBC providing strong alternative performance",
    },
    "Outliers": {
        "characteristic": "OUTLIER",
        "severity": 4,
        "strategies": ["QBC", "UNC", "CLUSTER", "DIVERSITY"],
        "description": "QBC demonstrates superior robustness to outliers through committee consensus",
    },
    "Redundancy": {
        "characteristic": "REDUNDANCY",
        "severity": 1,
        "strategies": ["QBC", "DIVERSITY", "UNC", "CLUSTER"],
        "description": "QBC and Diversity strategies effectively mitigate feature redundancy issues",
    },
}

# Strategy performance weights (empirical)
STRATEGY_PERFORMANCE_WEIGHTS = {
    "UNC": {
        "base_weight": 0.847,
        "characteristic_weights": {
            "HD": 0.920, "IMBALANCE": 0.910, "MISSING": 0.781, "OUTLIER": 0.669, "REDUNDANCY": 0.921
        },
    },
    "QBC": {
        "base_weight": 0.894,
        "characteristic_weights": {
            "HD": 0.963, "IMBALANCE": 0.934, "MISSING": 0.758, "OUTLIER": 0.873, "REDUNDANCY": 0.953
        },
    },
    "DIVERSITY": {
        "base_weight": 0.864,
        "characteristic_weights": {
            "HD": 0.960, "IMBALANCE": 0.913, "MISSING": 0.721, "OUTLIER": 0.583, "REDUNDANCY": 0.953
        },
    },
    "DENSITY": {
        "base_weight": 0.623,
        "characteristic_weights": {
            "HD": 0.697, "IMBALANCE": 0.723, "MISSING": 0.583, "OUTLIER": 0.413, "REDUNDANCY": 0.714
        },
    },
    "CLUSTER": {
        "base_weight": 0.683,
        "characteristic_weights": {
            "HD": 0.773, "IMBALANCE": 0.753, "MISSING": 0.634, "OUTLIER": 0.534, "REDUNDANCY": 0.793
        },
    },
}


def calculate_strategy_score(strategy: str, problem: str) -> float:
    """Calculate weighted score for a strategy given a problem."""
    if problem not in KNOWLEDGE_BASE:
        return 0.0

    characteristic = KNOWLEDGE_BASE[problem]["characteristic"]
    strategy_data = STRATEGY_PERFORMANCE_WEIGHTS.get(strategy, {})

    char_weight = strategy_data.get("characteristic_weights", {}).get(characteristic, 0)
    base_weight = strategy_data.get("base_weight", 0)

    # Weighted: 75% characteristic, 25% base
    return 0.75 * char_weight + 0.25 * base_weight


def recommend_strategy(problems: List[str]) -> Optional[Dict]:
    """
    Recommend active learning strategies based on dataset problems.
    - Considers severity of each problem
    - Uses empirical weights
    - Returns ranked strategies with explanations
    """
    if not problems:
        logger.warning("No problems provided for recommendation")
        return None

    valid_problems = [p for p in problems if p in KNOWLEDGE_BASE]
    unknown_problems = set(problems) - set(valid_problems)

    if unknown_problems:
        logger.warning(f"Ignoring unknown problems: {unknown_problems}")

    if not valid_problems:
        logger.error("No valid problems provided")
        return None

    try:
        # Aggregate strategy scores
        strategy_scores = defaultdict(float)
        strategy_reasons = defaultdict(list)

        for problem in valid_problems:
            severity = KNOWLEDGE_BASE[problem]["severity"]
            for strategy in KNOWLEDGE_BASE[problem]["strategies"]:
                score = calculate_strategy_score(strategy, problem) * severity
                strategy_scores[strategy] += score
                strategy_reasons[strategy].append(problem)

        if not strategy_scores:
            logger.error("No strategies scored")
            return None

        # Normalize
        max_score = max(strategy_scores.values())
        normalized_scores = {s: score / max_score for s, score in strategy_scores.items()}

        # Rank strategies
        ranked_strategies = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)

        recommendations = []
        for strat, score in ranked_strategies:
            recommendations.append({
                "strategy": strat,
                "score": round(score, 3),
                "reasons": strategy_reasons[strat],
            })

        # Best explanation
        top_strategy = recommendations[0]["strategy"]
        top_score = recommendations[0]["score"]
        primary_problem = max(valid_problems, key=lambda x: KNOWLEDGE_BASE[x]["severity"])
        explanation = (
            f"Recommended '{top_strategy}' (confidence: {top_score:.2f}) due to severity of '{primary_problem}'. "
            f"{KNOWLEDGE_BASE[primary_problem]['description']}"
        )

        return {
            "recommendation": recommendations[0],
            "alternatives": recommendations[1:4],
            "all_ranked": recommendations,
            "problem_analysis": {p: KNOWLEDGE_BASE[p] for p in valid_problems},
            "explanation": explanation,
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Recommendation failed: {str(e)}", exc_info=True)
        return {"status": "error", "message": f"Error: {str(e)}"}


def get_strategy_performance_data() -> Dict:
    """Return the full knowledge base and weights for analysis."""
    return {
        "knowledge_base": KNOWLEDGE_BASE,
        "weights": STRATEGY_PERFORMANCE_WEIGHTS,
    }
