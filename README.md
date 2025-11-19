>[!NOTE]
> This is a work in progress. The content may change frequently and could be incomplete. Do NOT rely on this for production use.

>[!IMPORTANT]
> This is not the original IntenseRP Next project. Here I'm rebuilding it from scratch with new technologies and approaches. Right now it's in a state of messy, inefficient reverse-engineering and prototyping, but eventually it will eat its predecessor and restore "the glory" of IntenseRP Next.

# What's known

- v2 will use Python and FastAPI for the backend.
- The configuration app will be built with PySide6.
- Browser automation will be made with Playwright.
- Network interception will be the only method for working with providers.
- v2 will support multiple providers (DeepSeek, Alibaba, Z.AI, Moonshot, etc.) out of the box.

# What isn't

- No support for Electron or web-based configuration apps.
- Not sure about support for older Python versions (will likely require Python 3.12+).
- Still figuring out how I'll package and distribute the app (PyInstaller, Docker, etc.).
- Will rewrite the installer from scratch as well.
- Likely will use QT-Material for theming the configuration app, but not 100% decided yet.
- No, not a HTML5 app D: like SillyTavern
- Stealth probably still Chrome-based (since Patchright is Chrome-based), for FF I'll just recommend Camoufox or similar.