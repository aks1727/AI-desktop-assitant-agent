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

        print(f"Started {self.app_name} launcher with PID: {self.process.pid}")


if __name__ == "__main__":
    handler = SubprocessHandler("gtk-launch", "brave-browser")
    handler.start_process()