from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

SOURCE_FILENAME = "tickets_synthetic_v0.1.csv"
SPLIT_VERSION = "v0.1"
SPLIT_SEED = 20260625

EXPECTED_CATEGORIES = [
    "acceso_autenticacion",
    "pagos_facturacion",
    "error_tecnico",
    "rendimiento",
    "solicitud_funcionalidad",
    "consulta_general",
]


def deterministic_family_order(category: str, families: list[str]) -> list[str]:
    return sorted(
        families,
        key=lambda family: hashlib.sha256(
            f"{SPLIT_SEED}|{category}|{family}".encode("utf-8")
        ).hexdigest(),
    )


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    source_path = project_root / "data" / "raw" / SOURCE_FILENAME
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_path.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {source_path}")

    with source_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        source_fields = reader.fieldnames or []

    required_columns = {"id", "title", "description", "category", "template_family"}
    missing_columns = sorted(required_columns - set(source_fields))
    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias: {missing_columns}")

    rows_by_category_family: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for row in rows:
        category = row["category"].strip()
        family = row["template_family"].strip()

        if category not in EXPECTED_CATEGORIES:
            raise ValueError(f"Categoría no esperada: {category}")
        if not family:
            raise ValueError(f"Fila sin template_family: {row.get('id')}")

        rows_by_category_family[category][family].append(row)

    missing_categories = [
        category
        for category in EXPECTED_CATEGORIES
        if category not in rows_by_category_family
    ]
    if missing_categories:
        raise ValueError(f"Faltan categorías: {missing_categories}")

    split_rows: dict[str, list[dict]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    family_assignments: dict[str, dict[str, list[str]]] = {}

    for category in EXPECTED_CATEGORIES:
        family_map = rows_by_category_family[category]
        families = deterministic_family_order(category, list(family_map.keys()))

        if len(families) < 3:
            raise ValueError(
                f"{category} necesita al menos 3 familias y solo tiene {len(families)}."
            )

        validation_family = families[0]
        test_family = families[1]
        train_families = families[2:]

        assignment = {
            "train": train_families,
            "validation": [validation_family],
            "test": [test_family],
        }
        family_assignments[category] = assignment

        for split_name, assigned_families in assignment.items():
            for family in assigned_families:
                for row in family_map[family]:
                    output_row = dict(row)
                    output_row["split"] = split_name
                    split_rows[split_name].append(output_row)

    for split_name in split_rows:
        split_rows[split_name].sort(key=lambda row: row["id"])

    output_fields = source_fields + ([] if "split" in source_fields else ["split"])

    train_path = output_dir / "train_v0.1.csv"
    validation_path = output_dir / "validation_v0.1.csv"
    test_path = output_dir / "test_v0.1.csv"
    manifest_path = output_dir / "split_manifest_v0.1.json"

    write_csv(train_path, split_rows["train"], output_fields)
    write_csv(validation_path, split_rows["validation"], output_fields)
    write_csv(test_path, split_rows["test"], output_fields)

    ids_by_split = {
        name: {row["id"] for row in split_data}
        for name, split_data in split_rows.items()
    }
    source_ids = {row["id"] for row in rows}

    id_overlaps = {
        "train_validation": sorted(ids_by_split["train"] & ids_by_split["validation"]),
        "train_test": sorted(ids_by_split["train"] & ids_by_split["test"]),
        "validation_test": sorted(ids_by_split["validation"] & ids_by_split["test"]),
    }

    groups_by_split = {
        name: {
            f"{row['category']}::{row['template_family']}"
            for row in split_data
        }
        for name, split_data in split_rows.items()
    }

    family_overlaps = {
        "train_validation": sorted(groups_by_split["train"] & groups_by_split["validation"]),
        "train_test": sorted(groups_by_split["train"] & groups_by_split["test"]),
        "validation_test": sorted(groups_by_split["validation"] & groups_by_split["test"]),
    }

    combined_ids = set().union(*ids_by_split.values())

    checks = {
        "all_source_rows_assigned": combined_ids == source_ids,
        "no_extra_rows": combined_ids <= source_ids,
        "no_id_overlap": all(not values for values in id_overlaps.values()),
        "no_family_overlap": all(not values for values in family_overlaps.values()),
        "all_splits_non_empty": all(split_rows.values()),
        "all_categories_in_every_split": all(
            all(
                any(row["category"] == category for row in split_rows[split_name])
                for category in EXPECTED_CATEGORIES
            )
            for split_name in split_rows
        ),
    }

    split_counts = {
        split_name: len(split_data)
        for split_name, split_data in split_rows.items()
    }
    category_counts = {
        split_name: dict(Counter(row["category"] for row in split_data))
        for split_name, split_data in split_rows.items()
    }

    manifest = {
        "split_version": SPLIT_VERSION,
        "split_seed": SPLIT_SEED,
        "source_file": str(source_path.relative_to(project_root)),
        "strategy": (
            "Separación determinista por category::template_family. "
            "Por cada categoría se asignan 6 familias a train, "
            "1 a validation y 1 a test."
        ),
        "counts": split_counts,
        "category_counts": category_counts,
        "family_assignments": family_assignments,
        "id_overlaps": id_overlaps,
        "family_overlaps": family_overlaps,
        "checks": checks,
        "all_checks_passed": all(checks.values()),
        "output_files": {
            "train": str(train_path.relative_to(project_root)),
            "validation": str(validation_path.relative_to(project_root)),
            "test": str(test_path.relative_to(project_root)),
        },
    }

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("División del dataset completada")
    print(f"Fuente: {source_path}")
    print(f"Semilla de división: {SPLIT_SEED}")
    print("Estrategia: separación por category::template_family")
    print("")

    for split_name in ["train", "validation", "test"]:
        print(f"{split_name}: {split_counts[split_name]} filas")
        for category in EXPECTED_CATEGORIES:
            count = category_counts[split_name].get(category, 0)
            print(f"  - {category}: {count}")

    print("")
    print("Comprobaciones:")
    for name, passed in checks.items():
        print(f"  - {name}: {'OK' if passed else 'FALLÓ'}")

    print("")
    print(
        "RESULTADO GENERAL: "
        + ("APROBADO" if manifest["all_checks_passed"] else "REQUIERE REVISIÓN")
    )
    print(f"Manifiesto: {manifest_path}")


if __name__ == "__main__":
    main()
