# MODIF JOELLE : NOUVEAU FICHIER POUR PARAMETRER LE DECOUPAGE ET TESTER DES VARIANTES
# 
# Fichier de paramétrage du découpage et de définition des variantes à tester + celle à retenir.
#
# Tous les réglages du découpage au même endroit :
#   1. PARAMETRES : la valeur utilisée par défaut pour chaque option, et les choix possibles en commentaire ;
#   2. VARIANTES : les découpages à comparer, chacun avec un nom et seulement ce qui change par rapport à PARAMETRES.
#
# Utilisation (depuis le dossier version_finale) :
#     python extract_patches.py --variante base               (un découpage)
#     python extract_patches.py --variante base centre        (plusieurs, l'un après l'autre)
#     python extract_patches.py --variante toutes             (toutes les variantes ci-dessous)
# Chaque variante écrit dans son propre dossier : patches/<nom de la variante>/niveau_<n>/
# Une option écrite dans la commande (par exemple --max-slides 2) l'emporte sur ce fichier.
#
# Quand les tests sont faits, on note le choix retenu dans la variante "retenue" en bas du fichier.

PARAMETRES = {
    # Lames à découper
    "selection": "data/CAMELYON17/selection_lames.csv", # la sélection faite dans le notebook 01_preparation_donnees (None = toutes les lames de --slides)
    "sets": ["entrainement", "validation"], # sets de la sélection à découper (le test n'est pas découpé en patchs)
    "slides": "labelled", # sans sélection : "annotated" (50 lames annotées) | "labelled" (+ négatives) | "all"

    # Surface et niveau des patchs
    "patch_um": 112, # côté d'un patch en µm, quel que soit le niveau (None = ancienne façon : "patch" pixels au niveau)
    "patch_level": [1], # niveau de lecture
    "patch": 224, # côté du patch enregistré en pixels (taille d'entrée de ResNet18)

    # Détection du tissu
    "violet_s_min": 15, # Saturation minimale sur 255. Choisi avec le notebook 01_preparation_donnees (partie 4)
    "level": 5, # niveau de la miniature utilisée pour repérer le tissu
    "min_tissue": 0.5, # part minimale de tissu dans un patch (camarade ; prototype : 0.25).

    # Étiquetage
    "labelling": "pourcentage", # "pourcentage" (tumeur >= tumor_thr sur tout le patch)
                                # "centre" (idem prototype : tumeur dans la zone centrale, aucune tumeur = sain)
    "tumor_thr": 0.5, # seuil de la méthode "pourcentage"
    "centre_um": 56, # côté de la zone centrale en µm (pour la méthode "centre") = la moitié du patch

    # Équilibre des classes
    "max_tumor": 250, # patchs tumoraux au plus par lame
    "max_normal": 250, # patchs sains au plus par lame

    # Calcul
    "slide_workers": 3, # lames traitées en même temps
    "workers": 16, # lectures en parallèle dans une lame
    "seed": 0, # graine aléatoire
}

VARIANTES = {
    # La version de base (avec les paramètres ci-dessus)
    "base": {},
    # Test de l'étiquetage : zone centrale au lieu de 50 % de tumeur sur tout le patch
    "centre": {"labelling": "centre"},
    # Test des niveaux : même surface (112 µm) lue au niveau 2
    "niveaux": {"patch_level": [2]},
    # Le choix final, à remplir après les tests
    "retenue": {"labelling": "centre", "patch_level": [2]},
}
