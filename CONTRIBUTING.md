# Cómo se trabaja

## Backlog

- Cada tarea es un **issue** con el código de su fase en el título (`[F0-03] …`), una etiqueta de fase (`F0`…`F12`) y su milestone.
- [BACKLOG.md](BACKLOG.md) es el índice en orden de ejecución. Las tareas se toman **de a una**, en orden.
- `usuario` marca las tareas que necesitan algo del usuario (hablarle al micrófono, inventario, aceptar avisos en la tele).

## Ramas

- `main` siempre funciona. No se commitea directo, salvo el commit inicial.
- Una rama por tarea, desde `main` actualizado: `<tipo>/<issue>-<slug>`, por ejemplo `chore/2-build-tools-rust`.
- Tipos: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `spike`.

## Commits

- [Conventional commits](https://www.conventionalcommits.org/) en español, chicos y con un solo propósito: `feat(voice): detectar fin de frase con Silero VAD`.
- Scopes habituales: `repo`, `infra`, `voice`, `desktop`, `character`, `island`, `ui`, `assistant`, `home`, `media`, `recordings`, `docs`.
- Sin atribución de IA ni `Co-Authored-By`.

## Pull requests

- Uno por tarea, con `Closes #<issue>`, qué se hizo y cómo se verificó (tests, capturas o resultado corriendo).
- Se integra con *merge commit* para conservar los commits chicos. La rama se conserva.
- Al cerrar la última tarea de una fase se muestra que cumple su criterio "Cuándo está lista" (PLAN.md §7) y se espera aprobación antes de seguir.
