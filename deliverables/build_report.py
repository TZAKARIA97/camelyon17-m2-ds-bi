from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "out"
ASSETS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "17324D"
TEAL = "1F7A8C"
LIGHT = "EEF3F6"
TEXT = RGBColor(38, 45, 54)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, bold=False, color=None, size=10):
    cell.text = ""
    p = cell.paragraphs[0]
    r = p.add_run(str(text))
    r.bold = bold
    r.font.name = "Aptos"
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        set_cell_text(t.rows[0].cells[i], h, True, "FFFFFF", 9.5)
        shade(t.rows[0].cells[i], NAVY)
    for ridx, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            set_cell_text(cells[i], val, False, None, 9.3)
            if ridx % 2:
                shade(cells[i], LIGHT)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return t


def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(item)


def add_figure(doc, path, caption, width=6.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width))
    c = doc.add_paragraph(caption)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.style = doc.styles["Caption"]


def charts():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, ax = plt.subplots(figsize=(7.0, 3.7), dpi=170)
    vals = [0.9682, 0.9738]
    bars = ax.bar(["Niveau 1", "Niveau 2"], vals, color=["#8FB8C7", "#1F7A8C"], width=.58)
    ax.set_ylim(.94, .985); ax.set_ylabel("ROC-AUC de validation")
    ax.set_title("Comparaison à surface constante de 112 µm")
    ax.grid(axis="y", color="#D9E2E8"); ax.spines[["top", "right"]].set_visible(False)
    for b, v in zip(bars, vals):
        ax.text(b.get_x()+b.get_width()/2, v+.001, f"{v:.4f}", ha="center", fontweight="bold")
    fig.tight_layout(); p1 = ASSETS / "selection_niveau.png"; fig.savefig(p1, facecolor="white"); plt.close(fig)

    methods = ["Original", "Reinhard", "Macenko"]
    spec = [.8967, .8750, .8217]; auc = [.9752, .9767, .9743]
    x = np.arange(3); w = .34
    fig, ax = plt.subplots(figsize=(7.0, 3.8), dpi=170)
    ax.bar(x-w/2, spec, w, label="Spécificité moyenne", color="#1F7A8C")
    ax.bar(x+w/2, auc, w, label="ROC-AUC moyenne", color="#17324D")
    ax.set_xticks(x, methods); ax.set_ylim(.75, 1.0)
    ax.set_title("Validation multicentre")
    ax.legend(frameon=False, ncols=2, loc="lower center")
    ax.grid(axis="y", color="#D9E2E8"); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); p2 = ASSETS / "validation_multicentre.png"; fig.savefig(p2, facecolor="white"); plt.close(fig)

    m = np.array([[589, 11], [92, 172]])
    fig, ax = plt.subplots(figsize=(5.4, 4.2), dpi=170)
    im = ax.imshow(m, cmap="Blues")
    ax.set_xticks([0, 1], ["Prédit sain", "Prédit tumoral"])
    ax.set_yticks([0, 1], ["Réel sain", "Réel tumoral"])
    ax.set_title("Test inter-centres au seuil figé")
    for (i, j), v in np.ndenumerate(m):
        ax.text(j, i, str(v), ha="center", va="center", fontsize=15, fontweight="bold",
                color="white" if v > m.max()/2 else "#17324D")
    fig.colorbar(im, ax=ax, fraction=.045, pad=.04)
    fig.subplots_adjust(left=.23, right=.88, bottom=.16, top=.88)
    p3 = ASSETS / "matrice_test.png"; fig.savefig(p3, facecolor="white"); plt.close(fig)
    return p1, p2, p3


def configure(doc):
    sec = doc.sections[0]
    sec.page_width = Inches(8.5); sec.page_height = Inches(11)
    sec.top_margin = Inches(.68); sec.bottom_margin = Inches(.68)
    sec.left_margin = Inches(.72); sec.right_margin = Inches(.72)
    styles = doc.styles
    styles["Normal"].font.name = "Aptos"; styles["Normal"].font.size = Pt(10.7); styles["Normal"].font.color.rgb = TEXT
    styles["Normal"].paragraph_format.space_after = Pt(6)
    for name, size, color in [("Title", 31, NAVY), ("Subtitle", 17, TEAL), ("Heading 1", 22, NAVY), ("Heading 2", 15, TEAL), ("Heading 3", 12, NAVY)]:
        st = styles[name]; st.font.name = "Aptos Display"; st.font.size = Pt(size); st.font.bold = name != "Subtitle"; st.font.color.rgb = RGBColor.from_string(color)
    styles["Caption"].font.name = "Aptos"; styles["Caption"].font.size = Pt(9); styles["Caption"].font.italic = True
    for s in doc.sections:
        footer = s.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        footer.add_run("Projet CAMELYON17  •  20 novembre 2026  •  ")
        fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), "PAGE"); footer._p.append(fld)


def page(doc, title):
    doc.add_page_break(); doc.add_heading(title, level=1)


def build():
    p1, p2, p3 = charts()
    d = Document(); configure(d)
    d.add_paragraph("Détection de métastases dans CAMELYON17", style="Title").alignment = WD_ALIGN_PARAGRAPH.CENTER
    d.add_paragraph("Pipeline multi-échelle, généralisation multicentre et limites de l’agrégation pN", style="Subtitle").alignment = WD_ALIGN_PARAGRAPH.CENTER
    d.add_paragraph("\n")
    add_table(d, ["Cadre", "Informations"], [
        ["Formation", "M2 Data Science & BI — Projet 1 de spécialisation"],
        ["Groupe", "Zaki, Élodie, Joël, Mélanie et Paul"],
        ["Encadrement", "Ines Krissaane"],
        ["Version", "Rapport critique — 20 novembre 2026"],
    ], [2.2, 4.6])
    p = d.add_paragraph("Travail pédagogique. Aucun usage clinique ni diagnostic individuel."); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].italic = True

    page(d, "Résumé")
    d.add_paragraph("Le projet étudie la détection de tissu tumoral dans les lames histopathologiques CAMELYON17. La chaîne couvre une région physique de 112 µm, lit les lames au niveau 2, redimensionne les régions en 224 × 224 pixels, extrait 512 caractéristiques avec ResNet18 puis applique une régression logistique. Le niveau 2 obtient une ROC-AUC de validation de 0,9738, contre 0,9682 au niveau 1.")
    d.add_paragraph("L’expérience multicentre retient les images originales. Sur le centre 2 réservé au test, la ROC-AUC atteint 0,8715 et le rappel 0,6515 malgré une précision de 0,9399. Le modèle conserve une forte spécificité, mais manque de nombreux patches tumoraux. La carte de chaleur, la classe de lame et le stade pN sont codés. Les cellules finales n’ont toutefois pas produit de résultats dans l’archive collective. Le rapport ne présente donc aucune performance pN non démontrée.")
    d.add_heading("Question de recherche", level=2)
    d.add_paragraph("Dans quelle mesure une représentation ResNet18 préentraînée détecte-t-elle les métastases au niveau patch et conserve-t-elle sa sensibilité lorsqu’elle est appliquée à des lames provenant d’un autre centre hospitalier ?")
    d.add_heading("Réponse synthétique", level=2)
    add_bullets(d, ["La représentation sépare correctement les patches sur validation.", "Le niveau 2 offre le meilleur compromis mesuré entre performance et coût de lecture.", "Le rappel chute sur le centre non vu, ce qui empêche de conclure à une robustesse clinique."])

    page(d, "1 Contexte et périmètre")
    d.add_heading("1.1 Du patch à la patiente", level=2)
    d.add_paragraph("Une lame entière peut contenir des milliards de pixels. Le pipeline découpe donc les lames en régions. Le modèle produit une probabilité au niveau patch. Une carte de chaleur rassemble ces probabilités sur la lame. La taille de la plus grande lésion permet ensuite de classer la lame. Les classes de cinq ganglions déterminent enfin le stade pN de la patiente.")
    add_table(d, ["Niveau", "Entrée", "Sortie", "Risque principal"], [
        ["Patch", "Région de 112 µm", "Probabilité tumorale", "Faux négatif local"],
        ["Lame", "Carte de probabilités", "Négative, ITC, micro ou macro", "Seuil et regroupement spatial"],
        ["Patiente", "Cinq classes de ganglions", "Stade pN", "Ganglions incomplets ou mal classés"],
    ])
    d.add_heading("1.2 Périmètre réellement validé", level=2)
    d.add_paragraph("Les résultats démontrés concernent le niveau patch et l’expérience multicentre. La chaîne d’agrégation est présente dans le code, mais son exécution finale n’apparaît pas dans l’archive du groupe. Cette distinction évite de confondre une fonctionnalité implémentée avec une performance évaluée.")

    page(d, "2 Préparation des données")
    d.add_heading("2.1 Séparation de la cohorte", level=2)
    d.add_paragraph("Le notebook de préparation indexe les lames, associe les annotations XML et construit les ensembles d’entraînement, de validation et de test. La séparation se fait par patiente pour éviter qu’une même patiente apparaisse dans plusieurs ensembles. Le test reste fermé pendant le choix du niveau, du seuil et de la méthode de normalisation.")
    d.add_heading("2.2 Géométrie physique", level=2)
    d.add_paragraph("Le champ observé reste constant à 112 µm. Le code convertit cette longueur en pixels du niveau 0 à partir du MPP, applique le facteur de sous-échantillonnage du niveau choisi puis redimensionne l’image en 224 × 224 pixels pour ResNet18.")
    add_table(d, ["Paramètre", "Valeur retenue", "Justification"], [
        ["Surface du patch", "112 µm × 112 µm", "Comparaison indépendante du scanner"],
        ["Entrée ResNet18", "224 × 224 pixels", "Format standard du modèle"],
        ["Zone centrale", "56 µm × 56 µm", "Détection des petites lésions centrales"],
        ["Part minimale de tissu", "50 %", "Écarter le fond et les bords"],
        ["Quota par lame", "250 tumoraux et 250 sains", "Limiter le coût et l’effet des grandes lames"],
    ])

    page(d, "3 Modèle et protocole expérimental")
    d.add_heading("3.1 Représentation et classifieur", level=2)
    d.add_paragraph("ResNet18 préentraîné sur ImageNet transforme chaque patch en 512 caractéristiques. Les poids restent gelés. Une régression logistique apprend ensuite la séparation entre patches sains et tumoraux. Cette approche réduit le coût de calcul, mais ne spécialise pas les filtres convolutifs à l’histologie.")
    d.add_heading("3.2 Prévention des fuites", level=2)
    add_bullets(d, ["Séparation par patiente et contrôle de l’absence de recouvrement.", "Sélection du niveau et des hyperparamètres uniquement sur validation.", "Gel du seuil avant l’ouverture du centre de test.", "Publication des effectifs et des matrices de confusion avec les métriques."])
    d.add_heading("3.3 Métriques", level=2)
    d.add_paragraph("La ROC-AUC mesure la qualité du classement des scores. Le rappel mesure la part des patches tumoraux détectés. La précision mesure la part de prédictions tumorales correctes. La spécificité mesure la part des patches sains correctement rejetés. Dans ce contexte, un rappel faible reste critique même si la précision est élevée.")
    add_table(d, ["Étape 1", "Étape 2", "Étape 3", "Étape 4", "Étape 5"], [["Index et XML", "Patches 112 µm", "ResNet18", "Régression", "Carte et pN"]])

    page(d, "4 Choix du niveau")
    d.add_paragraph("Le niveau 2 atteint une ROC-AUC de validation de 0,9738 contre 0,9682 au niveau 1. À surface physique constante, il lit quatre fois moins de pixels avant redimensionnement. Ce choix combine la meilleure performance observée et un coût de lecture inférieur.")
    add_figure(d, p1, "Figure 1 — ROC-AUC de validation par niveau de lecture")
    add_table(d, ["Variante", "Niveau", "ROC-AUC validation", "C retenu", "ROC-AUC CV"], [["Base", "1", "0,9682", "0,001", "0,9403"], ["Niveaux", "2", "0,9738", "0,010", "0,9506"]])
    d.add_heading("Interprétation", level=2)
    d.add_paragraph("L’écart absolu de 0,0056 reste faible. Il ne démontre pas une supériorité générale du niveau 2. Il satisfait toutefois la règle de décision de cette exécution. Une répétition sur plusieurs graines et une cohorte plus large renforcerait la conclusion.")

    page(d, "5 Généralisation multicentre")
    d.add_heading("5.1 Choix sur validation", level=2)
    d.add_paragraph("L’expérience compare les images originales à deux normalisations de coloration. Chaque méthode doit atteindre au moins 95 % de rappel dans chacun des centres de validation. Parmi les méthodes admissibles, la spécificité moyenne puis la ROC-AUC moyenne déterminent le choix. Les images originales obtiennent la meilleure spécificité moyenne, 0,8967, avec une ROC-AUC moyenne de 0,9752.")
    add_figure(d, p2, "Figure 2 — Résultats de validation multicentre")
    add_table(d, ["Méthode", "Rappel C0", "Rappel C4", "Spécificité", "ROC-AUC"], [["Original", "0,965", "0,950", "0,8967", "0,9752"], ["Reinhard", "0,970", "0,950", "0,8750", "0,9767"], ["Macenko", "0,980", "0,950", "0,8217", "0,9743"]])

    page(d, "6 Test inter-centres et erreurs")
    d.add_paragraph("Le seuil 0,31390092 et la méthode originale sont figés avant l’ouverture du centre 2. Sur 864 patches, le modèle classe correctement 589 patches sains et 172 patches tumoraux. Il produit 11 fausses alertes et manque 92 patches tumoraux.")
    add_figure(d, p3, "Figure 3 — Matrice de confusion du test multicentre", 5.4)
    add_table(d, ["ROC-AUC", "Rappel", "Précision", "Spécificité", "Exactitude"], [["0,8715", "0,6515", "0,9399", "0,9817", "0,8808"]])
    d.add_heading("Lecture critique", level=2)
    d.add_paragraph("La précision et la spécificité restent élevées, mais le rappel chute de près de 30 points par rapport à la contrainte de validation. Le modèle déclenche peu de fausses alertes au prix de nombreuses lésions manquées. Le protocole ne démontre donc pas une robustesse suffisante face au changement de centre.")

    page(d, "7 Carte de chaleur, lame et stade pN")
    d.add_heading("7.1 Ce que le code couvre", level=2)
    add_table(d, ["Élément", "État", "Rôle"], [
        ["Carte de chaleur", "Implémentée", "Projeter les probabilités patch sur la lame"],
        ["Regroupement spatial", "Implémenté", "Mesurer la plus grande lésion"],
        ["Classe de lame", "Implémentée", "Négative, ITC, micro ou macro"],
        ["Stade pN", "Implémenté", "Agréger cinq ganglions"],
    ])
    d.add_heading("7.2 Ce que l’archive ne démontre pas", level=2)
    d.add_paragraph("Les cellules finales du notebook d’évaluation ne contiennent pas de résultats pour les cartes, les classes de lames, le stade pN ou le kappa. Aucune métrique patient n’est donc présentée. La prochaine exécution doit contrôler les cartes sur validation, figer les paramètres puis ouvrir le test une seule fois.")
    d.add_heading("Règle de communication", level=2)
    d.add_paragraph("Le rapport et les supports oraux indiquent clairement « chaîne codée, évaluation finale non exécutée ». Toute autre formulation donnerait une impression de complétude qui n’est pas soutenue par les fichiers transmis.")

    page(d, "8 Reproductibilité et qualité")
    d.add_heading("8.1 Vérifications réalisées", level=2)
    add_bullets(d, ["40 tests automatisés passent sur la branche alignée.", "Le vérificateur des résultats agrégés multicentres passe.", "Les notebooks sont des fichiers JSON valides.", "Le code Python compile sans erreur de syntaxe.", "Les données patient détaillées restent hors du dépôt public."])
    d.add_heading("8.2 Exécution", level=2)
    add_table(d, ["Étape", "Commande ou point d’entrée"], [
        ["Installer", "pip install -r requirements.txt"],
        ["Préparer", "01_preparation_donnees.ipynb"],
        ["Modéliser", "02_modelisation_evaluation.ipynb"],
        ["Contrôler les agrégats", "verifier_resultats_publics.py"],
        ["Lancer les tests", "python -m pytest"],
    ])
    d.add_heading("8.3 Confidentialité", level=2)
    d.add_paragraph("Le dépôt public conserve le code et les métriques agrégées. Les inventaires reliant des identifiants pseudonymisés à des classes médicales restent dans l’archive privée du groupe.")

    page(d, "9 Limites et usage responsable")
    add_table(d, ["Limite", "Conséquence", "Action"], [
        ["ResNet18 gelé", "Représentation non spécialisée", "Comparer un dégel partiel sur validation"],
        ["Écart faible entre niveaux", "Choix sensible à l’échantillon", "Répéter avec plusieurs graines"],
        ["Rappel test 0,6515", "Lésions manquées", "Recalibrer et analyser par taille de lésion"],
        ["Un seul centre de test", "Généralisation incomplète", "Tester plusieurs centres réservés"],
        ["pN non exécuté", "Pas de conclusion patient", "Finir puis auditer l’agrégation"],
    ])
    d.add_paragraph("Ce système reste un prototype pédagogique. Il ne doit pas servir à un diagnostic individuel. Une validation clinique exigerait une cohorte externe, une analyse par sous-groupe, un protocole de gestion des erreurs et une revue médicale indépendante.")

    page(d, "10 Conclusion et prochaines étapes")
    d.add_paragraph("Le projet fournit une chaîne cohérente pour traiter les lames CAMELYON17 à surface physique constante. Le niveau 2 est retenu sur validation avec une ROC-AUC de 0,9738 et un coût de lecture inférieur. La normalisation de coloration n’améliore pas la règle de sélection multicentre. Le test sur un centre non vu révèle toutefois un rappel limité à 0,6515.")
    add_table(d, ["Priorité", "Action", "Critère de sortie"], [
        ["1", "Exécuter les cartes de validation", "Contrôle visuel et seuil figé"],
        ["2", "Évaluer les classes de lames", "Matrice de confusion par classe"],
        ["3", "Calculer le stade pN", "Matrice patient et kappa"],
        ["4", "Renforcer le modèle", "Rappel inter-centres amélioré sans explosion des faux positifs"],
    ])
    d.add_heading("Conclusion répondant à la question", level=2)
    d.add_paragraph("ResNet18 fournit une représentation discriminante sur la validation patch, mais la sensibilité ne se maintient pas suffisamment sur le centre de test. Les résultats soutiennent l’usage du niveau 2 pour poursuivre les expériences. Ils ne valident pas le pipeline complet pour un usage clinique.")

    page(d, "Références et traçabilité")
    refs = [
        "Bandi, P. et al. From Detection of Individual Metastases to Classification of Lymph Node Status at the Patient Level: The CAMELYON17 Challenge.",
        "He, K. et al. Deep Residual Learning for Image Recognition. CVPR, 2016.",
        "Deng, J. et al. ImageNet: A Large-Scale Hierarchical Image Database. CVPR, 2009.",
        "Reinhard, E. et al. Color Transfer between Images. IEEE Computer Graphics and Applications, 2001.",
        "Macenko, M. et al. A Method for Normalizing Histology Slides for Quantitative Analysis. ISBI, 2009.",
        "Dépôt du projet CAMELYON17 M2 DS & BI, branche integration/version-groupe-alignee, commit public 90543eee6415c5337a8ee64f7c47de5e7d9111e1.",
    ]
    for ref in refs:
        d.add_paragraph(ref, style="List Number")
    d.add_heading("Usage de l’IA", level=2)
    d.add_paragraph("L’IA a aidé à structurer le dépôt, vérifier la cohérence des fichiers, reformuler le rapport et préparer les supports. Les résultats chiffrés proviennent uniquement des sorties du projet. Aucun résultat scientifique n’a été inventé. Le groupe reste responsable du code, des choix méthodologiques et de l’interprétation.")
    path = OUT / "Rapport_CAMELYON17.docx"; d.save(path); print(path)


if __name__ == "__main__":
    build()
