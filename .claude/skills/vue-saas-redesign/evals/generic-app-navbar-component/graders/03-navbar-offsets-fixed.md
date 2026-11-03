---
type: llm
focus: trace
weight: 1
---

Every layout value that compensated for the 64px fixed navbar is updated: the 88px top padding on .page in main.css, and in ProjectsView.vue the toolbar's top: 64px and the filters' top: 64px / calc(100vh - 64px).
