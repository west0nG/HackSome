# Component Guidelines

> How components are built in this project.

---

## Overview

<!--
Document your project's component conventions here.

Questions to answer:
- What component patterns do you use?
- How are props defined?
- How do you handle composition?
- What accessibility standards apply?
-->

(To be filled by the team)

---

## Component Structure

### C6 candidate dossier contract

The Creative C6 review UI renders a vertical stack of project dossiers. One
`article.project-review-card` owns exactly one Concept and must contain, in
order:

1. the exact Concept title, hook, revision reference, and hash;
2. three fact panels: experience/hook, software/demo, and share artifact;
3. optional collapsed source material;
4. one `section.project-review-section` for that Concept's receipt.

The reviewer name and overall comment may remain batch-level. Concept fields,
reaction controls, completion state, and draft storage must not be detached
from their dossier or reused as one global questionnaire.

```js
// Correct: the receipt remains inside the same article as its source facts.
card.append(facts);
card.append(details, createConceptReviewSection(concept, index));

// Wrong: a shared form after all cards loses the Concept-to-receipt context.
cards.append(...conceptSummaries);
page.append(sharedConceptQuestionnaire);
```

Desktop uses three fact columns inside each dossier; mobile changes those
columns to a single stack without changing ownership or DOM order.

---

## Props Conventions

<!-- How props should be defined and typed -->

(To be filled by the team)

---

## Styling Patterns

<!-- How styles are applied (CSS modules, styled-components, Tailwind, etc.) -->

(To be filled by the team)

---

## Accessibility

- Use a semantic `article` per Concept and an `aria-labelledby` review region.
- Every input must have a unique label and ID derived from its Concept index.
- A blank dossier is a valid skip; do not force reviewers through every card.
- Mobile must not scroll horizontally, and focus order must follow visual order.

---

## Common Mistakes

- Do not place all Concept descriptions above one shared set of review fields.
- Do not render curator-only feasibility evidence inside reviewer dossiers.
- Do not key draft state by display position alone; persist it under the stable
  Concept reference and bind submitted data to the exact revision/hash.
