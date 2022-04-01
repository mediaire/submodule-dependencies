from mediaire_toolbox.queue.tasks import Task
from pprint import pprint

task = Task(t_id=1, tag='demo')

pprint(task.to_dict())
