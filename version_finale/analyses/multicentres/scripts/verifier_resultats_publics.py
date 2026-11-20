"""Vérifier la cohérence des résultats multicentres agrégés publiables."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "resultats" / "multicentres"


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def close(actual: float, expected: float, tolerance: float = 1e-9) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{actual} != {expected}")


def main() -> None:
    choice = json.loads((ROOT / "choix_final.json").read_text(encoding="utf-8"))
    if choice["methode"] != "original":
        raise AssertionError("La méthode finale doit être sélectionnée sur la validation.")

    validation = [row for row in rows("metriques_validation_par_centre.csv") if row["methode"] == "original"]
    if {int(row["centre"]) for row in validation} != {0, 4}:
        raise AssertionError("Les deux centres de validation attendus sont absents.")
    mean_specificity = sum(float(row["specificite"]) for row in validation) / len(validation)
    mean_auc = sum(float(row["auc"]) for row in validation) / len(validation)
    close(mean_specificity, float(choice["specificite_moyenne"]))
    close(mean_auc, float(choice["auc_moyenne"]))

    test = rows("metriques_test.csv")
    if len(test) != 1 or test[0]["methode"] != choice["methode"]:
        raise AssertionError("Le test doit contenir uniquement la méthode figée.")
    close(float(test[0]["seuil"]), float(choice["seuil"]), tolerance=1e-8)
    if int(test[0]["centre"]) != 2 or int(test[0]["n"]) != 864:
        raise AssertionError("La cohorte de test agrégée ne correspond pas au protocole publié.")

    print("OK — choix sur validation et métriques de test agrégées cohérents")


if __name__ == "__main__":
    main()
