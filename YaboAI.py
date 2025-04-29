import datetime
import random

import ac  # type: ignore
import acsys  # type: ignore

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
last_camera_update_time = 0
is_commentating = False
driver_count = 32
sector_count = 0
car_in_focus = 0

event_queue = []

current_state = RaceState()


def acMain(ac_version):
    global appWindow, driver_count, current_state

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
        ac.console(
            "Driver: {} - {} - {}".format(driver.name, driver.car_name, driver.nation)
        )

    return APP_NAME


def appGL(deltaT):
    pass


def acUpdate(deltaT):
    global \
        last_update_time, \
        last_camera_update_time, \
        event_queue, \
        driver_count, \
        car_in_focus, \
        is_commentating, \
        current_state

    last_update_time += deltaT
    last_camera_update_time += deltaT
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
                    "{} event is {} seconds old. Removing from queue".format(
                        event.type, duration
                    )
                )
                event_queue.pop()
    else:
        is_commentating = True
        event = event_queue.pop()
        ac.console("Trigger commentary on {} event".format(event.type))
        camera_control(current_state, event)
        prompt = generate_prompt(event)
        ac.console("PROMPT = '{}'".format(prompt))
        script = chat_completion(prompt)
        ac.console("SCRIPT = '{}'".format(script))
        audio = text_to_speech(script)
        if audio:
            is_commentating = False

    last_update_time = 0


def camera_control(state: RaceState, event=None):
    global last_camera_update_time

    if last_camera_update_time < 15:
        ac.console("Camera locked for {} more seconds".format(15 - int(last_camera_update_time)))
        return

    if not event or event.type == EventType.DNF:
        driver = state.drivers[random.randint(1, len(state.drivers) - 1)]
        ac.focusCar(driver.id)
        ac.console(
            "No camera event or driver DNF'd. Randomly focusing on driver: {}".format(
                driver.name
            )
        )
        ac.setCameraMode(acsys.CM.Random)
        return

    ac.console("Focus on driver_id: {}".format(event.driver_id))
    if not ac.focusCar(event.driver_id):
        ac.console("ERROR: Unable to focus on driver_id: {}".format(event.driver_id))
        driver = state.drivers[random.randint(1, len(state.drivers) - 1)]
        ac.focusCar(driver)
        ac.console("Randomly focusing on driver: {}".format(driver.name))

    if event.type in (
        EventType.START_SAFETY_CAR,
        EventType.END_SAFETY_CAR,
        EventType.DNF,
        EventType.COLLISION,
    ):
        ac.setCameraMode(acsys.CM.Helicopter)
        ac.console("Selecting HELICOPTER camera")
    elif event.type in (EventType.ENTERED_PIT, EventType.OVERTAKE):
        ac.setCameraMode(acsys.CM.Car)
        ac.console("Selecting CAR camera")
    elif event.type in (EventType.SHORT_INTERVAL, EventType.DRS_RANGE):
        ac.setCameraMode(acsys.CM.Cockpit)
        ac.console("Selecting COCKPIT camera")
    else:
        ac.setCameraMode(acsys.CM.Random)
        ac.console("Selecting RANDOM camera")

    last_camera_update_time = 0


def generate_prompt(event: Event):
    ac.console("{} -- event type: {}".format(datetime.datetime.now(), event.type))
    prompt = ""
    if event.type == EventType.START_SAFETY_CAR:
        prompt = "The safety car has come out on lap {}.".format(
            event.params["lap_count"]
        )
    elif event.type == EventType.END_SAFETY_CAR:
        prompt = "The safety car has now ended on lap {}.".format(
            event.params["lap_count"]
        )
    elif event.type == EventType.DNF:
        prompt = (
            "The driver named {} is now out of the race due to this reason: {}.".format(
                event.params["driver"], event.params["reason"]
            )
        )
    elif event.type == EventType.COLLISION:
        pass
    elif event.type == EventType.BEST_LAP:
        prompt = "The driver named {} has just set a personal best with a lap time of {}.".format(
            event.params["driver"], event.params["lap_time"]
        )
    elif event.type == EventType.FASTEST_LAP:
        prompt = "The driver named {} has just set the fastest lap with a time of {}.".format(
            event.params["driver"], event.params["lap_time"]
        )
    elif event.type == EventType.ENTERED_PIT:
        prompt = "The driver named {} has entered the pit on lap {}. They completed their last lap with a time of {} on the {} compound tire.".format(
            event.params["driver"],
            event.params["lap_count"],
            event.params["last_lap"],
            event.params["compound"],
        )
    elif event.type == EventType.QUICK_PIT:
        prompt = "The driver named {} just finished a quick pit stop that lasted {} seconds. They are now running the {} compound tire.".format(
            event.params["driver"],
            event.params["duration"],
            event.params["compound"],
        )
    elif event.type == EventType.LONG_PIT:
        prompt = "The driver named {} just finished a long pit stop that lasted {} seconds. They are now running the {} compound tire.".format(
            event.params["driver"],
            event.params["duration"],
            event.params["compound"],
        )
    elif event.type == EventType.SHORT_INTERVAL:
        prompt = (
            "The driver named {} is within {} seconds of the driver named {}.".format(
                event.params["driver_b"],
                event.params["interval"],
                event.params["driver_a"],
            )
        )
    elif event.type == EventType.DRS_RANGE:
        prompt = "The driver named {} is within {} seconds of the driver named {}. They can now use DRS to help with overtaking.".format(
            event.params["driver_b"],
            event.params["interval"],
            event.params["driver_a"],
        )
    elif event.type == EventType.OVERTAKE:
        prompt = "The driver named {} has overtaken the driver named {}. The driver named {} is now in position {}.".format(
            event.params["driver_a"],
            event.params["driver_b"],
            event.params["driver_a"],
            event.params["position"],
        )
    elif event.type == EventType.LONG_STINT:
        prompt = "The driver named {} has now completed {} laps with the {} compound tires. They completed the last lap with a time of {}. We are now on lap {}".format(
            event.params["driver"],
            event.params["tire_age"],
            event.params["compound"],
            event.params["last_lap"],
            event.params["lap_count"],
        )

    return prompt


def text_to_speech(text):
    # time.sleep(10)
    return True
