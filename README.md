>[!NOTE]
> This is a work in progress. The content may change frequently and could be incomplete. Do NOT rely on this for production use.

>[!IMPORTANT]
> This is not the original IntenseRP Next project. Here I'm rebuilding it from scratch with new technologies and approaches. Right now it's in a state of messy, inefficient reverse-engineering and prototyping, but eventually it will eat its predecessor and restore "the glory" of IntenseRP Next.

>[!DANGER]
> The auto-updater is currently VERY, VERY broken and may corrupt your installation. Just don't use it for now, I'll figure it out later.

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

# To contributors

Feel free to open issues or submit PRs, but keep in mind that we don't have a clear roadmap (besides for what's inside my head) and things may change frequently, so contributions may be wasted if they don't align with the final design.

Also, if we do agree on something, just make sure to follow best practices and keep a similar modular structure as the rest of the codebase. Also, please add lots of comments, I throw them in everywhere so it's easier to understand for other contributors (and for myself in the future).

# Credits (so far)

- Feather Icons (<https://feathericons.com/>) - for the icon set used in the UI
- Qt6 / PySide6 - for the configuration app framework
- FastAPI - for the server framework
- Playwright - for browser automation
- Patchright - for stealth techniques and ideas
- SillyTavern - for the actual front-end that will use this backend
- IntenseRP API (from OmegaSlender) - for the original idea and some code snippets
- Me for doing all the work :D