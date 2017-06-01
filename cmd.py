import subprocess

class Cmd:
    def run(self, cmd_string):
        try:
            result = subprocess.run(cmd_string.split(' '), stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=True)
            return result.stdout.decode("utf-8")
        except subprocess.CalledProcessError as e:
            raise e

