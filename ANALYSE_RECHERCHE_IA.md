# Phase d'Analyse et de Recherche 

## Objectif de la phase

Cette phase avait pour objectif d'étudier l'utilisation d'une intelligence artificielle pour assister la création de QCM à partir de documents de cours.

Les points étudiés étaient :

- l'extraction du texte des documents ;
- la segmentation des cours en sections ;
- la génération des questions ;
- la correction des questions par l'enseignant ;
- les performances des modèles ;
- les limites et les formats de sortie de l'IA.

Le fonctionnement étudié est :

```text
Document PDF ou Markdown
        ↓
Extraction du texte
        ↓
Segmentation en sections
        ↓
Génération des questions avec Ollama
        ↓
Affichage du QCM
        ↓
Correction éventuelle par l'enseignant
```

## Utilisation d'Ollama

Nous avons étudié plusieurs configurations :

- Ollama installé sur la machine ;
- Ollama installé sur un serveur distant.

## Comparaison des modèles

Le modèle `gemma4:26b` a été testé. Il nécessite beaucoup de mémoire et pouvait être arrêté ou ne pas répondre correctement avec les ressources disponibles.

Le modèle `llama3.2:3b` est plus léger et plus facile à exécuter, mais les réponses peuvent être moins précises.

Les tests ont montré un compromis entre :

- la qualité des réponses 
- la rapidité 
- la mémoire nécessaire
- la stabilité du serveur 

Le changement de modèle a aussi révélé un problème de compatibilité. Avec `gemma4:26b`, la segmentation pouvait renvoyer des sections exploitables. Après le passage à `llama3.2:3b`, le modèle pouvait ne pas respecter le format JSON attendu par la segmentation. Dans ce cas, aucune section n'était créée. Comme la génération des questions dépend des sections, l'application obtenait alors :

```text
0 section
    ↓
0 question
```

Ce comportement ne signifie pas nécessairement que le document est vide. Il peut simplement venir d'une réponse du modèle qui n'est pas compatible avec le format attendu, d'un JSON invalide ou d'un échec de l'appel à Ollama.

Une solution envisagée est de rendre la segmentation indépendante de la version du modèle utilisé. 
L'objectif serait que l'application fonctionne avec différents modèles disponibles sur le serveur, sans dépendre d'un format de réponse propre à `gemma4:26b` ou à `llama3.2:3b`.

## Segmentation des documents

La segmentation consiste à découper le cours en sections avant de générer les questions :

```text
Texte du document
        ↓
Découpage en blocs
        ↓
Analyse par Ollama
        ↓
Création des sections
        ↓
Génération des questions
```

Ici on utilise des blocs de 6000 caractères avec un chevauchement de 200 caractères :

## Méthode de segmentation réellement utilisée

Dans le code actuellement étudié, les titres du PDF sont bien extraits, mais ils ne servent pas à construire les sections. Comme `extractFromPdf()` et `extractFromMd()` transmettent un `OllamaWrapper` à `segment_text()`, la segmentation est réalisée par le LLM.

Le fonctionnement réellement observé est :

```text
Extraction du texte
        ↓
Extraction des titres
        ↓
Découpage en blocs de 6000 caractères
        ↓
Segmentation de chaque bloc par Ollama
        ↓
Création des sections à partir du JSON retourné
```

## Comparaison avec une segmentation algorithmique

Une segmentation algorithmique par titres ou paragraphes a été étudiée comme piste de comparaison, mais elle n'est pas utilisée actuellement dans le parcours d'extraction. Cette solution détecte moins de section que le LLM.


### Segmentation par LLM utilisée

La segmentation par LLM analyse le contenu et crée les sections selon les notions et concepts détectés.

Les essais réalisés sur cette méthode ont montré qu'elle peut produire beaucoup de sections. Cela peut produire des questions plus ciblées, mais augmente le temps de traitement :

```text
plus de sections
        ↓
plus d'appels à Ollama
        ↓
temps de génération plus long
```

Le traitement peut nécessiter :

```text
1 appel pour la segmentation
+ 1 appel par section pour la détection
+ 1 appel par section pour générer une question
```

Les tests disponibles vérifient surtout que la segmentation par LLM renvoie des sections valides.

Ainsi si il y a davantage de sections sa entraine plus d'appels et un temps de traitement plus long.

## Analyse réflexive : évolution de la BDD

L'application utilise actuellement PostgreSQL. Les données sont organisées dans des tables et manipulées avec des requêtes SQL. Cette solution fonctionne pour les données structurées comme les utilisateurs, les documents, les générations et les questions.

Cependant, le projet manipule aussi des structures plus imbriquées :

- les sections d'un document 
- les questions et leurs options 
- les retours de l'enseignant 
- les corrections 
- les résumés produits par le LLM 
- les contextes pédagogiques associés à une génération.

MongoDB est une solution envisagée, car son modèle documentaire permettrait de regrouper des données liées dans des documents et de stocker plus naturellement des tableaux ou des objets imbriqués.

## Taille des documents et temps de traitement

La taille du document influence directement la durée du traitement. Un document d'une vingtaine de pages contient généralement plus de texte qu'un document de cinq pages. Il est donc découpé en davantage de blocs de 6000 caractères, ce qui entraîne davantage d'appels à Ollama pour la segmentation.

Après la segmentation, chaque section peut également entraîner :

- un appel pour détecter la discipline et le type de contenu ;
- un appel pour générer la question ;
- d'éventuels appels supplémentaires en cas de contrôle anti-verbatim.

Il existe actuellement une limite sur le nombre de questions générées (`qcm_max_questions`). Cette limite est appliquée dans `generation_qcm()` après l'extraction et la segmentation 

Elle limite donc le nombre de questions finales, mais elle n'empêche pas la segmentation d'avoir déjà traité l'ensemble du document. Elle ne constitue pas une limite de taille du document et ne suffit pas à empêcher un appel de segmentation très long.

Une limite de pages, de caractères ou de blocs pourrait être ajoutée pour éviter qu'un document trop volumineux entraîne un temps d'attente excessif. Cette limite n'est pas encore mise en place dans le code actuel c'est un point à étudier et à définir selon le compromis recherché entre :

- traiter des documents complets ;
- limiter le temps d'attente ;
- réduire le nombre d'appels à Ollama ;
- éviter de consommer trop de ressources sur le serveur.

## Tests avec les mathématiques

Nous avons testé la génération de QCM à partir de cours de mathématiques.

Le LLM cherche à produire les formules en LaTeX, par exemple :

```latex
\( f(x) = x^2 + 2x + 1 \)
```

ou :

```latex
\[
\frac{a}{b}
\]
```

Une formule peut être correcte mathématiquement tout en n'étant pas directement exploitable comme une chaîne de caractères classique par l'application.

Les difficultés observées concernent notamment :

- les antislashs ;
- les caractères spéciaux ;
- l'affichage dans l'interface ;
- l'enregistrement des formules ;
- la différence entre une formule LaTeX et du texte simple.

## Difficultés liées aux schémas mathématiques

Les schémas présents dans un cours de maths sont aussi une limite. Si l'information importante se trouve dans un graphique, une figure ou un schéma, le modèle qui reçoit principalement le texte extrait du document peut avoir du mal à l'interpréter correctement. Il peut alors manquer une information, produire une explication incomplète ou générer une question qui ne tient pas compte du schéma.

L'analyse de documents contenant des schémas peut aussi ralentir le traitement. Le temps de traitement dépend alors du type de document, du modèle utilisé et de la complexité des schémas.

## Génération des questions

L'IA peut générer des questions cohérentes avec le document, mais elle peut aussi produire du contenu hors sujet ou inventer des informations.

Un cours de mathématiques a notamment pu produire des questions semblant appartenir à une autre matière. Plusieurs causes ont été envisagées :

- extraction incorrecte du PDF ;
- segmentation incorrecte ;
- texte incorrect envoyé au modèle ;
- hallucination du modèle.

Une question produite sans erreur technique n'est donc pas nécessairement correcte sur le plan pédagogique.

## Correction des questions

L'IA doit renvoyer un objet JSON contenant :

```json
{
  "question": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "bonne_reponse": "A. ..."
}
```

Les tests ont montré que l'IA peut :

- ne pas respecter la lettre de réponse demandée ;
- retourner une lettre au lieu du texte complet ;
- modifier la question sans corriger la réponse ;
- mal interpréter le numéro de la question ;
- ajouter du texte autour du JSON ;
- retourner un JSON vide ou incomplet.

## Format des réponses de l'IA

Même lorsque le modèle doit répondre uniquement en JSON, il peut renvoyer :

```text
Voici la correction :
{"question": "...", "options": [...]}
```

ou 

```text
{"question": "...", "options": [...]}
Explication supplémentaire...
```

Cela a provoqué des erreurs comme :

```text
Expecting value: line 1 column 1
Extra data
```

Nous avons donc mit en place un contrôle des réponses doivent avant d'être utilisées par l'application.

## Antiverbatism ???