# Anvaya — Browser Automation with AT-SPI

## 1. Overview

Anvaya is a personal AI assistant being developed to interact with desktop applications programmatically.

One of the current goals is to control the Brave browser through Python and the Linux Accessibility Technology Service Provider Interface (AT-SPI).

The intended workflow is:

1. Launch Brave programmatically.
2. Detect Brave through AT-SPI.
3. Access its application and window objects.
4. Discover accessible browser controls.
5. Interact with browser controls, including tabs and web content.

The objective is to interact with the browser as a desktop application rather than relying on a browser extension.

---

## 2. Development Environment

| Component | Configuration |
|---|---|
| Operating System | Fedora Workstation |
| Desktop Environment | GNOME 50.4 |
| Display Server | Wayland |
| Browser | Brave |
| Programming Language | Python |
| Accessibility Interface | AT-SPI |
| Python Accessibility Library | pyatspi |
| Browser Launch Method | gtk-launch |
| Project Environment | Python virtual environment |

### Important Python environment detail

`pyatspi` is installed through Fedora's system packages.

The system Python can access it:

```bash
/usr/bin/python3
```

The project also has a virtual environment:

```bash
~/anvaya/.venv
```

The virtual environment may not have access to Fedora's system-installed `pyatspi` package.

Do not assume that installing Python dependencies into the virtual environment automatically makes system RPM packages available.

---

## 3. Project Structure

Current relevant files:

```text
anvaya/
├── .venv/
├── backend/
├── docs/
├── prototype/
├── main.py
├── handling_Subprocess.py
└── requirements.txt
```

### `main.py`

Responsible for:

- Discovering the Brave application through AT-SPI.
- Checking whether Brave is already running.
- Initiating the browser launch if it is not detected.
- Inspecting accessible application objects.

### `handling_Subprocess.py`

Contains the subprocess handler used to launch desktop applications.

---

## 4. Launching Brave

Brave is launched through its desktop application entry:

```bash
gtk-launch brave-browser
```

The Python implementation uses a custom subprocess handler.

Example:

```python
import subprocess


class SubprocessHandler:

    def __init__(self, command, app_name):
        self.command = command
        self.app_name = app_name
        self.process = None

    def start_process(self, *args):
        self.process = subprocess.Popen(
            [self.command, self.app_name, *args],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )

        print(
            f"Started {self.app_name} "
            f"launcher with PID: {self.process.pid}"
        )
```

Usage:

```python
handler = SubprocessHandler(
    "gtk-launch",
    "brave-browser"
)

handler.start_process()
```

### Important observations

- `gtk-launch` launches the application using its desktop entry.
- It can reuse an existing Brave browser session.
- Additional command-line arguments passed through `gtk-launch` are not guaranteed to reach the actual browser process.
- The PID returned by `Popen` represents the launcher process, not necessarily the actual Brave browser process.
- `Popen.wait()` waits for the launcher process, not necessarily the browser.

---

## 5. Brave Accessibility Configuration

A user-level desktop entry was created:

```text
~/.local/share/applications/brave-browser.desktop
```

This overrides the corresponding system desktop entry.

The main launch entry was configured with:

```ini
Exec=env ACCESSIBILITY_ENABLED=1 /usr/bin/brave-browser-stable --force-renderer-accessibility %U
```

The new-window action was also configured to use accessibility-related launch settings.

### Brave accessibility verification

The following was checked through:

```text
brave://accessibility
```

Observed:

- Native accessibility: enabled.
- Web contents accessibility: enabled.

The actual accessibility tree is still being investigated.

### GNOME accessibility settings

Previously checked values:

```bash
gsettings get org.gnome.desktop.interface toolkit-accessibility
```

Result:

```text
true
```

```bash
gsettings get org.gnome.desktop.a11y.applications screen-reader-enabled
```

Result:

```text
false
```

These settings are different. Enabling toolkit accessibility does not mean that GNOME's screen reader is enabled.

---

## 6. AT-SPI Basics

AT-SPI provides an accessibility tree through which applications expose information about their interface.

The Python library used is:

```python
import pyatspi
```

The desktop accessibility root can be obtained using:

```python
registry = pyatspi.Registry

desktop = registry.getDesktop(0)
```

`pyatspi.Registry` is an existing registry object. It does not need to be instantiated.

### Inspect desktop applications

```python
import pyatspi

desktop = pyatspi.Registry.getDesktop(0)

print("Desktop:", desktop.name)

for i in range(desktop.getChildCount()):
    child = desktop.getChildAtIndex(i)

    print(
        f"Child {i}: "
        f"{child.name}, "
        f"Role: {child.getRoleName()}"
    )
```

### Important AT-SPI interfaces

| Interface | Purpose |
|---|---|
| Accessible | Names, roles, hierarchy and child objects |
| Action | Invoking supported accessibility actions |
| Component | Screen position, size and component operations |
| Text | Reading and interacting with exposed text |
| Selection | Accessing selection-related functionality |

The Action interface does not automatically provide keyboard input. It only exposes actions supported by the accessible object.

`pyatspi.Registry.start()` is relevant when running the event loop for registered accessibility event listeners. It is not required simply to enumerate the desktop tree.

---

## 7. Current Brave Detection Implementation

The current implementation searches the desktop accessibility tree for Brave.

A simplified version:

```python
import pyatspi
import handling_Subprocess
import time

found_application = False


def start_browser():
    handler = handling_Subprocess.SubprocessHandler(
        "gtk-launch",
        "brave-browser"
    )

    handler.start_process()


def find_browser():

    desktop = pyatspi.Registry.getDesktop(0)

    for i in range(desktop.getChildCount()):

        desktop_child = desktop.getChildAtIndex(i)

        print(
            f"Child {i}: "
            f"{desktop_child.name}"
        )

        if "brave" in (desktop_child.name or "").lower():

            print("Found Brave Browser")

            return desktop_child

    return None
```

The important design decision is that `find_browser()` returns the accessible application object or `None`.

This is preferable to modifying a global variable from inside a function.

### Why the original implementation needed improvement

The initial implementation had several issues:

1. `found_application` was modified inside a function without correctly managing its global scope.
2. The retry loop could launch Brave repeatedly.
3. Browser detection and browser launching were mixed together.
4. The function did not return the discovered application object.
5. The code searched backwards through the desktop children unnecessarily.

The recommended design separates:

- Browser discovery.
- Browser launching.
- Retry and timeout handling.

The browser should be launched once, followed by bounded polling for its appearance in AT-SPI.

---

## 8. Current Accessibility Investigation

Brave was initially missing from the desktop accessibility tree.

After configuring and investigating the accessibility setup, Brave became visible.

This is an important milestone: **Brave application registration with AT-SPI is now working.**

### Latest observed output

```text
main
Child 6: Brave Browser
Found Brave Browser: [application | Brave Browser]

Brave Browser is running.

application

Attributes:
[
    'explicit-name:true',
    'name-from:attribute'
]

Child 0: AI ASSITANT PROJECT (6) - Brave
Role: frame

Action 0: doDefault
Action 1: showContextMenu
```

### What this confirms

- Brave is visible through `pyatspi.Registry.getDesktop(0)`.
- Its accessible application object can be retrieved.
- Its browser frame can be discovered.
- The frame exposes accessibility actions.

### What is not confirmed

- Whether the browser tab bar is exposed.
- Whether the New Tab button is exposed.
- Whether the address bar is accessible.
- Whether web document elements are accessible.
- Whether the frame's panel contains further useful controls.

These are still under investigation.

---

## 9. Inspecting Accessibility Actions

An accessible object may expose actions through its Action interface.

Example:

```python
query_action = desktop_child.queryAction()

for i in range(query_action.n):
    print(
        f"Action {i}: "
        f"{query_action.getName(i)}"
    )
```

The Brave application object and frame currently expose:

```text
Action 0: doDefault
Action 1: showContextMenu
```

Calling:

```python
query_action.doAction(1)
```

invokes the context-menu action.

It does not open a new browser tab.

**Important:** Actions must be inspected on the actual accessible control. The application-level Action interface does not represent every action available inside the browser.

---

## 10. Inspecting the Accessibility Tree

The next investigation is to recursively inspect the Brave application's descendants.

Use:

```python
import pyatspi


def inspect_tree(node, depth=0):

    indent = "  " * depth

    try:
        print(
            f"{indent}{node.name!r} "
            f"[{node.getRoleName()}] "
            f"children={node.getChildCount()}"
        )

        try:
            actions = node.queryAction()

            for i in range(actions.n):
                print(
                    f"{indent}  Action {i}: "
                    f"{actions.getName(i)}"
                )

        except Exception:
            pass

        for i in range(node.getChildCount()):
            inspect_tree(
                node.getChildAtIndex(i),
                depth + 1
            )

    except Exception as e:

        print(f"{indent}Error: {e}")


desktop = pyatspi.Registry.getDesktop(0)

for i in range(desktop.getChildCount()):

    app = desktop.getChildAtIndex(i)

    if "brave" in (app.name or "").lower():

        inspect_tree(app)
```

This prints:

- Accessible object names.
- Accessible roles.
- Number of children.
- Available actions.

### Previously observed tree structure

The browser frame previously had one child:

```text
Brave Browser [application]
    AI ASSITANT PROJECT (6) - Brave [frame]
        panel
```

The presence of a panel alone does not establish that the browser controls are exposed.

The panel and its descendants need to be inspected.

---

## 11. Opening a New Browser Tab

The intended operation is to open a new Brave tab programmatically.

Two possible approaches have been discussed.

### Approach A: AT-SPI Action

If the accessibility tree exposes a New Tab button:

1. Locate the button.
2. Query its Action interface.
3. Inspect available actions.
4. Invoke the appropriate action.

Example:

```python
actions = new_tab_button.queryAction()

for i in range(actions.n):
    print(i, actions.getName(i))
```

After identifying the correct action:

```python
actions.doAction(action_index)
```

The action index must be discovered at runtime. It must not be assumed.

### Approach B: Keyboard input

The standard Brave shortcut for opening a new tab is:

```text
Ctrl + T
```

An external keyboard input mechanism such as `ydotool` was discussed as a fallback.

Example:

```bash
ydotool key 29:1 20:1 20:0 29:0
```

This represents Ctrl+T key press and release events.

However:

- This is not an AT-SPI operation.
- It requires a properly configured `ydotool` daemon.
- It has not yet been integrated into Anvaya.

### Current decision

Continue investigating AT-SPI first.

Do not introduce keyboard simulation as the primary solution until the accessibility-tree limitation is understood.

---

## 12. Browser Controller Architecture

The browser automation functionality should eventually be separated into three responsibilities.

| Component | Responsibility |
|---|---|
| Browser Manager | Launching and detecting Brave |
| AT-SPI Controller | Discovering and interacting with accessible controls |
| Input Controller | Keyboard and mouse simulation when necessary |

Possible future operations:

```text
Browser Manager
    ├── launch()
    ├── is_running()
    └── get_application()

AT-SPI Controller
    ├── get_desktop()
    ├── find_application()
    ├── inspect_tree()
    └── invoke_action()

Input Controller
    ├── press_key()
    ├── release_key()
    └── hotkey()
```

These are proposed responsibilities, not implemented features.

---

## 13. Current Progress

| Task | Status |
|---|---|
| Install AT-SPI dependencies | Completed |
| Access AT-SPI through system Python | Completed |
| Launch Brave through `gtk-launch` | Implemented |
| Configure Brave accessibility flags | Configured |
| Detect Brave in desktop tree | Completed |
| Retrieve Brave application object | Completed |
| Retrieve browser frame | Completed |
| Inspect application/frame actions | Completed |
| Identify tab bar | Pending |
| Identify New Tab button | Pending |
| Open a new tab through AT-SPI | Pending |
| Navigate to a URL | Pending |
| Interact with web page elements | Pending |

---

## 14. Immediate Next Steps

The next work should proceed in this order:

1. Inspect the complete recursive accessibility tree of Brave.
2. Determine whether the frame's panel exposes additional descendants.
3. Verify whether the browser toolbar and tab controls are exposed.
4. Investigate Chromium/Brave accessibility-tree behavior if those controls remain missing.
5. Test invoking the New Tab button if it becomes accessible.
6. If necessary, implement keyboard input as a separate fallback.
7. Once tab creation works, investigate address-bar interaction and URL navigation.

### Important debugging principle

Do not confuse these three states:

- Brave is running.
- Brave is registered with AT-SPI.
- Brave exposes the controls needed for automation.

The first two are confirmed. The third is not.

The current blocker is browser-control accessibility, not browser launching or application discovery.

---

## 15. Development Notes

- Keep the implementation modular.
- Avoid unnecessary GNOME accessibility-setting changes.
- Do not enable a screen reader merely to make browser automation work without evidence that it is required.
- Avoid launching multiple Brave instances during polling.
- Use the actual accessibility tree to discover controls rather than assuming names, roles or action indexes.
- Prefer small, testable functions.
- Keep the AT-SPI implementation compatible with Fedora's system Python unless a deliberate integration strategy is chosen for the project's virtual environment.

**Current milestone:** Brave is successfully discoverable through Python AT-SPI. The next milestone is discovering and controlling its browser interface, beginning with the New Tab operation.