from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from statistics import mean, median


EXPECTED_CATEGORIES = [
    "acceso_autenticacion",
    "pagos_facturacion",
    "error_tecnico",
    "rendimiento",
    "solicitud_funcionalidad",
    "consulta_general",
]

EXPECTED_TOTAL = 900
EXPECTED_PER_CATEGORY = 150
SIMILARITY_THRESHOLD = 0.88
MAX_SUSPICIOUS_PAIRS = 200


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def combined_text(row: dict) -> str:
    return normalize(f"{row.get('title', '')} {row.get('description', '')}")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    dataset_path = project_root / "data" / "raw" / "tickets_synthetic_v0.1.csv"
    reports_dir = project_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / "dataset_validation_v0.1.json"
    pairs_path = reports_dir / "near_duplicate_pairs_v0.1.csv"

    if not dataset_path.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {dataset_path}")

    with dataset_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    required_columns = [
        "id",
        "title",
        "description",
        "category",
        "source",
        "synthetic",
    ]
    recommended_columns = [
        "template_family",
        "generator_version",
    ]

    missing_required = [column for column in required_columns if column not in fieldnames]
    missing_recommended = [column for column in recommended_columns if column not in fieldnames]

    empty_by_column = {
        column: sum(not str(row.get(column, "")).strip() for row in rows)
        for column in required_columns
        if column in fieldnames
    }

    ids = [str(row.get("id", "")).strip() for row in rows]
    duplicate_ids = sorted(
        value for value, count in Counter(ids).items() if value and count > 1
    )

    exact_keys = [combined_text(row) for row in rows]
    exact_duplicate_counts = {
        value: count
        for value, count in Counter(exact_keys).items()
        if value and count > 1
    }

    category_counts = Counter(row.get("category", "").strip() for row in rows)
    unexpected_categories = sorted(
        category for category in category_counts if category not in EXPECTED_CATEGORIES
    )

    family_counts = Counter()
    if "template_family" in fieldnames:
        family_counts = Counter(
            f"{row.get('category', '').strip()}::{row.get('template_family', '').strip()}"
            for row in rows
        )

    title_lengths = [len(str(row.get("title", "")).split()) for row in rows]
    description_lengths = [len(str(row.get("description", "")).split()) for row in rows]
    combined_lengths = [len(combined_text(row).split()) for row in rows]

    duplicate_titles = {
        value: count
        for value, count in Counter(normalize(row.get("title", "")) for row in rows).items()
        if value and count > 1
    }

    duplicate_descriptions = {
        value: count
        for value, count in Counter(
            normalize(row.get("description", "")) for row in rows
        ).items()
        if value and count > 1
    }

    rows_by_category: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        rows_by_category[row.get("category", "").strip()].append(row)

    suspicious_pairs = []

    for category, category_rows in rows_by_category.items():
        if category not in EXPECTED_CATEGORIES:
            continue

        for index, left in enumerate(category_rows):
            left_text = combined_text(left)

            for right in category_rows[index + 1 :]:
                right_text = combined_text(right)

                if left_text == right_text:
                    continue

                similarity = SequenceMatcher(None, left_text, right_text).ratio()

                if similarity >= SIMILARITY_THRESHOLD:
                    suspicious_pairs.append(
                        {
                            "category": category,
                            "similarity": round(similarity, 4),
                            "id_1": left.get("id", ""),
                            "family_1": left.get("template_family", ""),
                            "title_1": left.get("title", ""),
                            "description_1": left.get("description", ""),
                            "id_2": right.get("id", ""),
                            "family_2": right.get("template_family", ""),
                            "title_2": right.get("title", ""),
                            "description_2": right.get("description", ""),
                        }
                    )

    suspicious_pairs.sort(key=lambda item: item["similarity"], reverse=True)
    suspicious_pairs = suspicious_pairs[:MAX_SUSPICIOUS_PAIRS]

    checks = {
        "total_is_expected": len(rows) == EXPECTED_TOTAL,
        "required_columns_present": not missing_required,
        "no_empty_required_fields": all(value == 0 for value in empty_by_column.values()),
        "no_duplicate_ids": not duplicate_ids,
        "no_exact_duplicate_tickets": not exact_duplicate_counts,
        "only_expected_categories": not unexpected_categories,
        "balanced_categories": all(
            category_counts.get(category, 0) == EXPECTED_PER_CATEGORY
            for category in EXPECTED_CATEGORIES
        ),
        "all_marked_synthetic": all(
            normalize(row.get("synthetic", "")) == "true" for row in rows
        ),
    }

    report = {
        "dataset": str(dataset_path.relative_to(project_root)),
        "total_rows": len(rows),
        "columns": fieldnames,
        "missing_required_columns": missing_required,
        "missing_recommended_columns": missing_recommended,
        "empty_by_column": empty_by_column,
        "duplicate_ids": duplicate_ids,
        "exact_duplicate_ticket_groups": len(exact_duplicate_counts),
        "duplicate_title_groups": len(duplicate_titles),
        "duplicate_description_groups": len(duplicate_descriptions),
        "category_counts": dict(category_counts),
        "unexpected_categories": unexpected_categories,
        "family_counts": dict(sorted(family_counts.items())),
        "length_statistics_words": {
            "title": {
                "min": min(title_lengths) if title_lengths else 0,
                "mean": round(mean(title_lengths), 2) if title_lengths else 0,
                "median": median(title_lengths) if title_lengths else 0,
                "max": max(title_lengths) if title_lengths else 0,
            },
            "description": {
                "min": min(description_lengths) if description_lengths else 0,
                "mean": round(mean(description_lengths), 2) if description_lengths else 0,
                "median": median(description_lengths) if description_lengths else 0,
                "max": max(description_lengths) if description_lengths else 0,
            },
            "combined": {
                "min": min(combined_lengths) if combined_lengths else 0,
                "mean": round(mean(combined_lengths), 2) if combined_lengths else 0,
                "median": median(combined_lengths) if combined_lengths else 0,
                "max": max(combined_lengths) if combined_lengths else 0,
            },
        },
        "near_duplicate_threshold": SIMILARITY_THRESHOLD,
        "near_duplicate_pairs_found": len(suspicious_pairs),
        "checks": checks,
        "all_critical_checks_passed": all(checks.values()),
    }

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    pair_fieldnames = [
        "category",
        "similarity",
        "id_1",
        "family_1",
        "title_1",
        "description_1",
        "id_2",
        "family_2",
        "title_2",
        "description_2",
    ]

    with pairs_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=pair_fieldnames)
        writer.writeheader()
        writer.writerows(suspicious_pairs)

    print("Validación del dataset completada")
    print(f"Dataset: {dataset_path}")
    print(f"Reporte: {report_path}")
    print(f"Pares similares: {pairs_path}")
    print(f"Total de filas: {len(rows)}")
    print(f"Duplicados exactos: {len(exact_duplicate_counts)}")
    print(f"Pares casi duplicados >= {SIMILARITY_THRESHOLD}: {len(suspicious_pairs)}")
    print("")
    print("Distribución por categoría:")
    for category in EXPECTED_CATEGORIES:
        print(f"  - {category}: {category_counts.get(category, 0)}")
    print("")
    print("Comprobaciones críticas:")
    for name, passed in checks.items():
        print(f"  - {name}: {'OK' if passed else 'FALLÓ'}")
    print("")
    print(
        "RESULTADO GENERAL: "
        + ("APROBADO" if report["all_critical_checks_passed"] else "REQUIERE REVISIÓN")
    )


if __name__ == "__main__":
    main()
