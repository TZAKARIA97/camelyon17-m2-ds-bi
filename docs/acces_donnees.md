# Accéder aux données du projet

Le jeu étudié reste **CAMELYON17**. Le groupe retient sa version **CAMELYON17-WILDS 1.0** pour apprendre à classer des patchs, et une lame originale avec son XML pour comprendre la visualisation et les annotations. Ce sont deux représentations du même projet, avec des unités et des labels différents.

## 1. Récupérer seulement un pilote WILDS

Après l'installation décrite dans le README, depuis la racine du dépôt :

```bash
python -m src.data.acquire_wilds --out data/wilds/pilot_download
python -m src.data.audit data/wilds/pilot_download/pilot.csv --check-files
python -m src.data.explore --manifest data/wilds/pilot_download/pilot.csv --out outputs/exploration_real
```

Le téléchargement standard de WILDS repose sur un ancien lien CodaLab qui a répondu **HTTP 404 lors de notre essai du 6 novembre 2026**. Le script utilise donc le miroir communautaire [fumiyau/wilds-archive](https://huggingface.co/datasets/fumiyau/wilds-archive), à la révision figée `f7b0ea1de482b7dcccfd9a15af2825a4e70b335d`. Ce n'est pas un miroir officiel ; l'identité binaire avec l'archive CodaLab indisponible n'a pas été démontrée. La source et cette limite doivent apparaître dans le rapport.

Le script lit les index des six ZIP par plages HTTP, extrait `metadata.csv`, sélectionne les lignes, puis récupère uniquement les PNG correspondants. Il **ne télécharge pas les six ZIP complets**. Il refuse une réponse HTTP complète, une plage incorrecte, un fichier trop grand ou un dépassement du budget de transfert. La connexion doit autoriser les requêtes HTTP Range et les redirections de Hugging Face.

Paramètres par défaut : graine 42, au plus 10 groupes patient par couple ensemble/centre et 16 patchs par groupe. Ici, le plafond de 10 inclut les 43 groupes disponibles dans train/val/test, soit **688 patchs**. Le tirage des patchs n'utilise pas leurs labels. Cela donne un essai de fonctionnement, pas un échantillon représentatif de la population clinique ni le benchmark complet. Le poids identique attribué aux groupes modifie notamment la prévalence.

Fichiers créés :

| Fichier | Rôle |
| --- | --- |
| `camelyon17_v1.0/metadata.csv` | Métadonnées originales conservées sans modification |
| `all_patches.csv` | 422 394 lignes retenues après exclusion documentée de `id_val` ; toutes les images ne sont pas téléchargées |
| `pilot.csv` | Les seules images du pilote, avec leur split, label et chemin local |
| `camelyon17_v1.0/patches/` | PNG sélectionnés, contrôlés en RGB 96 × 96 et par CRC ZIP |
| `acquisition.json` | Source figée, paramètres, volumes transférés et empreintes SHA-256 des métadonnées et images |

Le script refuse un dossier déjà existant. En cas d'échec, garder le diagnostic et choisir un nouveau dossier pour réessayer ; aucune reprise automatique n'est implémentée. Les chemins du manifeste sont locaux : régénérer le manifeste après déplacement. Les empreintes du manifeste peuvent différer entre deux machines à cause de ces chemins ; les chemins relatifs et empreintes des PNG dans `acquisition.json` permettent de comparer le contenu.

## 2. Comprendre la séparation retenue

L'audit du CSV réel a trouvé **26 groupes patient et 30 lames partagés entre `train` et `id_val`**. La validation interne de WILDS est définie au niveau patch. Notre protocole exige une séparation des groupes, donc nous excluons ses 33 560 patchs `id_val`. Nous ne déplaçons aucun patch entre les autres ensembles et ne modifions pas les métadonnées originales.

| Ensemble conservé | Centres WILDS | Métadonnées complètes | Usage |
| --- | --- | ---: | --- |
| `train` | 0, 3, 4 | 302 436 | Apprentissage |
| `val` | 1 | 34 904 | Choix du checkpoint et comparaison des méthodes |
| `test` | 2 | 85 054 | Évaluation finale après gel du protocole |

Il n'y a donc **pas de comparaison ID/OOD** dans ce protocole. Nous conservons les ensembles OOD du schéma officiel, mais nous ne reproduisons pas l'ensemble du protocole WILDS. Les identifiants patient CAMELYON17 désignent des groupes artificiels : leur séparation ne garantit pas l'indépendance biologique de toutes les lames.

Pour un WILDS complet déjà présent sur disque, sans passer par le miroir :

```bash
python -m src.data.wilds_manifest --root data/wilds/camelyon17_v1.0 --split-policy exclude-id-val --out data/manifests/wilds_patches.csv
```

Sans `--split-policy exclude-id-val`, le convertisseur reste strict et signale le chevauchement. Ce contrôle n'est pas désactivé.

## 3. Télécharger une seule lame avec ses annotations

```bash
python -m pip install -r requirements-wsi-tested.txt
python -m src.data.acquire_wsi_example
python -m src.data.inspect_wsi --wsi data/raw/wsi_example/patient_089_node_3.tif --xml data/raw/wsi_example/patient_089_node_3.xml --coords examples/coords_patient_089_node_3.csv --size 384 --level 2 --out outputs/inspection_real
```

Le script récupère `patient_089_node_3.tif` et son XML depuis le [stockage public CAMELYON sur AWS](https://registry.opendata.aws/camelyon/), ainsi que les sommes de contrôle de la distribution. La lame mesure **518 910 648 octets**, environ 519 Mo ; prévoir au moins 1,04 Go libre. Les deux fichiers doivent correspondre aux MD5 publiés avant d'être utilisés. Leur SHA-256 est aussi enregistré.

La lame mesure 152 064 × 66 048 pixels au niveau 0, avec 0,25 µm/pixel selon ses métadonnées. Les trois coordonnées fournies sont les centres des boîtes englobantes des annotations 0, 1 et 3, arrondis, moins 768 pixels sur chaque axe. Le niveau 2 réduit d'un facteur 4 : une image de 384 × 384 couvre donc 1 536 × 1 536 pixels du niveau 0. Ces coordonnées sont propres à cette lame.

L'inspection produit une miniature, une miniature annotée, les trois régions, leurs masques et leurs superpositions rouges. La proportion colorée mesure la surface couverte par les polygones dans la région extraite. Elle n'est ni le label central WILDS ni une mesure validée de la taille d'une métastase. Les régions ont été choisies autour d'annotations positives ; elles ne constituent pas un test équilibré.

Pour la collègue chargée de la visualisation, ouvrir le TIFF puis le XML portant le même nom dans ASAP, ou examiner les exports OpenSlide. Le lecteur Python reconnaît le groupe `Tumor` réellement présent dans ce XML. L'installation ASAP et son éventuel conflit NumPy sur son poste restent à vérifier séparément.

## 4. Passer à l'apprentissage

```bash
python -m src.models.train --manifest data/wilds/pilot_download/pilot.csv --config configs/baseline.json --out outputs/baseline_real
python -m src.models.train --manifest data/wilds/pilot_download/pilot.csv --config configs/fine_tune.json --out outputs/finetune_real
python -m src.evaluation.evaluate --manifest data/wilds/pilot_download/pilot.csv --checkpoint outputs/baseline_real/best.pt --split val --out outputs/baseline_real_val
python -m src.evaluation.evaluate --manifest data/wilds/pilot_download/pilot.csv --checkpoint outputs/finetune_real/best.pt --split val --out outputs/finetune_real_val
```

Le premier entraînement télécharge environ 45 Mo de poids ImageNet s'ils sont absents du cache. Comparer les AP de validation ; en cas d'égalité, garder la référence gelée. Une amélioration sur ce petit pilote ne suffit pas à retenir définitivement une méthode. **Ne pas lancer le test final pendant les ajustements du pilote.** Poursuivre avec le [guide d'exécution](02_demarrage.md) pour les figures, Grad-CAM, puis le protocole final.

Sur un CPU disposant de nombreux cœurs, limiter les threads peut éviter un surcoût sur ces petites images : `OMP_NUM_THREADS=2 MKL_NUM_THREADS=2` sous Linux/macOS, ou les variables d'environnement équivalentes sous PowerShell. Le poste Windows et le GPU du groupe n'ont pas été vérifiés ici.
