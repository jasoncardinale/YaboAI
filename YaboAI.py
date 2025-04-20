import datetime
import random

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
last_camera_update_time = datetime.datetime.now()
is_commentating = False
driver_count = 32
sector_count = 0
car_in_focus = 0

event_queue: list[Event] = []

current_state = RaceState()


def acMain(ac_version):
    global appWindow, driver_count, current_state, previousState

    appWindow = ac.newApp(APP_NAME)
    ac.setTitle(appWindow, APP_NAME)
    ac.setSize(appWindow, 200, 200)

    ac.addRenderCallback(appWindow, appGL)

    ac.console("===BEGIN RACE===")
    ac.console("DRIVERS:")

    driver_count = ac.getCarsCount()
    for id in range(driver_count):
        driver = Driver(id)
        current_state.add_driver(driver)
        ac.console(f"Driver: {driver.name} - {driver.car_name} - {driver.nation}")

    return APP_NAME


def appGL(deltaT):
    pass


def acUpdate(deltaT):
    global \
        last_update_time, \
        event_queue, \
        driver_count, \
        car_in_focus, \
        is_commentating, \
        current_state

    last_update_time += deltaT
    if last_update_time < 5:
        return

    event_queue.extend(current_state.update())

    if len(event_queue) == 0:
        ac.console("No events. Resetting last_update_time")
        camera_control(current_state)
        last_update_time = 0
        return

    if is_commentating:
        ac.console("Actively commentating")
        event = event_queue[0]
        duration = (datetime.datetime.now() - event.time).total_seconds()
        if duration > 30:
            if event.type in [
                EventType.BEST_LAP,
                EventType.SHORT_INTERVAL,
                EventType.ENTERED_PIT,
            ]:
                ac.console(
                    f"Oldest {event.type} event is {duration} seconds old. Removing from queue"
                )
                event_queue.pop()
    else:
        is_commentating = True
        event = event_queue.pop()
        ac.console(f"Trigger commentary on {event.type} event")
        camera_control(current_state, event)
        prompt = generate_prompt(event)
        script = chat_completion(prompt)
        ac.console(f"SCRIPT = '{script}'")
        audio = text_to_speech(script)
        if audio:
            is_commentating = False

    last_update_time = 0


def camera_control(state: RaceState, event: Event | None = None):
    global last_camera_update_time

    current_time = datetime.datetime.now()
    time_delta = (current_time - last_camera_update_time).total_seconds()
    if time_delta < 10:
        ac.console(f"Camera locked for {10 - int(time_delta)} more seconds")
        return

    last_camera_update_time = current_time

    if not event:
        driver = state.drivers[random.randint(1, len(state.drivers) - 1)]
        ac.focusCar(driver)
        ac.console(f"No camera event. Randomly focusing on driver: {driver.name}")
        ac.setCameraMode("Random")
        return

    if not ac.focusCar(event.driver_id):
        ac.console(f"ERROR: Unable to assign focus to driver_id: {event.driver_id}")
        driver = state.drivers[random.randint(1, len(state.drivers) - 1)]
        ac.focusCar(driver)
        ac.console(f"Randomly focusing on driver: {driver.name}")

    match event.type:
        case (
            EventType.START_SAFETY_CAR,
            EventType.END_SAFETY_CAR,
            EventType.DNF,
            EventType.COLLISION,
        ):
            ac.setCameraMode("Helicopter")
            ac.console("Selecting HELICOPTER camera")
        case EventType.ENTERED_PIT, EventType.OVERTAKE:
            ac.setCameraMode("Car")
            ac.console("Selecting CAR camera")
        case EventType.SHORT_INTERVAL, EventType.DRS_RANGE:
            ac.setCameraMode("Cockpit")
            ac.console("Selecting COCKPIT camera")
        case _:
            ac.setCameraMode("Random")
            ac.console("Selecting RANDOM camera")


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
