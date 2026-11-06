# Trame de soutenance — 10 minutes

| Temps | Sujet |
|---|---|
| 0:00–1:00 | Besoin médical et question étudiée |
| 1:00–2:30 | Données, unités patch/lame/patient, limites |
| 2:30–4:00 | Pipeline et prévention des fuites |
| 4:00–5:30 | Baseline et expérience d'amélioration |
| 5:30–7:30 | Résultats, erreurs, généralisation inter-centres |
| 7:30–9:00 | Interprétabilité, portée du pN, limites |
| 9:00–10:00 | Conclusion et réponse à la problématique |

Répartir environ deux minutes par membre sans couper artificiellement une explication.
Questions croisées : pourquoi ce split ? Que signifie un faux négatif ? D'où vient le label ? Pourquoi un score patch ne suffit-il pas au pN ? Qu'avons-nous réellement testé ? Que contient le test final ?

## Messages à préparer, sans fabriquer de résultats

1. **Besoin :** expliquer le passage de l’image très grande au patch et pourquoi les erreurs n’ont pas toutes les mêmes conséquences.
2. **Données :** montrer la source, les effectifs réellement observés et le contrôle de séparation. Distinguer groupe patient artificiel et patiente biologique.
3. **Méthode :** expliquer ce qui est gelé dans ResNet18, ce qui apprend et comment la validation choisit le checkpoint.
4. **Résultats :** présenter les métriques avec les dénominateurs, un faux négatif et un faux positif réels si disponibles. Ne pas substituer les chiffres de démonstration à des expériences absentes.
5. **Portée :** expliquer ce que montre Grad-CAM, les limites du centre de test et pourquoi le pN reste une étape séparée.

## Questions et réponses de principe

- **Pourquoi ne pas découper aléatoirement les patchs ?** Des patchs d’une même lame peuvent être très proches ; leur présence des deux côtés donnerait une évaluation trop favorable.
- **WILDS suffit-il au stade pN ?** L’autorisation d’utiliser WILDS ne fournit pas automatiquement les informations nécessaires à toutes les agrégations. Notre périmètre doit être confirmé.
- **Une forte accuracy suffit-elle ?** Non : elle peut masquer des faux négatifs et dépend de la proportion de classes.
- **Une belle Grad-CAM prouve-t-elle que le modèle a raison ?** Non : c’est une aide d’analyse qualitative, à confronter aux annotations.
- **Qu’avez-vous réellement validé aujourd’hui ?** Le logiciel sur une démonstration artificielle ; la qualité sur données réelles reste à établir tant que les expériences correspondantes ne sont pas réalisées.
- **Qui comprend le code ?** Chaque membre doit être capable d’expliquer la chaîne entière ; les rôles ne dispensent pas de cette maîtrise.
