# Backlog

Tareas en orden de ejecución. Cada una es un issue; se toman de a una (ver [CONTRIBUTING.md](CONTRIBUTING.md)).
🙋 = necesita algo del usuario. Las fases F2 en adelante se detallan más al llegar a cada una.


## F0 · Preparación

> Cuándo está lista: HA ve las luces y la tele; el detector reconoce "Luchi" con < 1 falso positivo por hora de TV de fondo

- [x] [#1](https://github.com/MaxLezano/LuchiAssistant/issues/1) **F0-01** Build Tools de Visual Studio (C++) + Rust MSVC
- [x] [#2](https://github.com/MaxLezano/LuchiAssistant/issues/2) **F0-02** Ollama + qwen3:8b con modelos en D:/E:
- [x] [#3](https://github.com/MaxLezano/LuchiAssistant/issues/3) **F0-03** Python 3.12 con uv
- [x] [#4](https://github.com/MaxLezano/LuchiAssistant/issues/4) **F0-04** ffmpeg y yt-dlp
- [x] [#5](https://github.com/MaxLezano/LuchiAssistant/issues/5) **F0-05** VM de Home Assistant OS en Hyper-V
- [x] [#6](https://github.com/MaxLezano/LuchiAssistant/issues/6) **F0-06** Onboarding de Home Assistant y token de larga duración 🙋
- [x] [#7](https://github.com/MaxLezano/LuchiAssistant/issues/7) **F0-07** Inventario de dispositivos de la casa 🙋
- [ ] [#8](https://github.com/MaxLezano/LuchiAssistant/issues/8) **F0-08** Integrar los dispositivos en Home Assistant 🙋
- [ ] [#9](https://github.com/MaxLezano/LuchiAssistant/issues/9) **F0-09** Elegir la voz de Piper en español 🙋
- [ ] [#10](https://github.com/MaxLezano/LuchiAssistant/issues/10) **F0-10** Spike wake word: generar muestras de "Luchi" y "Oye Luchi"
- [ ] [#11](https://github.com/MaxLezano/LuchiAssistant/issues/11) **F0-11** Spike wake word: entrenar los modelos
- [ ] [#12](https://github.com/MaxLezano/LuchiAssistant/issues/12) **F0-12** Spike wake word: herramienta de prueba y medición
- [ ] [#13](https://github.com/MaxLezano/LuchiAssistant/issues/13) **F0-13** Spike wake word: medir con el usuario 🙋
- [ ] [#14](https://github.com/MaxLezano/LuchiAssistant/issues/14) **F0-14** Cierre de F0 🙋

## F1 · Escucha y personaje

> Cuándo está lista: "Luchi, hola": Luchi cae desde el borde, escucha, muestra "hola" y se esconde saltando hacia arriba

- [ ] [#15](https://github.com/MaxLezano/LuchiAssistant/issues/15) **F1-01** Scaffold de apps/desktop (Tauri 2 + TS + Vite + Vitest)
- [ ] [#16](https://github.com/MaxLezano/LuchiAssistant/issues/16) **F1-02** Scaffold de services/voice (uv + pytest, hexagonal)
- [ ] [#17](https://github.com/MaxLezano/LuchiAssistant/issues/17) **F1-03** Verificación local de todo el repo
- [ ] [#18](https://github.com/MaxLezano/LuchiAssistant/issues/18) **F1-04** Protocolo WebSocket voz ↔ app
- [ ] [#19](https://github.com/MaxLezano/LuchiAssistant/issues/19) **F1-05** luchi-voice: micrófono + detector de "Luchi"
- [ ] [#20](https://github.com/MaxLezano/LuchiAssistant/issues/20) **F1-06** luchi-voice: fin de frase con Silero VAD
- [ ] [#21](https://github.com/MaxLezano/LuchiAssistant/issues/21) **F1-07** luchi-voice: transcripción con faster-whisper en GPU
- [ ] [#22](https://github.com/MaxLezano/LuchiAssistant/issues/22) **F1-08** luchi-voice: servidor WebSocket y orquestación
- [ ] [#23](https://github.com/MaxLezano/LuchiAssistant/issues/23) **F1-09** Tokens de diseño y componentes base
- [ ] [#24](https://github.com/MaxLezano/LuchiAssistant/issues/24) **F1-10** Dominio del personaje: Expression, BodyTransform, Style y líneas de tiempo
- [ ] [#25](https://github.com/MaxLezano/LuchiAssistant/issues/25) **F1-11** CanvasRenderer: cuerpo, sombra, mejillas, ojos, párpados, tinta y boca
- [ ] [#26](https://github.com/MaxLezano/LuchiAssistant/issues/26) **F1-12** Emociones: aparecer, atento, escuchando, esconderse, dormido
- [ ] [#27](https://github.com/MaxLezano/LuchiAssistant/issues/27) **F1-13** Tests visuales contra frames del prototipo
- [ ] [#28](https://github.com/MaxLezano/LuchiAssistant/issues/28) **F1-14** Isla: ventana transparente con borde, Luchi y globo
- [ ] [#29](https://github.com/MaxLezano/LuchiAssistant/issues/29) **F1-15** Bandeja del sistema y atajo de teclado
- [ ] [#30](https://github.com/MaxLezano/LuchiAssistant/issues/30) **F1-16** Conectar la app con luchi-voice
- [ ] [#31](https://github.com/MaxLezano/LuchiAssistant/issues/31) **F1-17** Ventana principal, barra lateral y Ajustes › General básico
- [ ] [#32](https://github.com/MaxLezano/LuchiAssistant/issues/32) **F1-18** Estado del sistema (micrófono y detector)
- [ ] [#33](https://github.com/MaxLezano/LuchiAssistant/issues/33) **F1-19** Laboratorio del personaje
- [ ] [#34](https://github.com/MaxLezano/LuchiAssistant/issues/34) **F1-20** Cierre de F1 🙋

## F2 · Casa

> Cuándo está lista: "Luchi, prendé la luz del comedor" funciona y Luchi contesta "Listo"

- [ ] [#35](https://github.com/MaxLezano/LuchiAssistant/issues/35) **F2-01** Piper TTS en luchi-voice con amplitud en vivo
- [ ] [#36](https://github.com/MaxLezano/LuchiAssistant/issues/36) **F2-02** HomePort: Home Assistant Assist + REST
- [ ] [#37](https://github.com/MaxLezano/LuchiAssistant/issues/37) **F2-03** Router rápido sin LLM y `home_command`
- [ ] [#38](https://github.com/MaxLezano/LuchiAssistant/issues/38) **F2-04** Emociones: hablando, feliz, guiño, apenado
- [ ] [#39](https://github.com/MaxLezano/LuchiAssistant/issues/39) **F2-05** Set de evaluación de órdenes 🙋
- [ ] [#40](https://github.com/MaxLezano/LuchiAssistant/issues/40) **F2-06** Ajustes › Voz y micrófono
- [ ] [#41](https://github.com/MaxLezano/LuchiAssistant/issues/41) **F2-07** Casa y dispositivos (estado y lista)
- [ ] [#42](https://github.com/MaxLezano/LuchiAssistant/issues/42) **F2-08** Cierre de F2 🙋

## F3 · Cerebro

> Cuándo está lista: "Luchi, poné lofi" y "pausa" funcionan

- [ ] [#43](https://github.com/MaxLezano/LuchiAssistant/issues/43) **F3-01** LlmPort con Ollama y tool calling
- [ ] [#44](https://github.com/MaxLezano/LuchiAssistant/issues/44) **F3-02** Acciones de PC en Rust: media_control y set_volume
- [ ] [#45](https://github.com/MaxLezano/LuchiAssistant/issues/45) **F3-03** play_media YouTube en PC, open_url y web_search
- [ ] [#46](https://github.com/MaxLezano/LuchiAssistant/issues/46) **F3-04** Preguntas generales + pantalla
- [ ] [#47](https://github.com/MaxLezano/LuchiAssistant/issues/47) **F3-05** Emoción pensando (> 400 ms)
- [ ] [#48](https://github.com/MaxLezano/LuchiAssistant/issues/48) **F3-06** Comparar 2–3 modelos con el set de evaluación
- [ ] [#49](https://github.com/MaxLezano/LuchiAssistant/issues/49) **F3-07** Cierre de F3 🙋

## F4 · Apps y sistema

> Cuándo está lista: Abre y cierra juegos por nombre sin mirar la pantalla

- [ ] [#50](https://github.com/MaxLezano/LuchiAssistant/issues/50) **F4-01** Catálogo de apps: Menú Inicio y Steam
- [ ] [#51](https://github.com/MaxLezano/LuchiAssistant/issues/51) **F4-02** launch_app y close_app con búsqueda aproximada
- [ ] [#52](https://github.com/MaxLezano/LuchiAssistant/issues/52) **F4-03** Preguntas de aclaración en voz + emoción pregunta
- [ ] [#53](https://github.com/MaxLezano/LuchiAssistant/issues/53) **F4-04** Acciones del sistema
- [ ] [#54](https://github.com/MaxLezano/LuchiAssistant/issues/54) **F4-05** Pantalla Apps y sistema
- [ ] [#55](https://github.com/MaxLezano/LuchiAssistant/issues/55) **F4-06** Cierre de F4 🙋

## F5 · Tele y películas

> Cuándo está lista: "Luchi, poné Interestelar en Netflix en la tele"

- [ ] [#56](https://github.com/MaxLezano/LuchiAssistant/issues/56) **F5-01** Destinos multimedia y devices.yaml
- [ ] [#57](https://github.com/MaxLezano/LuchiAssistant/issues/57) **F5-02** Control de la tele vía HA
- [ ] [#58](https://github.com/MaxLezano/LuchiAssistant/issues/58) **F5-03** TitleResolverPort + catálogo local de títulos
- [ ] [#59](https://github.com/MaxLezano/LuchiAssistant/issues/59) **F5-04** Netflix y YouTube en PC y en la tele
- [ ] [#60](https://github.com/MaxLezano/LuchiAssistant/issues/60) **F5-05** Asistente para agregar dispositivos (config flows de HA)
- [ ] [#61](https://github.com/MaxLezano/LuchiAssistant/issues/61) **F5-06** Detectados en la red y video por defecto
- [ ] [#62](https://github.com/MaxLezano/LuchiAssistant/issues/62) **F5-07** Cierre de F5 🙋

## F6 · Grabar reuniones

> Cuándo está lista: "Grabá esta reunión" → "dejá de grabar" deja audio.mp3 y transcripcion.txt; "traducí la última al inglés" crea transcripcion.en.txt

- [ ] [#63](https://github.com/MaxLezano/LuchiAssistant/issues/63) **F6-01** Captura en dos pistas (micrófono + loopback)
- [ ] [#64](https://github.com/MaxLezano/LuchiAssistant/issues/64) **F6-02** Mezcla a MP3 con ffmpeg
- [ ] [#65](https://github.com/MaxLezano/LuchiAssistant/issues/65) **F6-03** Transcripción Yo / Otros
- [ ] [#66](https://github.com/MaxLezano/LuchiAssistant/issues/66) **F6-04** Traducción y resumen con el LLM local
- [ ] [#67](https://github.com/MaxLezano/LuchiAssistant/issues/67) **F6-05** Pantalla Grabaciones + isla en modo grabación
- [ ] [#68](https://github.com/MaxLezano/LuchiAssistant/issues/68) **F6-06** Spike: loopback de una sola app
- [ ] [#69](https://github.com/MaxLezano/LuchiAssistant/issues/69) **F6-07** Cierre de F6 🙋

## F7 · Conversación y memoria

> Cuándo está lista: Diálogo de 2–3 turnos sin repetir "Luchi"

- [ ] [#70](https://github.com/MaxLezano/LuchiAssistant/issues/70) **F7-01** SQLite local
- [ ] [#71](https://github.com/MaxLezano/LuchiAssistant/issues/71) **F7-02** Ventana de seguimiento y contexto de la última orden
- [ ] [#72](https://github.com/MaxLezano/LuchiAssistant/issues/72) **F7-03** Historial, correcciones por voz y botón, deshacer
- [ ] [#73](https://github.com/MaxLezano/LuchiAssistant/issues/73) **F7-04** Recordatorios y temporizadores
- [ ] [#74](https://github.com/MaxLezano/LuchiAssistant/issues/74) **F7-05** Dictado
- [ ] [#75](https://github.com/MaxLezano/LuchiAssistant/issues/75) **F7-06** Emociones: mareado, cansado, amor, enojado
- [ ] [#76](https://github.com/MaxLezano/LuchiAssistant/issues/76) **F7-07** Cierre de F7 🙋

## F8 · Escenas y rutinas

> Cuándo está lista: Una frase dispara varias acciones

- [ ] [#77](https://github.com/MaxLezano/LuchiAssistant/issues/77) **F8-01** Escenas: modelo y run_scene
- [ ] [#78](https://github.com/MaxLezano/LuchiAssistant/issues/78) **F8-02** Editor de escenas y horarios
- [ ] [#79](https://github.com/MaxLezano/LuchiAssistant/issues/79) **F8-03** Cierre de F8 🙋

## F9 · La voz de Luchi

> Cuándo está lista: Luchi habla con su voz

- [ ] [#80](https://github.com/MaxLezano/LuchiAssistant/issues/80) **F9-01** Evaluar motores de clonación de voz locales
- [ ] [#81](https://github.com/MaxLezano/LuchiAssistant/issues/81) **F9-02** Grabación de datos de voz 🙋
- [ ] [#82](https://github.com/MaxLezano/LuchiAssistant/issues/82) **F9-03** Integrar la voz clonada en TextToSpeechPort
- [ ] [#83](https://github.com/MaxLezano/LuchiAssistant/issues/83) **F9-04** Cierre de F9 🙋

## F10 · Toda la casa (opcional)

> Cuándo está lista: Se le habla desde el comedor sin estar en la PC

- [ ] [#84](https://github.com/MaxLezano/LuchiAssistant/issues/84) **F10-01** Satélites por habitación (opcional) 🙋

## F11 · Pulido

> Cuándo está lista: Uso diario sin fricción

- [ ] [#85](https://github.com/MaxLezano/LuchiAssistant/issues/85) **F11-01** Autostart, instalador y firma local
- [ ] [#86](https://github.com/MaxLezano/LuchiAssistant/issues/86) **F11-02** Modo juego automático y ocultar en pantalla completa
- [ ] [#87](https://github.com/MaxLezano/LuchiAssistant/issues/87) **F11-03** Movimiento reducido y subtítulos accesibles
- [ ] [#88](https://github.com/MaxLezano/LuchiAssistant/issues/88) **F11-04** Bienvenida, Privacidad y Acerca de
- [ ] [#89](https://github.com/MaxLezano/LuchiAssistant/issues/89) **F11-05** Interacciones extra: mirada al cursor, squish, bailar con la música
- [ ] [#90](https://github.com/MaxLezano/LuchiAssistant/issues/90) **F11-06** Cierre de F11 🙋

## F12 · Tu Luchi

> Cuándo está lista: Cada usuario arma su Luchi, todas las emociones siguen funcionando y sus preferencias lo siguen a otra PC

- [ ] [#91](https://github.com/MaxLezano/LuchiAssistant/issues/91) **F12-01** Renderer: colores, estilos de ojos y bocas
- [ ] [#92](https://github.com/MaxLezano/LuchiAssistant/issues/92) **F12-02** Renderer: tatuajes (multiply, realismo) y accesorios
- [ ] [#93](https://github.com/MaxLezano/LuchiAssistant/issues/93) **F12-03** Editor Tu Luchi
- [ ] [#94](https://github.com/MaxLezano/LuchiAssistant/issues/94) **F12-04** Accesorios de temporada automáticos
- [ ] [#95](https://github.com/MaxLezano/LuchiAssistant/issues/95) **F12-05** Exportar/importar .luchi y copias locales
- [ ] [#96](https://github.com/MaxLezano/LuchiAssistant/issues/96) **F12-06** Iniciar sesión con Google y sincronizar con Drive appDataFolder
- [ ] [#97](https://github.com/MaxLezano/LuchiAssistant/issues/97) **F12-07** Cierre de F12 🙋
