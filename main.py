import pyatspi
import handling_Subprocess
import time

global found_application 
found_application = False


def start_browser():
    handler = handling_Subprocess.SubprocessHandler("gtk-launch", "brave-browser")
    handler.start_process()

def inspect(node, depth=0):
    indent = "  " * depth

    print(
        f"{indent}{node.name!r} "
        f"[{node.getRoleName()}] "
        f"children={node.getChildCount()}"
    )

    for i in range(node.getChildCount()):
        inspect(node.getChildAtIndex(i), depth + 1)


def myFunc():
    registry = pyatspi.Registry

    desktop = registry.getDesktop(0)

    print(desktop.name)
    count = desktop.getChildCount()
    count -= 1
    global found_application
    desktop_child = None
    while count >= 0:
        desktop_child = desktop.getChildAtIndex(count)
        print(f"Child {count}: {desktop_child.name}")
        if "Brave".lower()  in desktop_child.name.lower():
            print(f"Found Brave Browser: {desktop_child}")
            found_application = True
            break
        count -= 1
    inspect(desktop_child)
    if found_application:
        print("Brave Browser is running.")
        print(desktop_child.getRoleName())
        print(f"Attributes: {desktop_child.getAttributes()}")

        for i in range(desktop_child.getChildCount()):
            child = desktop_child.getChildAtIndex(i)
            print(f"Child {i}: {child.name}, Role: {child.getRoleName()}")
            qa = child.queryAction()
            for j in range(qa.nActions):
                print(f"Action {j}: {qa.getName(j)}")




if __name__ == "__main__":
    application_search_count = 0
    while (not found_application) and application_search_count < 5:
        myFunc()
        if not found_application:
            print("Brave Browser not found. Starting the browser...")
            start_browser()
            time.sleep(5)  
        application_search_count += 1