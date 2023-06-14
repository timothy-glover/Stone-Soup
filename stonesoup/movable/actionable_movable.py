from stonesoup.movable import FixedMovable
from stonesoup.sensor.action.move_position_action import GridActionGenerator
from stonesoup.types.state import State


class GridActionableMovable(FixedMovable):
    """  """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._next_action = None

    #         self.scheduled_actions = dict()

    def actions(self, timestamp, start_timestamp=None):
        generators = set()
        generators.add(GridActionGenerator(owner=self,
                                           attribute="position",
                                           start_time=start_timestamp,
                                           end_time=timestamp))

        return generators

    def move(self, timestamp, *args, **kwargs):
        current_time = self.states[-1].timestamp
        new_state = State.from_state(self.state, timestamp=timestamp)
        new_state.state_vector = new_state.state_vector.copy()
        self.states.append(new_state)
        action = self._next_action
        if action is not None:
            self.position = action.act(current_time, timestamp, self.position)
        self._next_action = None

    def add_actions(self, actions):
        self._next_action = actions[0]
        #         for name in self._actionable_properties:
        #             for action in actions:
        #                 if action.generator.attribute ==name:
        #                     self.scheduled_actions[name] = action
        return True

    def act(self, timestamp, *args, **kwargs):
        self.move(timestamp, *args, **kwargs)