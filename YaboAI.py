import copy
import datetime

import ac  # type: ignore

from llm.services import chat_completion
from models import Driver, Event, EventType, RaceState
from third_party.sim_info import SimInfo

# Global constants
APP_NAME = "YaboAI"
FOCUS_DURATION_MIN_MS = 300
FOCUS_DURATION_MAX_MS = 1500

simInfo = SimInfo()

# Global variables
last_update_time = 0
is_commentating = False
driver_count = 32
sector_count = 0
car_in_focus = 0

event_queue: list[Event] = []

currentState = RaceState()
previousState = RaceState()


def acMain(ac_version):
    global appWindow, driver_count, currentState, previousState

    appWindow = ac.newApp(APP_NAME)
    ac.setTitle(appWindow, APP_NAME)
    ac.setSize(appWindow, 200, 200)

    ac.addRenderCallback(appWindow, appGL)

    driver_count = ac.getCarsCount()
    for id in range(driver_count):
        driver = Driver(id)
        previousState.add_driver(driver)
        currentState.add_driver(driver)

    return APP_NAME


def appGL(deltaT):
    pass


def eventPriority():
    pass


def step():
    global last_update_time, currentState, previousState
    last_update_time = 0
    previousState = copy.deepcopy(currentState)


def acUpdate(deltaT):
    global \
        last_update_time, \
        event_queue, \
        driver_count, \
        car_in_focus, \
        is_commentating, \
        previousState, \
        currentState

    last_update_time += deltaT
    if last_update_time < 5:
        return

    event_queue.extend(currentState.update())

    if len(event_queue) == 0:
        step()
        return

    if is_commentating:
        event = event_queue[0]
        duration = datetime.datetime.now() - event.time
        if duration.total_seconds() > 30:
            if event.type in [
                EventType.BEST_LAP,
                EventType.SHORT_INTERVAL,
                EventType.ENTERED_PIT,
            ]:
                event_queue.pop()
    else:
        is_commentating = True
        event = event_queue.pop()
        camera_control(event)
        prompt = generate_prompt(event)
        script = chat_completion(prompt)
        audio = text_to_speech(script)
        if audio:
            is_commentating = False

    step()


def camera_control(event: Event):
    ac.focusCar(event.driver_id)

    match event.type:
        case EventType.START_SAFETY_CAR:
            pass
        case EventType.END_SAFETY_CAR:
            pass
        case EventType.DNF:
            pass
        case EventType.COLLISION:
            pass
        case EventType.BEST_LAP:
            pass
        case EventType.FASTEST_LAP:
            pass
        case EventType.ENTERED_PIT:
            pass
        case EventType.QUICK_PIT:
            pass
        case EventType.LONG_PIT:
            pass
        case EventType.SHORT_INTERVAL, EventType.DRS_RANGE:
            pass
        case EventType.OVERTAKE:
            pass
        case EventType.LONG_STINT:
            pass


def generate_prompt(event: Event):
    ac.console("{} -- event type: {}".format(datetime.datetime.now(), event.type))
    prompt = ""
    match event.type:
        case EventType.START_SAFETY_CAR:
            prompt = "The safety car has come out on lap {}.".format(
                event.params["lap_count"]
            )
        case EventType.END_SAFETY_CAR:
            prompt = "The safety car has now ended on lap {}.".format(
                event.params["lap_count"]
            )
        case EventType.DNF:
            pass
        case EventType.COLLISION:
            pass
        case EventType.BEST_LAP:
            prompt = "The driver named {} has just set a personal best with a lap time of {}.".format(
                event.params["driver"], event.params["lap_time"]
            )
        case EventType.FASTEST_LAP:
            prompt = "The driver named {} has just set the fastest lap with a time of {}.".format(
                event.params["driver"], event.params["lap_time"]
            )
        case EventType.ENTERED_PIT:
            prompt = "The driver named {} has entered the pit on lap {}. They completed their last lap with a time of {} on the {} compound tire.".format(
                event.params["driver"],
                event.params["lap_count"],
                event.params["last_lap"],
                event.params["compound"],
            )
        case EventType.QUICK_PIT:
            prompt = "The driver named {} just finished a quick pit stop that lasted {} seconds. They are now running the {} compound tire.".format(
                event.params["driver"],
                event.params["duration"],
                event.params["compound"],
            )
        case EventType.LONG_PIT:
            prompt = "The driver named {} just finished a long pit stop that lasted {} seconds. They are now running the {} compound tire.".format(
                event.params["driver"],
                event.params["duration"],
                event.params["compound"],
            )
        case EventType.SHORT_INTERVAL:
            prompt = "The driver named {} is within {} seconds of the driver named {}.".format(
                event.params["driver_b"],
                event.params["interval"],
                event.params["driver_a"],
            )
        case EventType.DRS_RANGE:
            prompt = "The driver named {} is within {} seconds of the driver named {}. They can now use DRS to help with overtaking.".format(
                event.params["driver_b"],
                event.params["interval"],
                event.params["driver_a"],
            )
        case EventType.OVERTAKE:
            prompt = "The driver named {} has overtaken the driver named {}. The driver named {} is now in position {}.".format(
                event.params["driver_a"],
                event.params["driver_b"],
                event.params["driver_a"],
                event.params["position"],
            )
        case EventType.LONG_STINT:
            prompt = "The driver named {} has now completed {} laps with the {} compound tires. They completed the last lap with a time of {}. We are now on lap {}".format(
                event.params["driver"],
                event.params["tire_age"],
                event.params["compound"],
                event.params["last_lap"],
                event.params["lap_count"],
            )

    ac.console(prompt)
    return prompt


def text_to_speech(text):
    # time.sleep(10)
    return True
