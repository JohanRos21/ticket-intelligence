from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


EXPECTED_CATEGORIES = [
    "acceso_autenticacion",
    "pagos_facturacion",
    "error_tecnico",
    "rendimiento",
    "solicitud_funcionalidad",
    "consulta_general",
]

STOPWORDS_ES = {
    "a", "al", "algo", "ante", "antes", "aunque", "cada", "como", "con", "contra",
    "cuando", "de", "del", "desde", "despues", "después", "donde", "dos", "el",
    "ella", "ellos", "en", "entre", "era", "es", "esa", "ese", "eso", "esta",
    "está", "estan", "están", "este", "esto", "fue", "ha", "hace", "hay", "la",
    "las", "le", "les", "lo", "los", "mas", "más", "me", "mi", "mis", "no",
    "nos", "o", "para", "pero", "por", "porque", "que", "qué", "se", "si",
    "sí", "sin", "sobre", "solo", "su", "sus", "tambien", "también", "te",
    "tengo", "un", "una", "uno", "varios", "y", "ya",
}


def normalize_text(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-záéíóúñü]+", normalize_text(text))

    return [
        token
        for token in tokens
        if len(token) >= 3 and token not in STOPWORDS_ES
    ]


def length_stats(series: pd.Series) -> dict:
    values = series.astype(str).str.split().str.len()

    return {
        "min": int(values.min()),
        "mean": round(float(values.mean()), 2),
        "median": round(float(values.median()), 2),
        "max": int(values.max()),
    }


def count_by_category(df: pd.DataFrame) -> dict:
    counts = df["category"].value_counts().reindex(
        EXPECTED_CATEGORIES,
        fill_value=0,
    )

    return {
        category: int(count)
        for category, count in counts.items()
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    train_path = project_root / "data" / "processed" / "train_v0.1.csv"
    validation_path = project_root / "data" / "processed" / "validation_v0.1.csv"

    reports_dir = project_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not train_path.exists():
        raise FileNotFoundError(f"No se encontró train: {train_path}")

    if not validation_path.exists():
        raise FileNotFoundError(f"No se encontró validation: {validation_path}")

    # Regla del proyecto:
    # Este análisis NO lee test_v0.1.csv.
    train = pd.read_csv(train_path, encoding="utf-8-sig")
    validation = pd.read_csv(validation_path, encoding="utf-8-sig")

    train["text"] = (
        train["title"].fillna("") + " " + train["description"].fillna("")
    )

    validation["text"] = (
        validation["title"].fillna("") + " " + validation["description"].fillna("")
    )

    train["normalized_text"] = train["text"].map(normalize_text)
    validation["normalized_text"] = validation["text"].map(normalize_text)

    train_texts = set(train["normalized_text"])
    validation_texts = set(validation["normalized_text"])
    exact_text_overlap = sorted(train_texts & validation_texts)

    train_families = set(
        train["category"] + "::" + train["template_family"]
    )

    validation_families = set(
        validation["category"] + "::" + validation["template_family"]
    )

    family_overlap = sorted(train_families & validation_families)

    top_tokens_rows = []
    top_tokens_by_category = {}

    for category in EXPECTED_CATEGORIES:
        category_text = " ".join(
            train.loc[train["category"] == category, "text"]
        )

        counts = Counter(tokenize(category_text))
        top_tokens = counts.most_common(15)

        top_tokens_by_category[category] = [
            {
                "token": token,
                "count": int(count),
            }
            for token, count in top_tokens
        ]

        for token, count in top_tokens:
            top_tokens_rows.append(
                {
                    "category": category,
                    "token": token,
                    "count": int(count),
                }
            )

    train_category_counts = count_by_category(train)
    validation_category_counts = count_by_category(validation)

    report = {
        "task": "EDA train/validation v0.1",
        "note": (
            "Este reporte usa solo train_v0.1.csv y validation_v0.1.csv. "
            "No lee test_v0.1.csv."
        ),
        "input_files": {
            "train": str(train_path.relative_to(project_root)),
            "validation": str(validation_path.relative_to(project_root)),
        },
        "row_counts": {
            "train": int(len(train)),
            "validation": int(len(validation)),
            "combined_without_test": int(len(train) + len(validation)),
        },
        "category_counts": {
            "train": train_category_counts,
            "validation": validation_category_counts,
        },
        "template_family_counts": {
            "train": int(
                (train["category"] + "::" + train["template_family"]).nunique()
            ),
            "validation": int(
                (
                    validation["category"]
                    + "::"
                    + validation["template_family"]
                ).nunique()
            ),
        },
        "length_stats_words": {
            "train": {
                "title": length_stats(train["title"]),
                "description": length_stats(train["description"]),
                "combined_text": length_stats(train["text"]),
            },
            "validation": {
                "title": length_stats(validation["title"]),
                "description": length_stats(validation["description"]),
                "combined_text": length_stats(validation["text"]),
            },
        },
        "overlap_checks": {
            "exact_text_overlap_train_validation_count": len(exact_text_overlap),
            "family_overlap_train_validation_count": len(family_overlap),
            "exact_text_overlap_train_validation_examples": exact_text_overlap[:10],
            "family_overlap_train_validation_examples": family_overlap[:10],
        },
        "top_tokens_train_by_category": top_tokens_by_category,
        "checks": {
            "train_has_all_expected_categories": all(
                train_category_counts[category] > 0
                for category in EXPECTED_CATEGORIES
            ),
            "validation_has_all_expected_categories": all(
                validation_category_counts[category] > 0
                for category in EXPECTED_CATEGORIES
            ),
            "no_exact_text_overlap_train_validation": len(exact_text_overlap) == 0,
            "no_family_overlap_train_validation": len(family_overlap) == 0,
        },
    }

    report["all_checks_passed"] = all(report["checks"].values())

    report_path = reports_dir / "eda_train_validation_v0.1.json"
    tokens_path = reports_dir / "eda_top_tokens_train_v0.1.csv"

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    pd.DataFrame(top_tokens_rows).to_csv(
        tokens_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("EDA train/validation completado")
    print("IMPORTANTE: no se leyó test_v0.1.csv")
    print(f"Reporte: {report_path}")
    print(f"Tokens frecuentes: {tokens_path}")
    print("")

    print("Filas:")
    print(f"  - train: {len(train)}")
    print(f"  - validation: {len(validation)}")
    print("")

    print("Distribución train:")
    for category, count in train_category_counts.items():
        print(f"  - {category}: {count}")
    print("")

    print("Distribución validation:")
    for category, count in validation_category_counts.items():
        print(f"  - {category}: {count}")
    print("")

    print("Longitud promedio en palabras:")
    print(
        "  - train texto combinado: "
        f"{report['length_stats_words']['train']['combined_text']['mean']}"
    )
    print(
        "  - validation texto combinado: "
        f"{report['length_stats_words']['validation']['combined_text']['mean']}"
    )
    print("")

    print("Solapamientos:")
    print(
        "  - textos exactos train/validation: "
        f"{report['overlap_checks']['exact_text_overlap_train_validation_count']}"
    )
    print(
        "  - familias train/validation: "
        f"{report['overlap_checks']['family_overlap_train_validation_count']}"
    )
    print("")

    print("Comprobaciones:")
    for name, passed in report["checks"].items():
        print(f"  - {name}: {'OK' if passed else 'FALLÓ'}")
    print("")

    print(
        "RESULTADO GENERAL: "
        + ("APROBADO" if report["all_checks_passed"] else "REQUIERE REVISIÓN")
    )


if __name__ == "__main__":
    main()