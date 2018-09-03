from datetime import datetime, timedelta
import time
import threading


class Scheduler:
    def __init__(self, per_minute=5, short_task_interval=5):
        self.short_task_interval = short_task_interval
        self.per_minute = per_minute
        self.kill = 0
        self.target = 0

    # override et
    def short_task(self):
        pass

    # override et
    def long_task(self):
        pass

    def get_target(self):
        return self.target

    def stop(self):
        self.kill = 1

    # thread olarak baslatir
    def start_as_thread(self):
        threading.Thread(target=self.start_as_loop).start()

    # loop olarak baslatir
    def start_as_loop(self):
        n = datetime.now().minute % self.per_minute
        self.target = datetime.now() + timedelta(minutes=self.per_minute - n)
        self.target = datetime(self.target.year, self.target.month, self.target.day, self.target.hour,
                               self.target.minute)
        # print(datetime.now(), target)

        while True:
            target = time.time() + self.short_task_interval
            if datetime.now() > self.target:
                # print("long task")
                self.long_task()
                self.target += timedelta(minutes=self.per_minute)

            # print("short task")
            self.short_task()
            left = target - time.time()
            if left > 0:
                time.sleep(left)
            if self.kill:
                break
