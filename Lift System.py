import asyncio
import time
import random

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(
    15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN
)  # Set pin 10 to be an input pin and set initial value to be pulled low (off)


# Set the pin numbers
led_pins = [26, 19, 13, 6, 5, 22, 27, 17]

# 1-5 floors
# 6 door open
# 7 motor start
# 8 emergency brake


# Set the pins as output
for pin in led_pins:
    GPIO.setup(pin, GPIO.OUT)


class Lift:
    def __init__(
        self,
        current_floor=0,
        door_open=True,
        direction=None,
        motor=False,
        brakes=False,
    ):
        self.current_floor = current_floor
        self.door_open = door_open
        self.direction = direction
        self.motor = motor
        self.brakes = brakes
        GPIO.output(led_pins[current_floor], GPIO.HIGH)
        if door_open:
            GPIO.output(led_pins[5], GPIO.HIGH)
        # print(f"LED {led_pins[current_floor]} ON")

    def open_door(self, x):
        if GPIO.input(15) == GPIO.HIGH:
            print("Emergency button pressed")
            x[6] = 0
        self.door_open = True
        x[3] = 0
        time.sleep(1)
        GPIO.output(led_pins[5], GPIO.HIGH)
        # print(f"LED {led_pins[5]} ON")

    def close_door(self, x, target_floor):
        speed = random.randint(0, 100)
        # if speed > 60:
        if GPIO.input(15) == GPIO.HIGH:
            print("Emergency button pressed")
            x[6] = 0
        self.door_open = False
        x[3] = 1
        if target_floor == self.current_floor:
            x[4] = 1
        if target_floor > self.current_floor:
            x[5] = 1

        time.sleep(1)
        GPIO.output(led_pins[5], GPIO.LOW)
        # print(f"LED {led_pins[5]} OFF")

    def down_direction(self, x):
        if GPIO.input(15) == GPIO.HIGH:
            print("Emergency button pressed")
            x[6] = 0
        self.direction = "Down"

    def up_direction(self, x):
        if GPIO.input(15) == GPIO.HIGH:
            print("Emergency button pressed")
            x[6] = 0
        self.direction = "Up"

    async def motor_start(self, target_floor, x):
        self.motor = True
        GPIO.output(led_pins[6], GPIO.HIGH)
        # print(f"LED {led_pins[6]} ON")
        await self.move_lift(target_floor, x)

    def motor_stop(self, x):
        if GPIO.input(15) == GPIO.HIGH:
            print("Emergency button pressed")
            x[6] = 0
        GPIO.output(led_pins[6], GPIO.LOW)
        # print(f"LED {led_pins[6]} OFF")
        self.motor = False

    def apply_brakes(self, x):
        GPIO.output(led_pins[7], GPIO.HIGH)
        # print(f"LED {led_pins[7]} ON")
        self.brakes = True

    async def move_lift(self, target_floor, x):
        # print(f"Lift moving from floor {self.current_floor} to floor {target_floor}")

        floor = self.current_floor
        for _ in range(abs(target_floor - self.current_floor)):
            time.sleep(2)
            GPIO.output(led_pins[self.current_floor], GPIO.LOW)
            # print(f"LED {led_pins[self.current_floor]} OFF")
            # print(self.direction)

            if self.direction == "Up":
                self.current_floor += 1
                speed = random.randint(0, 100)
                # print(f"Currently on {self.current_floor} floor")
                GPIO.output(led_pins[self.current_floor], GPIO.HIGH)
                # print(f"LED {led_pins[self.current_floor]} ON")
                # if speed > 80:
                if GPIO.input(15) == GPIO.HIGH:
                    # print(f"speed", speed)
                    x[6] = 0
                    return
                time.sleep(2)
            elif self.direction == "Down":
                time.sleep(2)
                self.current_floor -= 1
                speed = random.randint(0, 100)
                # print(f"Currently on {self.current_floor} floor")
                GPIO.output(led_pins[self.current_floor], GPIO.HIGH)
                # print(f"LED {led_pins[self.current_floor]} ON")
                # if speed > 80:
                if GPIO.input(15) == GPIO.HIGH:
                    # print(f"speed", speed)
                    x[6] = 0
                    return
                    # raise Exception("Free Fall")

        # Simulate lift movement time
        self.current_floor = target_floor
        x[4] = 1
        # print(f"Lift arrived at floor {self.current_floor}")


class BDDNode:
    def __init__(self, index, node_type, node_index, successor0=None, successor1=None):
        self.index = index
        self.node_type = node_type
        self.node_index = node_index
        self.successor0 = successor0
        self.successor1 = successor1


class ControlMemoryEntry:
    def __init__(self, index, control=None, imm_transition=False):
        self.index = index
        self.control = control
        self.imm_transition = imm_transition

    async def execute_control(self, lift, x, target_floor):
        # Assuming control is a function that opens the door of the lift
        if self.control == "Y7":
            print("Opening the door - Y7")
            lift.open_door(x)
        elif self.control == "Y1":
            print("Closing the door - Y1")
            lift.close_door(x, target_floor)
        elif self.control == "Y2":
            print("Moving Downwards - Y2")
            lift.down_direction(x)
        elif self.control == "Y3":
            print("Moving Upwards - Y3")
            lift.up_direction(x)
        elif self.control == "Y4":
            print("Motor starts - Y4")
            await lift.motor_start(target_floor, x)
        elif self.control == "Y5":
            print("Motor Stops - Y5")
            lift.motor_stop(x)
        elif self.control == "Y6":
            print("Emergency brakes applied - Y6")
            lift.apply_brakes(x)
            lift.motor_stop(x)
            lift.open_door(x)
        else:
            print("Unknown control action")


async def slc_driver(Number, BDD_Table, control_memory, x, lift, target_floor):
    state = 0
    i = Number

    while True:
        state = 0
        index = BDD_Table[i].node_index
        # print(index)
        # print(x[index])
        if BDD_Table[i].node_type == "x":
            if x[index] == 0:
                i = BDD_Table[i].successor0
            else:
                i = BDD_Table[i].successor1

        elif BDD_Table[i].node_type == "a":
            state = 1
            if control_memory[index].control is not None:
                await control_memory[index].execute_control(lift, x, target_floor)
                time.sleep(1)
                print("Executing control action:", control_memory[index].control)
            i = BDD_Table[i].successor1

        if state and not control_memory[index].imm_transition:
            # print("SLC driver finished execution.")
            return i


async def main():

    lift = Lift()

    # Example BDD table initialization
    BDD_Table = [
        BDDNode(0, "x", 6, successor0=3, successor1=1),
        BDDNode(1, "x", 1, successor0=4, successor1=2),
        BDDNode(2, "x", 2, successor0=5, successor1=6),
        BDDNode(3, "a", 6, successor1=-1),
        BDDNode(4, "a", 0, successor1=0),
        BDDNode(5, "a", 0, successor1=0),
        BDDNode(6, "a", 1, successor1=7),
        BDDNode(7, "x", 6, successor0=11, successor1=8),
        BDDNode(8, "x", 3, successor0=12, successor1=9),
        BDDNode(9, "x", 4, successor0=10, successor1=15),
        BDDNode(10, "x", 5, successor0=13, successor1=14),
        BDDNode(11, "a", 6, successor1=-1),
        BDDNode(12, "a", 1, successor1=7),
        BDDNode(13, "a", 2, successor1=16),
        BDDNode(14, "a", 3, successor1=19),
        BDDNode(15, "a", 7, successor1=30),
        BDDNode(16, "x", 6, successor0=17, successor1=18),
        BDDNode(17, "a", 6, successor1=-1),
        BDDNode(18, "a", 4, successor1=22),
        BDDNode(19, "x", 6, successor0=20, successor1=21),
        BDDNode(20, "a", 6, successor1=-1),
        BDDNode(21, "a", 4, successor1=22),
        BDDNode(22, "x", 6, successor0=24, successor1=23),
        BDDNode(23, "x", 4, successor0=25, successor1=26),
        BDDNode(24, "a", 6, successor1=-1),
        BDDNode(25, "a", 4, successor1=22),
        BDDNode(26, "a", 5, successor1=27),
        BDDNode(27, "x", 6, successor0=28, successor1=29),
        BDDNode(28, "a", 6, successor1=-1),
        BDDNode(29, "a", 7, successor1=30),
        BDDNode(30, "x", 6, successor0=31, successor1=32),
        BDDNode(31, "a", 6, successor1=-1),
        BDDNode(32, "a", 0, successor1=0),
    ]

    # Example control memory initialization
    control_memory = [
        ControlMemoryEntry(0),
        ControlMemoryEntry(1, control="Y1"),
        ControlMemoryEntry(2, control="Y2"),
        ControlMemoryEntry(3, control="Y3"),
        ControlMemoryEntry(4, control="Y4"),
        ControlMemoryEntry(5, control="Y5"),
        ControlMemoryEntry(6, control="Y6"),
        ControlMemoryEntry(7, control="Y7"),
    ]

    while True:
        try:
            x = [0] * 7
            x[6] = 1

            target_floor = int(
                input("Enter the floor you want to go to (-1 to exit): ")
            )
            if target_floor == -1:
                print("Exiting...")
                for pin in led_pins:
                    GPIO.output(pin, GPIO.LOW)
                GPIO.cleanup()
                break
            if target_floor > 4 or target_floor < -1:
                raise ValueError
            x[1] = 1

            print("Enter the body weight")
            bodyWeight = int(input())
            if bodyWeight > 0:
                x[2] = 1
            i = 0
            j = 1
            temp = False
            while j != 0:
                j = await slc_driver(
                    i, BDD_Table, control_memory, x, lift, target_floor
                )
                i = j
                # print(i)
                if i == -1:
                    print("Reboot system")
                    temp = True
                    break
                time.sleep(2)
            if temp == True:
                try:
                    num = int(input("Enter -1 for exiting: "))
                    if num == -1:
                        print("Exiting...")
                        for pin in led_pins:
                            GPIO.output(pin, GPIO.LOW)
                        GPIO.cleanup()
                        break
                    else:
                        raise ValueError
                except ValueError:
                    print("Rebooting the system anyways")
                    for pin in led_pins:
                        GPIO.output(pin, GPIO.LOW)
                    GPIO.cleanup()
                break
        except ValueError:
            print("Please enter a valid floor number.")
        # finally:
        #    GPIO.cleanup()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
